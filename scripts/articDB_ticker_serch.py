#!/usr/bin/env python3
import arcticdb as adb
import pandas as pd
import os
pd.set_option("display.max_rows", None)
def search_ticker(data_dir, ticker, show_all=True, top_n=20):
    try:
        # Ensure consistent URI
        data_dir = data_dir.rstrip("/\\")
        db_uri = f"lmdb://{data_dir}"
        print("✅ ArcticDB URI:", db_uri)

        arctic = adb.Arctic(db_uri)
        libraries = arctic.list_libraries()
        print("📂 Available libraries:", libraries)

        if "prices" not in libraries:
            print(f"❌ No 'prices' library found in {data_dir}")
            return

        lib = arctic.get_library("prices")
        symbols = lib.list_symbols()

        # ✅ Exact match only (case-insensitive)
        matches = [s for s in symbols if s.lower() == ticker.lower()]
        if not matches:
            print(f"❌ Exact ticker '{ticker}' not found in database.")
            return

        symbol = matches[0]  # only one exact match
        try:
            df = lib.read(symbol).data

            # Convert epoch -> datetime if column exists
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'], unit='s')

            print(f"\n--- 📊 Ticker: {symbol} ---")
            if show_all:
                print(df)  # full dataset
            else:
                print(df.head(top_n))  # first few rows

            print(f"✅ Total rows for {symbol}: {len(df)}\n")

        except Exception as inner_e:
            print(f"⚠️ Failed to read {symbol}: {str(inner_e)}")

    except Exception as e:
        print(f"❌ Database error: {str(e)}")


if __name__ == "__main__":
    data_dir = "C:/Users/dipen/Downloads/arctic-db-merged"

    # Ask user for ticker
    ticker = input("🔎 Enter ticker symbol (exact match): ").strip()

    # Always show all rows if exact match found
    search_ticker(data_dir, ticker=ticker, show_all=True)