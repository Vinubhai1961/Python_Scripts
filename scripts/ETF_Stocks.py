import requests
import pandas as pd
from io import StringIO

def fetch_nasdaq_symbols():
    url = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqtraded.txt"
    response = requests.get(url)
    response.raise_for_status()

    # Read into DataFrame
    df = pd.read_csv(StringIO(response.text), sep="|")
    df = df[df['Test Issue'] == 'N']  # Filter only active issues
    df = df[:-1]  # Remove footer row

    # Split by ETF flag
    stocks = df[df['ETF'] == 'N']['Symbol'].tolist()
    etfs = df[df['ETF'] == 'Y']['Symbol'].tolist()

    # Pad to equal length
    max_len = max(len(stocks), len(etfs))
    stocks += [''] * (max_len - len(stocks))
    etfs += [''] * (max_len - len(etfs))

    return stocks, etfs

def display_columns(stocks, etfs):
    print(f"{'Stock':<10} {'ETF':<10}")
    print(f"{'-'*10} {'-'*10}")
    for s, e in zip(stocks, etfs):
        print(f"{s:<10} {e:<10}")

def main():
    stocks, etfs = fetch_nasdaq_symbols()
    display_columns(stocks, etfs)

if __name__ == "__main__":
    main()