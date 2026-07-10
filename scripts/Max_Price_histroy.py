#!/usr/bin/env python3

import os
import arcticdb as adb
import pandas as pd
from tqdm import tqdm

# ==========================================================
# CONFIG
# ==========================================================

ARCTIC_DB_PATH = r"C:\Users\dipen\Downloads\arctic-db-merged"
OUTPUT_DIR = r"C:\Users\dipen\Downloads\HVE_Data"
LIBRARY_NAME = "prices"

# ==========================================================
# CONNECT TO ARCTICDB
# ==========================================================

arctic = adb.Arctic(f"lmdb://{ARCTIC_DB_PATH}")

if not arctic.has_library(LIBRARY_NAME):
    raise Exception(f"Library '{LIBRARY_NAME}' not found.")

lib = arctic.get_library(LIBRARY_NAME)

symbols = lib.list_symbols()

print(f"Found {len(symbols):,} symbols")

os.makedirs(OUTPUT_DIR, exist_ok=True)

results = []

# ==========================================================
# MAIN LOOP
# ==========================================================

for ticker in tqdm(symbols):

    try:

        data = lib.read(ticker).data

        required = {"datetime", "volume"}

        if not required.issubset(data.columns):
            continue

        df = data.copy()

        df["Date"] = pd.to_datetime(
            df["datetime"],
            unit="s",
            errors="coerce"
        )

        df = df.dropna(subset=["Date", "volume"])

        df = df[df["volume"] > 0]

        df = df.sort_values("Date")

        if len(df) < 2:
            continue

        # --------------------------------------------------

        first_date = df["Date"].iloc[0].date()
        last_date = df["Date"].iloc[-1].date()

        rows = len(df)

        years = round(
            (df["Date"].iloc[-1] - df["Date"].iloc[0]).days / 365.25,
            2
        )

        latest_volume = int(df["volume"].iloc[-1])

        highest_row = df.loc[df["volume"].idxmax()]

        highest_volume = int(highest_row["volume"])

        highest_date = highest_row["Date"].date()

        hve = "Yes" if latest_volume == highest_volume else "No"

        results.append({

            "Ticker": ticker,

            "Rows": rows,

            "Years": years,

            "Start": first_date,

            "End": last_date,

            "Latest Volume": latest_volume,

            "HVE": hve,

            "HVE Date": highest_date,

            "HVE Volume": highest_volume

        })

    except Exception:
        pass

# ==========================================================
# CREATE DATAFRAMES
# ==========================================================

df_all = pd.DataFrame(results)

df_today = df_all[df_all["HVE"] == "Yes"].copy()

# ==========================================================
# SORT
# ==========================================================

df_all = df_all.sort_values(
    ["HVE", "Rows"],
    ascending=[False, False]
)

df_today = df_today.sort_values(
    "HVE Volume",
    ascending=False
)

# ==========================================================
# SAVE
# ==========================================================

all_file = os.path.join(
    OUTPUT_DIR,
    "hve_all_symbols.csv"
)

today_file = os.path.join(
    OUTPUT_DIR,
    "hve_today.csv"
)

df_all.to_csv(
    all_file,
    index=False
)

df_today.to_csv(
    today_file,
    index=False
)

# ==========================================================
# SPY / QQQ SUMMARY
# ==========================================================

print("\n=== SPY / QQQ HISTORY CHECK ===")

for ticker in ["SPY", "QQQ"]:

    if ticker in df_all["Ticker"].values:

        row = df_all[df_all["Ticker"] == ticker].iloc[0]

        print(
            f"{ticker}: "
            f"{row['Rows']:,} rows | "
            f"{row['Years']} years | "
            f"{row['Start']} → {row['End']} | "
            f"HVE={row['HVE']} | "
            f"HVE Date={row['HVE Date']} | "
            f"HVE Volume={row['HVE Volume']:,}"
        )

print()

print(f"Total Symbols : {len(df_all):,}")
print(f"HVE Today     : {len(df_today):,}")

print("\nFiles Created")

print(all_file)
print(today_file)