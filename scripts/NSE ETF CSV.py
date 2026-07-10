import requests
import pandas as pd

# Define URLs and local filenames
sources = {
    "stocks": {
        "url": "https://archives.nseindia.com/content/equities/EQUITY_L.csv",
        "filename": "nse_stocks.csv"
    },
    "etfs": {
        "url": "https://archives.nseindia.com/content/equities/eq_etfseclist.csv",
        "filename": "nse_etfs.csv"
    }
}

# Standard headers
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Referer": "https://www.nseindia.com/"
}

all_tickers = []

for label, source in sources.items():
    try:
        # Download CSV
        response = requests.get(source["url"], headers=headers)
        response.raise_for_status()

        # Save locally
        with open(source["filename"], "wb") as f:
            f.write(response.content)
        print(f"✅ Downloaded: {source['filename']}")

        # Read CSV and extract symbols
        df = pd.read_csv(source["filename"])

        # Handle symbol column depending on file
        if "SYMBOL" in df.columns:
            tickers = df["SYMBOL"].dropna().astype(str).tolist()
        elif "ISIN" in df.columns:  # ETF file may be different
            tickers = df["ISIN"].dropna().astype(str).tolist()  # adjust if SYMBOL isn't available
        else:
            print(f"⚠️ Unknown format in {source['filename']}")
            tickers = []

        print(f"🔹 Found {len(tickers)} {label.upper()} tickers")
        all_tickers.extend(tickers)

    except Exception as e:
        print(f"❌ Failed to process {label}: {e}")

# Combine and deduplicate
unique_tickers = sorted(set(all_tickers))
print(f"\n✅ Total combined tickers (stocks + ETFs): {len(unique_tickers)}")

# Optional: Save to one file
pd.Series(unique_tickers).to_csv("all_nse_tickers.csv", index=False, header=["Ticker"])
print("📁 Saved combined tickers to: all_nse_tickers.csv")