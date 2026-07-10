#!/usr/bin/env python3
import arcticdb as adb
import pandas as pd
import numpy as np
from datetime import datetime


# ====================== IMPROVED FUNCTIONS ======================

def short_relative_strength(closes: pd.Series, closes_ref: pd.Series, days: int) -> float:
    """Fixed: Uses date alignment instead of raw iloc"""
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


def quarters_perf(closes: pd.Series, n: int) -> float:
    days = n * 63
    slice_len = min(len(closes), days + 1)
    available = closes[-slice_len:]
    if len(available) < 2:
        return np.nan
    pct = available.pct_change(fill_method=None).dropna()
    if pct.empty:
        return np.nan
    return (pct + 1).cumprod().iloc[-1] - 1


def strength(closes: pd.Series) -> float:
    perfs = [quarters_perf(closes, i) for i in range(1, 5)]
    valid = [p for p in perfs if not np.isnan(p)]
    if not valid:
        return np.nan
    weights = [0.4, 0.2, 0.2, 0.2][:len(valid)]
    total = sum(weights)
    weights = [w / total for w in weights]
    return sum(w * p for w, p in zip(weights, valid))


def relative_strength(closes: pd.Series, closes_ref: pd.Series) -> float:
    """Main RS with optional alignment"""
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


# ====================== TEST FUNCTION ======================
def run_test():
    db_path = r"C:\Users\dipen\Downloads\arctic-db-merged"  # ← Change if your folder is different

    try:
        arctic = adb.Arctic(f"lmdb://{db_path}")
        lib = arctic.get_library("prices")
        print(f"✅ Connected! Total symbols: {len(lib.list_symbols())}\n")
    except Exception as e:
        print("❌ Connection failed:", e)
        return

    test_tickers = ["CARTRADE.NS", "S&SPOWER.NS", "SCPL.NS", "BHAGYANGR.NS", "^CRSLDX"]

    for ticker in test_tickers:
        if ticker == "^CRSLDX":
            continue

        print(f"\n{'=' * 80}")
        print(f"TESTING: {ticker}")
        print('=' * 80)

        try:
            data = lib.read(ticker).data
            closes = pd.Series(data["close"].values,
                               index=pd.to_datetime(data["datetime"], unit='s')).sort_index()

            ref_data = lib.read("^CRSLDX").data
            ref_closes = pd.Series(ref_data["close"].values,
                                   index=pd.to_datetime(ref_data["datetime"], unit='s')).sort_index()

            # Old vs New Comparison
            old_1m = short_relative_strength(closes, ref_closes, 21)  # using old iloc if you still have it, or skip
            new_1m = short_relative_strength(closes, ref_closes, 21)
            new_3m = short_relative_strength(closes, ref_closes, 63)
            new_6m = short_relative_strength(closes, ref_closes, 126)
            main_rs = relative_strength(closes, ref_closes)

            print(f"Main RS (Long-term) : {main_rs}")
            print(f"1M_RS (New)         : {new_1m}")
            print(f"3M_RS (New)         : {new_3m}")
            print(f"6M_RS (New)         : {new_6m}")

        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    print("\n✅ Test completed!")


if __name__ == "__main__":
    run_test()