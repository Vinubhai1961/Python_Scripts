#!/usr/bin/env python3
import os
import argparse
import logging
from datetime import datetime

import numpy as np
import pandas as pd
import arcticdb as adb


# =========================
# VCP / BO DEFAULT SETTINGS
# Keep these requirements unchanged unless you intentionally want to loosen/tighten scanner.
# =========================
DEFAULTS = {
    "pivot_left": 3,
    "pivot_right": 3,

    # A real VCP should normally have 3+ contractions.
    # 2 contractions was too loose and created many false positives.
    "min_contractions": 3,
    "max_contractions": 6,

    "first_min_pct": 10.0,
    "first_max_pct": 35.0,
    "final_min_pct": 3.0,
    "final_max_pct": 10.0,
    "tightening_ratio": 0.90,

    # Keep bases current. Old 200-300 bar patterns caused false VCPs.
    "min_base_bars": 20,
    "max_base_bars": 90,

    # Breakout rules.
    "min_breakout_vol_x": 1.40,
    "vdu_max_x": 1.00,
    "max_extended_pct": 8.0,

    # Current-base quality filters.
    # Candidate must be near pivot, not already far above/below it.
    "max_above_pivot_pct_without_bo": 3.0,
    "max_below_pivot_pct": 12.0,

    # Final tightness filters to avoid names like RAL/ALAB where the stock is
    # trending/pulling back widely rather than forming a tight final contraction.
    "last10_range_max_pct": 8.0,
    "last20_range_max_pct": 15.0,

    # Need repeated resistance near pivot, like the drawing.
    "pivot_touch_pct": 5.0,
    "min_pivot_touches": 2,
}


def safe_float(x):
    try:
        if pd.isna(x):
            return np.nan
        return float(x)
    except Exception:
        return np.nan


def load_arctic_db(path):
    arctic = adb.Arctic(f"lmdb://{path}")
    if not arctic.has_library("prices"):
        raise RuntimeError(f"No 'prices' library found at {path}")
    lib = arctic.get_library("prices")
    return lib, lib.list_symbols()


def normalize_price_df(data):
    required = {"datetime", "open", "high", "low", "close", "volume"}
    if not required.issubset(set(data.columns)):
        return pd.DataFrame()

    df = pd.DataFrame({
        "Open": data["open"].values,
        "High": data["high"].values,
        "Low": data["low"].values,
        "Close": data["close"].values,
        "Volume": data["volume"].values,
    }, index=pd.to_datetime(data["datetime"], unit="s", errors="coerce"))

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
    df = df[(df["High"] > 0) & (df["Low"] > 0) & (df["Close"] > 0) & (df["Volume"] > 0)]
    df = df.sort_index()
    return df


def find_pivots(df, left, right):
    highs = df["High"].values
    lows = df["Low"].values

    pivot_highs = []
    pivot_lows = []

    for i in range(left, len(df) - right):
        window_high = highs[i - left:i + right + 1]
        window_low = lows[i - left:i + right + 1]

        if highs[i] == np.nanmax(window_high):
            pivot_highs.append(i)

        if lows[i] == np.nanmin(window_low):
            pivot_lows.append(i)

    return pivot_highs, pivot_lows


def build_contractions(df, pivot_highs, pivot_lows):
    """
    Build peak-to-trough pullbacks from pivot highs to the next pivot low.
    This creates the raw contraction list. validate_vcp() later scans multiple
    contraction windows to find a valid VCP sequence.
    """
    contractions = []

    for ph in pivot_highs:
        future_lows = [pl for pl in pivot_lows if pl > ph]
        if not future_lows:
            continue

        pl = future_lows[0]

        peak = safe_float(df.iloc[ph]["High"])
        trough = safe_float(df.iloc[pl]["Low"])

        if peak <= 0 or trough <= 0 or trough >= peak:
            continue

        depth = (peak - trough) / peak * 100.0

        contractions.append({
            "peak_idx": ph,
            "trough_idx": pl,
            "peak_date": df.index[ph],
            "trough_date": df.index[pl],
            "peak": peak,
            "trough": trough,
            "depth_pct": depth,
        })

    return contractions


