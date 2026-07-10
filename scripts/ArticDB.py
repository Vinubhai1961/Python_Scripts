#!/usr/bin/env python3
import arcticdb as adb
import os
import pandas as pd
def load_arctic_db(data_dir):
    try:
        # Connect to ArcticDB using LMDB format
        db_uri = f"lmdb://{data_dir}"
        arctic = adb.Arctic(db_uri)

        # Ensure 'prices' library exists
        if not arctic.has_library("prices"):
            print(f"No 'prices' library found in {data_dir}")
            return

        # Get the 'prices' library
        lib = arctic.get_library("prices")

        # List all symbols (tickers) in the library
        symbols = lib.list_symbols()
        print(f"Found {len(symbols)} symbols: {symbols[:10]}...")  # Show first 10

        # Read an example symbol
        if symbols:
            sample_symbol = symbols[0]
            data = lib.read(sample_symbol).data
            # Allow unlimited horizontal width
            pd.set_option('display.width', None)
            # Show all columns without truncation
            pd.set_option('display.max_columns', None)

            print(f"\nData for '{sample_symbol}':")
            print(data.head())
        else:
            print("No data available in the library.")

    except Exception as e:
        print(f"Database error: {str(e)}")


if __name__ == "__main__":
    # Path should be the folder containing the library, not the library itself
    data_dir = "C:/Users/dipen/Downloads/arctic-db-merged"
    load_arctic_db(data_dir)
