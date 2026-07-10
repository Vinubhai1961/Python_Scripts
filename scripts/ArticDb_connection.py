#!/usr/bin/env python3
import arcticdb as adb
import pandas as pd
import numpy as np

# ====================== ALL CORE FUNCTIONS ======================

def quarters_perf(closes: pd.Series, n: int) -> float:
    days = n * 63
    slice_len = min(len(closes), days + 1)
    available_data = closes[-slice_len:]
    if len(available_data) < 2:
        return np.nan
    pct_change = available_data.pct_change(fill_method=None).dropna()
    if pct_change.empty:
        return np.nan
    return (pct_change + 1).cumprod().iloc[-1] - 1


def strength(closes: pd.Series) -> float:
    perfs = [quarters_perf(closes, i) for i in range(1, 5)]
    valid_perfs = [p for p in perfs if not np.isnan(p)]
    if not valid_perfs:
        return np.nan
    weights = [0.4, 0.2, 0.2, 0.2][:len(valid_perfs)]
    total_weight = sum(weights)
    weights = [w / total_weight for w in weights]
    return sum(w * p for w, p in zip(weights, valid_perfs))


def relative_strength(closes: pd.Series, closes_ref: pd.Series) -> float:
    df = pd.DataFrame({"stock": closes, "ref": closes_ref}).dropna()
    if len(df) > 100:
        closes = df["stock"]
        closes_ref = df["ref"]
    rs_stock = strength(closes)
    rs_ref = strength(closes_ref)
    if np.isnan(rs_stock) or np.isnan(rs_ref):
        return np.nan
    rs = (1 + rs_stock) / (1 + rs_ref) * 100
    return round(rs, 2) if rs <= 700 else 700.0


def short_relative_strength(closes: pd.Series, closes_ref: pd.Series, days: int) -> float:
    if len(closes) < days + 5 or len(closes_ref) < days + 5:
        return np.nan
    df = pd.DataFrame({"stock": closes, "ref": closes_ref}).dropna().sort_index()
    if len(df) < days + 1:
        return np.nan
    price_old = df["stock"].iloc[-days - 1]
    price_new = df["stock"].iloc[-1]
    ref_old = df["ref"].iloc[-days - 1]
    ref_new = df["ref"].iloc[-1]

    if any(x <= 0 or pd.isna(x) for x in [price_new, price_old, ref_new, ref_old]):
        return np.nan

    stock_ret = price_new / price_old - 1
    ref_ret = ref_new / ref_old - 1
    if abs(ref_ret) < 0.0001:
        return np.nan if stock_ret <= 0 else 999.0
    rs = (1 + stock_ret) / (1 + ref_ret) * 100
    return round(rs, 2) if rs <= 700 else 700.0


# ====================== PERCENTILE + FINAL OUTPUT TEST ======================
def run_percentile_test():
    db_path = r"C:\Users\dipen\Downloads\arctic-db-merged"   # Change only if needed

    arctic = adb.Arctic(f"lmdb://{db_path}")
    lib = arctic.get_library("prices")
    print(f"✅ Connected. Total symbols: {len(lib.list_symbols())}\n")

    ref_data = lib.read("^CRSLDX").data
    ref_closes = pd.Series(ref_data["close"].values,
                         index=pd.to_datetime(ref_data["datetime"], unit='s')).sort_index()

    test_tickers = ["CARTRADE.NS", "S&SPOWER.NS", "SCPL.NS", "BHAGYANGR.NS", "TRENT.NS", "MOTHERSON.NS"]

    results = []
    for ticker in test_tickers:
        data = lib.read(ticker).data
        closes = pd.Series(data["close"].values,
                         index=pd.to_datetime(data["datetime"], unit='s')).sort_index()

        raw_rs = relative_strength(closes, ref_closes)
        rs_1m = short_relative_strength(closes, ref_closes, 21)

        results.append({
            "Ticker": ticker,
            "Raw_RS": raw_rs,
            "1M_RS": rs_1m
        })

    df = pd.DataFrame(results)

    # === PERCENTILE CONVERSION (Exact logic from your main script) ===
    for col in ["Raw_RS", "1M_RS"]:
        valid = df[col].dropna()
        if not valid.empty:
            df[f"{col}_Percentile"] = (valid.rank(pct=True, method='min') * 99).astype(int)

    df = df.sort_values("Raw_RS", ascending=False).reset_index(drop=True)
    df["Rank"] = df.index + 1

    print("=== FINAL OUTPUT SIMULATION (rs_stocks.csv style) ===")
    print(df[["Rank", "Ticker", "Raw_RS", "Raw_RS_Percentile", "1M_RS", "1M_RS_Percentile"]].round(2))

    print("\n" + "="*70)
    print("THRESHOLD CHECK (Top percentiles):")
    print(f"98th percentile Raw RS ≈ {df['Raw_RS'].quantile(0.98):.2f}")
    print(f"89th percentile Raw RS ≈ {df['Raw_RS'].quantile(0.89):.2f}")
    print(f"69th percentile Raw RS ≈ {df['Raw_RS'].quantile(0.69):.2f}")
    print("="*70)

    # CARTRADE.NS specific check
    car = df[df["Ticker"] == "CARTRADE.NS"]
    if not car.empty:
        print(f"\n🎯 CARTRADE.NS Final Result:")
        print(f"   Rank                    : {int(car.iloc[0]['Rank'])}")
        print(f"   Raw RS                  : {car.iloc[0]['Raw_RS']:.2f}")
        print(f"   RS Percentile (0-99)    : {int(car.iloc[0]['Raw_RS_Percentile'])}")

if __name__ == "__main__":
    run_percentile_test()