def validate_vcp(df, contractions, cfg, fail_stats=None):
    """
    Improved VCP validation:
      - Does NOT check only one fixed contraction sequence.
      - Scans multiple contraction windows.
      - Accepts the best valid tightening window.
      - Requires nested contractions: each later contraction range must stay
        inside the prior contraction range.
      - Uses full-base pivot = max peak of the accepted window, matching
        a classic VCP resistance/pivot line.
    """
    if len(contractions) < cfg["min_contractions"]:
        if fail_stats is not None:
            fail_stats["not_enough_contractions"] += 1
        return False, {}

    failure_counts = {
        "base_length_fail": 0,
        "first_depth_fail": 0,
        "final_depth_fail": 0,
        "tightening_fail": 0,
        "nested_range_fail": 0,
    }

    max_n = min(cfg["max_contractions"], len(contractions))
    min_n = cfg["min_contractions"]

    # Prefer larger/cleaner windows first, then smaller ones.
    for n in range(max_n, min_n - 1, -1):
        for start in range(0, len(contractions) - n + 1):
            window = contractions[start:start + n]

            base_start = window[0]["peak_idx"]
            base_end = len(df) - 1
            base_len = base_end - base_start + 1

            if base_len < cfg["min_base_bars"] or base_len > cfg["max_base_bars"]:
                failure_counts["base_length_fail"] += 1
                continue

            depths = [c["depth_pct"] for c in window]

            # Nested VCP rule:
            # Each later contraction must stay inside the prior contraction range.
            # This is what removes random pullbacks and keeps clean VCP structures:
            #   current peak <= previous peak
            #   current trough >= previous trough
            nested_ok = True
            for i in range(1, len(window)):
                prev_high = safe_float(window[i - 1]["peak"])
                prev_low = safe_float(window[i - 1]["trough"])
                curr_high = safe_float(window[i]["peak"])
                curr_low = safe_float(window[i]["trough"])

                if not (curr_high <= prev_high and curr_low >= prev_low):
                    nested_ok = False
                    break

            if not nested_ok:
                failure_counts["nested_range_fail"] += 1
                continue

            first = depths[0]
            final = depths[-1]

            if not (cfg["first_min_pct"] <= first <= cfg["first_max_pct"]):
                failure_counts["first_depth_fail"] += 1
                continue

            if not (cfg["final_min_pct"] <= final <= cfg["final_max_pct"]):
                failure_counts["final_depth_fail"] += 1
                continue

            tightening_ok = True
            for i in range(1, len(depths)):
                if depths[i] > depths[i - 1] * cfg["tightening_ratio"]:
                    tightening_ok = False
                    break

            if not tightening_ok:
                failure_counts["tightening_fail"] += 1
                continue

            # Important: full-base pivot/resistance, not just last two peaks.
            pivot = max(c["peak"] for c in window)

            if fail_stats is not None:
                fail_stats["valid_vcp"] += 1

            return True, {
                "pivot": pivot,
                "base_len": base_len,
                "contraction_count": len(window),
                "depths": depths,
                "first_contraction_pct": first,
                "final_contraction_pct": final,
                "base_start": df.index[base_start],
                "base_end": df.index[base_end],
                "base_start_idx": base_start,
                "pivot_date": df.index[window[[c["peak"] for c in window].index(pivot)]["peak_idx"]],
            }

    # Count the most frequent failure reason for this ticker once.
    if fail_stats is not None:
        if failure_counts:
            reason = max(failure_counts, key=failure_counts.get)
            if failure_counts[reason] > 0:
                fail_stats[reason] += 1

    return False, {}


def detect_breakout(df, vcp_info, cfg):
    close = safe_float(df["Close"].iloc[-1])
    volume = safe_float(df["Volume"].iloc[-1])
    pivot = safe_float(vcp_info["pivot"])

    if len(df) < 50 or close <= 0 or pivot <= 0:
        return False, {}

    avg_vol50 = safe_float(df["Volume"].tail(50).mean())
    if avg_vol50 <= 0:
        return False, {}

    vol_x = volume / avg_vol50
    extended_pct = (close - pivot) / pivot * 100.0

    last5_avg_vol = safe_float(df["Volume"].tail(5).mean())
    vdu_x = last5_avg_vol / avg_vol50 if avg_vol50 > 0 else np.nan

    is_bo = (
        close > pivot
        and vol_x >= cfg["min_breakout_vol_x"]
        and extended_pct <= cfg["max_extended_pct"]
        and vdu_x <= cfg["vdu_max_x"]
    )

    return is_bo, {
        "price": close,
        "volume": volume,
        "avg_vol50": avg_vol50,
        "vol_x_50d": vol_x,
        "extended_pct": extended_pct,
        "vdu_x": vdu_x,
    }



