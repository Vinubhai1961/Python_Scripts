from yahooquery import Ticker
from datetime import datetime

def get_earnings_date(symbols):
    print(f"\nFetching earnings dates for: {symbols}\n")

    yq = Ticker(symbols)
    calendar_events = yq.calendar_events

    results = []

    for sym in symbols:
        earning_date = None
        yahoo_sym = sym.replace(".", "-")

        try:
            cal = calendar_events.get(yahoo_sym, {})
            if isinstance(cal, dict):
                earnings = cal.get("earnings", {})
                if isinstance(earnings, dict):
                    e_dates = earnings.get("earningsDate")

                    if e_dates and isinstance(e_dates, list):
                        ed = e_dates[0]

                        # Convert to string if datetime
                        if hasattr(ed, "strftime"):
                            earning_date = ed.strftime("%m/%d/%Y")
                        else:
                            earning_date = str(ed)

        except Exception as e:
            print(f"{sym}: Error -> {e}")

        results.append({
            "ticker": sym,
            "Earning_Date": earning_date
        })

    return results


if __name__ == "__main__":
    # Test with known large-cap tickers
    test_tickers = ["MSFT", "AAPL", "TSLA", "NVDA", "AMZN", "ULH"]

    data = get_earnings_date(test_tickers)

    print("\n=== RESULTS ===")
    for row in data:
        print(row)