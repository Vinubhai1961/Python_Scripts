import yfinance as yf
def get_sector_industry(tickers):
    if isinstance(tickers, str):
        tickers = [tickers]  # Convert single ticker to list

    for symbol in tickers:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.get_info()  # New method for latest yfinance

            sector = info.get("sector", "N/A")
            industry = info.get("industry", "N/A")

            print(f"\nTicker: {symbol.upper()}")
            print(f"  Sector  : {sector}")
            print(f"  Industry: {industry}")

        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")


if __name__ == "__main__":
    user_input = input("Enter stock ticker(s) separated by commas (e.g., AAPL, TSLA, MSFT): ")
    tickers_list = [t.strip() for t in user_input.split(",") if t.strip()]
    get_sector_industry(tickers_list)