def range_pct(df, bars):
    """High-low range over the last N bars as percent of the low."""
    if len(df) < bars:
        return np.nan
    recent = df.tail(bars)
    hi = safe_float(recent["High"].max())
    lo = safe_float(recent["Low"].min())
    if lo <= 0:
        return np.nan
    return (hi - lo) / lo * 100.0


def count_pivot_touches(df, base_start_idx, pivot, pct=5.0):
    """Count local high touches within pct% below the pivot inside the base."""
    if pivot <= 0:
        return 0
    base = df.iloc[base_start_idx:].copy()
    if len(base) < 5:
        return 0

    highs = base["High"].values
    touches = 0
    for i in range(1, len(base) - 1):
        is_local_high = highs[i] >= highs[i - 1] and highs[i] >= highs[i + 1]
        near_pivot = ((pivot - highs[i]) / pivot * 100.0) <= pct and highs[i] <= pivot * 1.005
        if is_local_high and near_pivot:
            touches += 1
    return touches


def validate_current_base_quality(df, vcp_info, is_bo, bo_info, cfg, fail_stats=None):
    """
    Reject structurally valid but low-quality VCPs:
      - old pivots far below current price
      - names already extended above pivot without valid breakout volume
      - wide final ranges instead of tight final contractions
      - bases without repeated resistance/pivot touches
    """
    close = safe_float(df["Close"].iloc[-1])
    pivot = safe_float(vcp_info.get("pivot"))
    base_start_idx = int(vcp_info.get("base_start_idx", 0))

    if close <= 0 or pivot <= 0:
        if fail_stats is not None:
            fail_stats["current_base_quality_fail"] += 1
        return False

    dist_pct = (close - pivot) / pivot * 100.0

    # If above pivot, it must be a valid BO. Otherwise reject it as already moved / failed BO.
    if dist_pct > cfg["max_above_pivot_pct_without_bo"] and not is_bo:
        if fail_stats is not None:
            fail_stats["above_pivot_without_bo_fail"] += 1
        return False

    # If too far below pivot, it is not actionable as a current VCP setup.
    if dist_pct < -cfg["max_below_pivot_pct"]:
        if fail_stats is not None:
            fail_stats["below_pivot_too_far_fail"] += 1
        return False

    r10 = range_pct(df, 10)
    r20 = range_pct(df, 20)

    if pd.notna(r10) and r10 > cfg["last10_range_max_pct"]:
        if fail_stats is not None:
            fail_stats["last10_range_fail"] += 1
        return False

    if pd.notna(r20) and r20 > cfg["last20_range_max_pct"]:
        if fail_stats is not None:
            fail_stats["last20_range_fail"] += 1
        return False

    touches = count_pivot_touches(df, base_start_idx, pivot, cfg["pivot_touch_pct"])
    if touches < cfg["min_pivot_touches"]:
        if fail_stats is not None:
            fail_stats["pivot_touch_fail"] += 1
        return False

    vcp_info["distance_from_pivot_pct"] = dist_pct
    vcp_info["last10_range_pct"] = r10
    vcp_info["last20_range_pct"] = r20
    vcp_info["pivot_touches"] = touches
    return True

