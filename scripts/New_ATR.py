#!/usr/bin/env python3
import arcticdb as adb
import pandas as pd
import numpy as np


def get_atr_adr(ticker: str, period: int = 14, db_path: str = None):
    """Returns (ATR, ADR) for the ticker"""
    if db_path is None:
        db_path = r"C:\Users\dipen\Downloads\arctic-db-merged"

    try:
        arctic = adb.Arctic(f"lmdb://{db_path}")
        lib = arctic.get_library("prices")

        if ticker not in lib.list_symbols():
            return np.nan, np.nan

        data = lib.read(ticker).data
        df = pd.DataFrame({
            "high": data["high"].values,
            "low": data["low"].values,
            "close": data["close"].values,
        }, index=pd.to_datetime(data["datetime"], unit='s')).sort_index()

        if len(df) < period + 1:
            return np.nan, np.nan

        # True Range
        tr0 = df["high"] - df["low"]
        tr1 = (df["high"] - df["close"].shift(1)).abs()
        tr2 = (df["low"] - df["close"].shift(1)).abs()
        tr = pd.concat([tr0, tr1, tr2], axis=1).max(axis=1)

        atr = tr.rolling(window=period).mean().iloc[-1]
        adr = (df["high"] - df["low"]).rolling(window=period).mean().iloc[-1]

        return round(float(atr), 4), round(float(adr), 4)

    except Exception as e:
        print(f"Error with {ticker}: {e}")
        return np.nan, np.nan


# ====================== TEST ======================
if __name__ == "__main__":
    db_path = r"C:\Users\dipen\Downloads\arctic-db-merged"

    tickers = ["AMBQ", "AAPL", "MSFT", "NVDA", "LLY", "AMD", "GEV", "ALAB", "SITM"]

    print(f"{'Ticker':<8} {'ATR(14)':<12} {'ADR(14)':<12}")
    print("-" * 40)

    for ticker in tickers:
        atr, adr = get_atr_adr(ticker, period=14, db_path=db_path)

        if np.isnan(atr):
            print(f"{ticker:<8} Data unavailable")
        else:
            print(f"{ticker:<8} {atr:<12} {adr:<12}")