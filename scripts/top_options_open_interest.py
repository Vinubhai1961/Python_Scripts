from yahooquery import Screener
import pandas as pd
from tabulate import tabulate
import re
from datetime import datetime

# Initialize the Screener
s = Screener()

# Fetch the top 100 results for 'top_options_open_interest'
try:
    data = s.get_screeners('top_options_open_interest', count=100)
except Exception as e:
    print(f"Error fetching data: {e}")
    print("Try reducing the count or checking your internet connection.")
    exit()

# Extract the quotes from the screener data
quotes = data.get('top_options_open_interest', {}).get('quotes', [])

# Check if data is available
if not quotes:
    print("No data returned for 'top_options_open_interest' screener.")
    exit()


# Function to parse option details from shortName or symbol
def parse_option_details(symbol, short_name):
    ticker = "N/A"
    date = "N/A"
    strike_option = "N/A"
    base_ticker = "N/A"

    # Try parsing shortName (e.g., "HYG Aug 2025 75.000 put")
    if short_name and isinstance(short_name, str):
        match = re.match(r"(\w+)\s+(\w+)\s+(\d{4})\s+(\d+\.\d+)\s+(put|call)", short_name, re.IGNORECASE)
        if match:
            base_ticker = match.group(1)
            month = match.group(2)
            year = match.group(3)
            strike = match.group(4)
            option_type = match.group(5).upper()

            # Convert month name to number (e.g., "Aug" to "08")
            try:
                month_num = datetime.strptime(month, "%b").month
                # Format date as MM-DD-YY (assume 15th for consistency with option expirations)
                date = f"{month_num:02d}-15-{year[-2:]}"
            except ValueError:
                date = "N/A"

            strike_option = f"{base_ticker} {date} {strike} {option_type}"
            ticker = symbol  # Use full symbol as in your example
            return ticker, date, strike_option, base_ticker

    # Fallback: parse symbol (e.g., HYG250815P00079000)
    if symbol and isinstance(symbol, str):
        match = re.match(r"(\w+)(\d{2})(\d{2})(\d{2})([PC])(\d+)", symbol)
        if match:
            base_ticker = match.group(1)
            year = f"20{match.group(2)}"
            month = match.group(3)
            day = match.group(4)
            option_type = "PUT" if match.group(5) == "P" else "CALL"
            strike = str(int(match.group(6)) / 1000)  # Convert to decimal (e.g., 00079000 to 79.0)

            date = f"{month}-{day}-{year[-2:]}"
            strike_option = f"{base_ticker} {date} {strike} {option_type}"
            ticker = symbol
            return ticker, date, strike_option, base_ticker

    return ticker, date, strike_option, base_ticker


# Prepare data for table
table_data = []
for quote in quotes:
    symbol = quote.get('symbol', 'N/A')
    short_name = quote.get('shortName', 'N/A')
    ticker, date, strike_option, base_ticker = parse_option_details(symbol, short_name)
    row = {
        'Ticker': ticker,
        'Date': strike_option,
        'Options OI': quote.get('openInterest', 'N/A'),
        'Price': quote.get('regularMarketPrice', 'N/A'),
        'Base Ticker': base_ticker
    }
    table_data.append(row)

# Convert to DataFrame
df = pd.DataFrame(table_data)

# Group by Base Ticker and sort by Options OI within each group
df['Options OI'] = pd.to_numeric(df['Options OI'], errors='coerce')  # Convert to numeric for sorting
df = df.sort_values(by=['Base Ticker', 'Options OI'], ascending=[True, False])

# Display table
print("\nTop 100 Options by Open Interest (Grouped by Base Ticker):")
print(tabulate(df[['Ticker', 'Date', 'Options OI', 'Price']].head(100),
               headers='keys', tablefmt='psql', showindex=False, floatfmt=".2f"))