def scan_one_ticker(ticker, data, cfg, fail_stats=None):
    if fail_stats is not None:
        fail_stats["total_scanned"] += 1

    df = normalize_price_df(data)

    if df.empty or len(df) < 80:
        if fail_stats is not None:
            fail_stats["not_enough_data"] += 1
        return None

    pivot_highs, pivot_lows = find_pivots(
        df,
        cfg["pivot_left"],
        cfg["pivot_right"],
    )

    if len(pivot_highs) < 2 or len(pivot_lows) < 2:
        if fail_stats is not None:
            fail_stats["not_enough_pivots"] += 1
        return None

    contractions = build_contractions(df, pivot_highs, pivot_lows)
    is_vcp, vcp_info = validate_vcp(df, contractions, cfg, fail_stats)

    if not is_vcp:
        return None

    is_bo, bo_info = detect_breakout(df, vcp_info, cfg)

    if not validate_current_base_quality(df, vcp_info, is_bo, bo_info, cfg, fail_stats):
        return None

    if fail_stats is not None:
        if is_bo:
            fail_stats["breakout_yes"] += 1
        else:
            fail_stats["breakout_no"] += 1

    return {
        "Ticker": ticker,
        "Date": df.index[-1].date(),
        "Price": round(bo_info.get("price", df["Close"].iloc[-1]), 2),
        "Volume": int(bo_info.get("volume", df["Volume"].iloc[-1])),
        "AvgVol50": round(bo_info.get("avg_vol50", np.nan), 0),
        "Vol_x_50d": round(bo_info.get("vol_x_50d", np.nan), 2),
        "Pivot": round(vcp_info["pivot"], 2),
        "Pivot_Date": vcp_info.get("pivot_date", pd.NaT).date() if pd.notna(vcp_info.get("pivot_date", pd.NaT)) else "",
        "Extended_%": round(bo_info.get("extended_pct", np.nan), 2),
        "VCP": "YES",
        "BO": "YES" if is_bo else "NO",
        "Contractions": vcp_info["contraction_count"],
        "Contraction_Depths": " / ".join(f"{x:.1f}%" for x in vcp_info["depths"]),
        "First_Contraction_%": round(vcp_info["first_contraction_pct"], 2),
        "Final_Contraction_%": round(vcp_info["final_contraction_pct"], 2),
        "Base_Length": vcp_info["base_len"],
        "Base_Start": vcp_info["base_start"].date(),
        "Base_End": vcp_info["base_end"].date(),
        "VDU_x": round(bo_info.get("vdu_x", np.nan), 2),
        "Distance_From_Pivot_%": round(vcp_info.get("distance_from_pivot_pct", np.nan), 2),
        "Last10_Range_%": round(vcp_info.get("last10_range_pct", np.nan), 2),
        "Last20_Range_%": round(vcp_info.get("last20_range_pct", np.nan), 2),
        "Pivot_Touches": vcp_info.get("pivot_touches", np.nan),
    }


