import schwabdev
import requests
import pandas as pd
from time import sleep


def fetch_nasdaq_tickers(limit=500):
    url = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqtraded.txt"
    df = pd.read_csv(url, sep="|", skipfooter=1, engine="python")
    # Filter for valid tickers (exclude test/emergency symbols)
    df = df[df["Test Issue"] == "N"]
    tickers = df["Symbol"].head(limit).tolist()
    return tickers


def batch_tickers(tickers, batch_size=100):
    for i in range(0, len(tickers), batch_size):
        yield tickers[i:i + batch_size]


def get_ticker_info(client, tickers):
    results = []
    # Fetch quotes for multiple tickers
    try:
        response = client.quotes(tickers=",".join(tickers)).json()
        for ticker in tickers:
            ticker_data = response.get(ticker, {})
            if not ticker_data or ticker_data.get("error"):
                print(f"Error fetching quote for {ticker}")
                continue
            price = ticker_data.get("quote", {}).get("lastPrice", "N/A")
            asset_type = ticker_data.get("quote", {}).get("assetMainType", "N/A")
            is_etf = "Y" if asset_type == "ETF" else "N"

            # Fetch fundamental data for sector and industry
            fundamental = client.instrument(ticker=ticker).json()
            sector = fundamental.get(ticker, {}).get("fundamental", {}).get("sector", "N/A")
            industry = fundamental.get(ticker, {}).get("fundamental", {}).get("industry", "N/A")

            results.append({
                "Ticker": ticker,
                "Sector": sector,
                "Industry": industry,
                "Price": f"${price:.2f}" if isinstance(price, (int, float)) else "N/A",
                "ETF": is_etf
            })
    except Exception as e:
        print(f"Error processing batch: {e}")
    return results


def main():
    # Initialize Schwab client
    app_key = "FJh3eSQqGcfwyqQyeqyZh6UuX4igNYZg"  # Replace with your App Key
    app_secret = "Y6URwVqMtJqGjal9"  # Replace with your App Secret
    client = schwabdev.Client(app_key, app_secret)

    # Fetch tickers
    print("Fetching NASDAQ tickers...")
    tickers = fetch_nasdaq_tickers(limit=500)
    print(f"Fetched {len(tickers)} tickers.")

    # Process tickers in batches
    all_results = []
    for batch in batch_tickers(tickers, batch_size=100):
        print(f"Processing batch of {len(batch)} tickers...")
        batch_results = get_ticker_info(client, batch)
        all_results.extend(batch_results)
        sleep(1)  # Avoid hitting API rate limits

    # Print results in specified format
    for result in all_results:
        print(f"Ticker: {result['Ticker']}")
        print(f"Sector: {result['Sector']}")
        print(f"Industry: {result['Industry']}")
        print(f"Price: {result['Price']}")
        print(f"ETF: {result['ETF']}")
        print()


if __name__ == "__main__":
    main()