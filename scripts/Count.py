#!/usr/bin/env python3
import json
import os

# List of ticker file paths
TICKER_FILES = [
    r"C:\Users\dipen\Downloads\ticker_info.json",
    r"C:\Users\dipen\Downloads\ticker_price.json"
]

def count_tickers(filepath: str) -> int:
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return 0

    with open(filepath, "r") as f:
        data = json.load(f)
        count = len(data)
        print(f"✅ {os.path.basename(filepath)}: {count} tickers")
        return count

if __name__ == "__main__":
    total = 0
    for path in TICKER_FILES:
        total += count_tickers(path)

    print(f"\n📊 Total tickers across all files: {total}")