from yahooquery import Ticker


def get_last_4_earnings_dates_from_data(ticker_symbol):
    """
    Extracts and prints the last four quarterly earnings dates
    from the data structure provided by yahooquery.
    """
    try:
        # Create a Ticker object for the specified symbol
        ticker = Ticker(ticker_symbol)

        # Access the earnings chart data
        earnings_data_dict = ticker.quote_summary[ticker_symbol]['earnings']['earningsChart']['quarterly']

        # Extract the 'date' field from each dictionary in the list
        earnings_dates = [item['date'] for item in earnings_data_dict]

        # Sort the dates in reverse chronological order (assuming 'date' is a sortable string)
        earnings_dates.sort(reverse=True)

        # Get the most recent four dates
        last_4_dates = earnings_dates[:4]

        print(f"Last four quarterly earnings dates for {ticker_symbol.upper()}:")
        for date_str in last_4_dates:
            print(f"  - {date_str}")

    except (KeyError, TypeError) as e:
        print(f"An error occurred while parsing yahooquery data for {ticker_symbol}: {e}")
        print("The data structure may have changed. The yfinance method is generally more stable.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# Example usage: Get the last 4 earnings dates for Apple (AAPL)
get_last_4_earnings_dates_from_data('aapl')
