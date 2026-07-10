#!/usr/bin/env python3
import arcticdb as adb
import pandas as pd
import numpy as np

def short_relative_strength(closes: pd.Series, closes_ref: pd.Series, days: int):
    """Original function"""
    if len(closes) < days + 1 or len(closes_ref) < days + 1:
        return np.nan

    price_old = closes.iloc[-days - 1]
    price_new = closes.iloc[-1]
    ref_old = closes_ref.iloc[-days - 1]
    ref_new = closes_ref.iloc[-1]

    stock_ret = price_new / price_old - 1
    ref_ret = ref_new / ref_old - 1

    if ref_ret == 0:
        return np.nan if stock_ret <= 0 else 999.0

    rs = (1 + stock_ret) / (1 + ref_ret) * 100
    return round(rs, 2)


def test_rs_functions():
    # ================== CONFIG ==================
    db_path = r"C:\Users\dipen\Downloads\arctic-db-merged"   # ← Change if needed
    # ===========================================

    try:
        arctic = adb.Arctic(f"lmdb://{db_path}")
        lib = arctic.get_library("prices")
        print("✅ Connected. Total symbols:", len(lib.list_symbols()))
    except Exception as e:
        print("❌ DB Connection failed:", e)
        return

    tickers = ["CARTRADE.NS", "S&SPOWER.NS", "KOVAI.NS", "^CRSLDX"]

    for ticker in tickers:
        if ticker not in lib.list_symbols():
            print(f"\n{ticker} not found")
            continue

        data = lib.read(ticker).data
        closes = pd.Series(data["close"].values,
                          index=pd.to_datetime(data["datetime"], unit='s')).sort_index()

        print(f"\n{'='*70}")
        print(f"Testing {ticker} | Rows: {len(closes)} | Last date: {closes.index[-1].date()}")
        print('='*70)

        if ticker == "^CRSLDX":
            ref_closes = closes
        else:
            ref_data = lib.read("^CRSLDX").data
            ref_closes = pd.Series(ref_data["close"].values,
                                  index=pd.to_datetime(ref_data["datetime"], unit='s')).sort_index()

        # Test 1M RS
        rs_original = short_relative_strength(closes, ref_closes, 21)

        # Test with alignment (better method)
        df_aligned = pd.DataFrame({"stock": closes, "ref": ref_closes}).dropna()
        if len(df_aligned) > 21:
            stock_old = df_aligned["stock"].iloc[-22]
            stock_new = df_aligned["stock"].iloc[-1]
            ref_old = df_aligned["ref"].iloc[-22]
            ref_new = df_aligned["ref"].iloc[-1]

            stock_ret = stock_new / stock_old - 1
            ref_ret = ref_new / ref_old - 1
            rs_aligned = round((1 + stock_ret) / (1 + ref_ret) * 100, 2) if ref_ret != 0 else np.nan
        else:
            rs_aligned = np.nan

        print(f"Original short_relative_strength (iloc) → 1M_RS = {rs_original}")
        print(f"Aligned version (date-aware)         → 1M_RS = {rs_aligned}")
        print(f"Diff: {abs((rs_original or 0) - (rs_aligned or 0)):.2f}")

        # Show last 5 dates
        print("\nLast 5 aligned dates:")
        print(df_aligned.tail(5)[["stock", "ref"]])

if __name__ == "__main__":
    test_rs_functions()