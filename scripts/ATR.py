#!/usr/bin/env python3
import arcticdb as adb
import pandas as pd
import numpy as np

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    """Calculate current ATR (Wilder method)"""
    if len(high) < period + 1 or len(low) < period + 1 or len(close) < period + 1:
        return np.nan

    # True Range
    tr0 = high - low
    tr1 = (high - close.shift(1)).abs()
    tr2 = (low - close.shift(1)).abs()
    tr = pd.concat([tr0, tr1, tr2], axis=1).max(axis=1)

    # Wilder smoothing (first ATR is simple average, then smoothed)
    atr = tr.rolling(window=period).mean().iloc[-1]  # You can implement full Wilder if needed
    return round(atr, 4)


def calculate_adr(high: pd.Series, low: pd.Series, period: int = 14) -> float:
    """Calculate Average Daily Range (simple High - Low average)"""
    if len(high) < period or len(low) < period:
        return np.nan

    daily_range = high - low
    adr = daily_range.rolling(window=period).mean().iloc[-1]
    return round(adr, 4)


def test_volatility_functions():
    # ================== CONFIG ==================
    db_path = r"C:\Users\dipen\Downloads\arctic-db-merged"   # ← Change if needed
    # ===========================================

    try:
        arctic = adb.Arctic(f"lmdb://{db_path}")
        lib = arctic.get_library("prices")
        symbols = lib.list_symbols()
        print("✅ Connected. Total symbols:", len(symbols))
    except Exception as e:
        print("❌ DB Connection failed:", e)
        return

    # Test tickers (US market)
    tickers = ["AAPL", "MSFT", "NVDA", "LLY", "AMD", "GEV", "ALAB", "SITM", "ACMR", "IRDM", "NBIS", "AMBQ"]  # Added some popular ones

    for ticker in tickers:
        if ticker not in symbols:
            print(f"\n{ticker} not found in library")
            continue

        data = lib.read(ticker).data
        df = pd.DataFrame({
            "open": data["open"].values,
            "high": data["high"].values,
            "low": data["low"].values,
            "close": data["close"].values,
        }, index=pd.to_datetime(data["datetime"], unit='s')).sort_index()

        print(f"\n{'='*80}")
        print(f"Testing {ticker} | Rows: {len(df)} | Last date: {df.index[-1].date()}")
        print('='*80)

        atr14 = calculate_atr(df["high"], df["low"], df["close"], 14)
        adr14 = calculate_adr(df["high"], df["low"], 14)
        atr20 = calculate_atr(df["high"], df["low"], df["close"], 20)
        adr20 = calculate_adr(df["high"], df["low"], 20)

        print(f"ATR(14) : ${atr14:>8}")
        print(f"ADR(14) : ${adr14:>8}")
        print(f"ATR(20) : ${atr20:>8}")
        print(f"ADR(20) : ${adr20:>8}")

        # Optional: % of price
        last_close = df["close"].iloc[-1]
        if last_close > 0:
            print(f"ATR(14)%: {atr14 / last_close * 100:>7.2f}%")
            print(f"ADR(14)%: {adr14 / last_close * 100:>7.2f}%")

        # Last 5 days ranges for quick view
        recent = df.tail(5).copy()
        recent["range"] = recent["high"] - recent["low"]
        print("\nLast 5 days ranges:")
        print(recent[["high", "low", "range"]].round(4))

if __name__ == "__main__":
    test_volatility_functions()