def main():
    parser = argparse.ArgumentParser(description="Find VCP and breakout stocks from ArcticDB daily data")

    # Local PyCharm defaults based on your paths.
    parser.add_argument("--arctic-db-path", default=r"C:\Users\dipen\Downloads\arctic-db-merged")
    parser.add_argument("--input-csv", default=r"C:\Users\dipen\Downloads\rs_stocks.csv")
    parser.add_argument("--output-dir", default=r"C:\Users\dipen\Downloads")
    parser.add_argument("--log-file", default=r"C:\Users\dipen\Downloads\failed_vcp_tickers_local.log")

    parser.add_argument("--date", default=datetime.now().strftime("%m%d%Y"))
    parser.add_argument("--rs-threshold", type=float, default=80.0)
    parser.add_argument("--min-price", type=float, default=30.0)
    parser.add_argument("--only-stocks", action="store_true", default=True)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    log_dir = os.path.dirname(args.log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        filename=args.log_file,
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
    )

    if not os.path.exists(args.input_csv):
        raise FileNotFoundError(f"Input CSV not found: {args.input_csv}")

    rs_df = pd.read_csv(args.input_csv)

    required = {"Ticker", "Price", "RS Percentile"}
    missing = required - set(rs_df.columns)
    if missing:
        raise RuntimeError(f"Missing required columns from {args.input_csv}: {missing}")

    scan_df = rs_df.copy()

    scan_df["Price"] = pd.to_numeric(scan_df["Price"], errors="coerce")
    scan_df["RS Percentile"] = pd.to_numeric(scan_df["RS Percentile"], errors="coerce")

    scan_df = scan_df[
        (scan_df["Price"] >= args.min_price)
        & (scan_df["RS Percentile"] >= args.rs_threshold)
    ].copy()

    if args.only_stocks:
        if "Type" in scan_df.columns:
            scan_df = scan_df[scan_df["Type"].astype(str).str.upper().ne("ETF")].copy()
        elif "Sector" in scan_df.columns:
            scan_df = scan_df[scan_df["Sector"].astype(str).str.upper().ne("ETF")].copy()

    lib, symbols = load_arctic_db(args.arctic_db_path)
    symbol_set = set(symbols)

    results = []
    fail_stats = {
        "total_scanned": 0,
        "not_enough_data": 0,
        "not_enough_pivots": 0,
        "not_enough_contractions": 0,
        "base_length_fail": 0,
        "first_depth_fail": 0,
        "final_depth_fail": 0,
        "tightening_fail": 0,
        "nested_range_fail": 0,
        "valid_vcp": 0,
        "breakout_yes": 0,
        "breakout_no": 0,
        "current_base_quality_fail": 0,
        "above_pivot_without_bo_fail": 0,
        "below_pivot_too_far_fail": 0,
        "last10_range_fail": 0,
        "last20_range_fail": 0,
        "pivot_touch_fail": 0,
        "not_found_in_arcticdb": 0,
        "exceptions": 0,
    }

    print("=== VCP + BO SCANNER START ===")
    print(f"ArcticDB path: {args.arctic_db_path}")
    print(f"Input CSV: {args.input_csv}")
    print(f"Output dir: {args.output_dir}")
    print(f"RS threshold: {args.rs_threshold}")
    print(f"Min price: {args.min_price}")
    print(f"Candidates after RS/Price filter: {len(scan_df):,}")

    for _, meta in scan_df.iterrows():
        ticker = str(meta["Ticker"]).strip()

        if ticker not in symbol_set:
            fail_stats["not_found_in_arcticdb"] += 1
            logging.info(f"{ticker}: not found in ArcticDB")
            continue

        try:
            data = lib.read(ticker).data
            row = scan_one_ticker(ticker, data, DEFAULTS, fail_stats)

            if row is None:
                continue

            for col in [
                "Rank", "Price", "DVol", "Sector", "Industry",
                "RS Percentile", "1M_RS Percentile", "3M_RS Percentile", "6M_RS Percentile",
                "ATR", "ADR", "AvgVol", "AvgVol10", "52WKH", "52WKL", "MCAP", "IPO",
                "SMA50", "SMA200", "SMA10W", "SMA30W",
                "History_Days", "Gap (%)", "Latest Volume", "9M+ Volume", "HVE", "HVE Date", "HVE Volume"
            ]:
                if col in meta.index and col not in row:
                    row[col] = meta[col]

            results.append(row)

        except Exception as e:
            fail_stats["exceptions"] += 1
            logging.info(f"{ticker}: exception: {e}")

    out = pd.DataFrame(results)

    vcp_path = os.path.join(args.output_dir, "VCP_Stocks.csv")
    bo_path = os.path.join(args.output_dir, "VCP_BO_Stocks.csv")

    preferred_cols = [
        "Ticker", "Date", "Price", "Volume", "AvgVol50", "Vol_x_50d",
        "Pivot", "Pivot_Date", "Extended_%", "VCP", "BO",
        "Contractions", "Contraction_Depths",
        "First_Contraction_%", "Final_Contraction_%",
        "Base_Length", "Base_Start", "Base_End", "VDU_x",
        "Distance_From_Pivot_%", "Last10_Range_%", "Last20_Range_%", "Pivot_Touches",
        "Rank", "Sector", "Industry",
        "RS Percentile", "1M_RS Percentile", "3M_RS Percentile", "6M_RS Percentile",
        "ATR", "ADR", "AvgVol", "AvgVol10", "52WKH", "52WKL", "MCAP", "IPO",
        "SMA50", "SMA200", "SMA10W", "SMA30W",
        "History_Days", "Gap (%)", "Latest Volume", "9M+ Volume", "HVE", "HVE Date", "HVE Volume"
    ]

    print("\n=== VCP FAILURE SUMMARY ===")
    for k, v in fail_stats.items():
        print(f"{k}: {v:,}")

    if out.empty:
        print("\nNo VCP candidates found. No VCP files created.")
        return

    out = out.sort_values(
        ["BO", "RS Percentile", "Vol_x_50d", "Extended_%"],
        ascending=[False, False, False, True],
        na_position="last",
    )

    available_cols = [c for c in preferred_cols if c in out.columns]
    out[available_cols].to_csv(vcp_path, index=False, na_rep="")

    bo = out[out["BO"].astype(str).str.upper().eq("YES")].copy()

    if not bo.empty:
        bo[available_cols].to_csv(bo_path, index=False, na_rep="")

    print("\n=== VCP + BO SCANNER COMPLETE ===")
    print(f"VCP candidates: {len(out):,}")
    print(f"Breakouts: {len(bo):,}")
    print(f"Saved: {vcp_path}")
    if not bo.empty:
        print(f"Saved: {bo_path}")
    else:
        print("No breakout candidates found. No VCP_BO_Stocks.csv created.")


if __name__ == "__main__":
    main()