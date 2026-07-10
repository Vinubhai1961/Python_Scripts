#!/usr/bin/env python3
import arcticdb as adb
import pandas as pd
import os

def load_arctic_db(data_dir, max_symbols=1, top_n=10):
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
        print(f"✅ Found {len(symbols)} symbols. Showing TOP {top_n} rows for first {max_symbols} tickers.\n")

        for symbol in symbols[:max_symbols]:
            try:
                df = lib.read(symbol).data

                # Convert timestamps to readable datetime
                if 'datetime' in df.columns:
                    df['datetime'] = pd.to_datetime(df['datetime'], unit='s')

                print(f"--- {symbol} ---")
                print(df.head(top_n))
                print()
            except Exception as inner_e:
                print(f"⚠️ Failed to read {symbol}: {str(inner_e)}")

    except Exception as e:
        print(f"❌ Database error: {str(e)}")

if __name__ == "__main__":
    data_dir = "C:/Users/dipen/Downloads/arctic-db-merged"
    load_arctic_db(data_dir, max_symbols=3, top_n=10)