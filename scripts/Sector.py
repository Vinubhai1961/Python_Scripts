import yfinance as yf
import time
from requests.exceptions import HTTPError

# List of failed tickers from the log (example, expand as needed)
failed_tickers = [
    "PSUBNKBEES.NS"
    # Add more tickers from your error.log here...
]


def fetch_ticker_info(symbol):
    """Fetch sector, industry, and price for a given ticker with retry logic."""
    max_retries = 3
    retry_delay = 5  # Initial delay in seconds
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price = info.get('regularMarketPrice', info.get('previousClose', info.get('lastPrice')))

            if price is None:
                raise ValueError("Price data not available")

            return {
                "Sector": info.get('sector', 'N/A'),
                "Industry": info.get('industry', 'N/A'),
                "Price": round(float(price), 2)
            }
        except HTTPError as e:
            if attempt < max_retries - 1 and "429" in str(e):  # Too Many Requests
                print(f"HTTP Error 429 for {symbol}, retrying in {retry_delay * (2 ** attempt)} seconds...")
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                continue
            print(f"HTTP Error fetching data for {symbol}: {str(e)}")
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
        return None


def main():
    results = {}
    for ticker in failed_tickers:
        print(f"Testing {ticker}...")
        info = fetch_ticker_info(ticker)
        if info:
            print(f"Ticker: {ticker}")
            print(f"  Sector: {info['Sector']}")
            print(f"  Industry: {info['Industry']}")
            print(f"  Price: ${info['Price']}")
            results[ticker] = info
        time.sleep(2)  # Add delay to avoid rate limiting

    # Create data directory if it doesn't exist
    import os
    os.makedirs('data', exist_ok=True)

    # Save results to a file
    with open('data/failed_ticker_info.json', 'w') as f:
        import json
        json.dump(results, f, indent=2)

    print(f"\nTested {len(results)} failed tickers")


if __name__ == "__main__":
    main()