from yahooquery import Screener
import pandas as pd
from tabulate import tabulate
import re
from datetime import datetime

# Initialize the Screener
s = Screener()

# Check available screeners
try:
    available_screeners = s.available_screeners
    print("Available Screeners:", available_screeners)
    if 'top_options_open_interest' not in available_screeners:
        print("Error: 'top_options_open_interest' not found in available screeners.")
        exit()
except Exception as e:
    print(f"Error fetching available screeners: {e}")
    exit()

# Fetch all available results for 'top_options_open_interest'
max_count = 250
data = None
for count in [max_count, 250, 100]:  # Try decreasing counts
    try:
        print(f"Attempting to fetch {count} results...")
        data = s.get_screeners('top_options_open_interest', count=count)
        break
    except Exception as e:
        print(f"Failed with count={count}: {e}")
        continue

if data is None:
    print("Failed to fetch data with any count. Check API or internet connection.")
    exit()

# Check if data is a string (error message)
if isinstance(data, str):
    print(f"API returned string instead of dictionary: {data}")
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

            # Convert month name to number
            try:
                month_num = datetime.strptime(month, "%b").month
                date = f"{month_num:02d}-15-{year[-2:]}"  # Assume 15th
            except ValueError:
                date = "N/A"

            strike_option = f"{base_ticker} {date} {strike} {option_type}"
            ticker = symbol
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
            strike = str(int(match.group(6)) / 1000)
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
        'Base Ticker': base_ticker,
        'Bid': quote.get('bid', 'N/A'),
        'Ask': quote.get('ask', 'N/A')
    }
    table_data.append(row)

# Convert to DataFrame
df = pd.DataFrame(table_data)

# Convert columns to numeric for sorting and analysis
df['Options OI'] = pd.to_numeric(df['Options OI'], errors='coerce')
df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
df['Bid'] = pd.to_numeric(df['Bid'], errors='coerce')
df['Ask'] = pd.to_numeric(df['Ask'], errors='coerce')

# Calculate bid-ask spread
df['Spread'] = df['Ask'] - df['Bid']
df['Spread Pct'] = (df['Spread'] / df['Ask']) * 100

# Group by Base Ticker and sort by Options OI
df = df.sort_values(by=['Base Ticker', 'Options OI'], ascending=[True, False])

# Display table
print(f"\nAll Options by Open Interest (Grouped by Base Ticker, Total: {len(df)} Contracts):")
print(tabulate(df[['Ticker', 'Date', 'Options OI', 'Price']],
               headers='keys', tablefmt='psql', showindex=False, floatfmt=".2f"))

# Analyze top 10 opportunities
print("\nTop 10 Trading Opportunities:")
print("-" * 50)

# Filter for high OI (>1000) and sort by OI
viable_options = df[df['Options OI'] > 1000].copy()
if viable_options.empty:
    print("No options with open interest > 1000 found.")
else:
    top_10 = viable_options.sort_values(by='Options OI', ascending=False).head(10)

    # Display top 10 table
    print(tabulate(top_10[['Ticker', 'Date', 'Options OI', 'Price']],
                   headers='keys', tablefmt='psql', showindex=False, floatfmt=".2f"))

    # Provide rationale for each
    print("\nRationale for Top 10 Opportunities:")
    print("-" * 50)
    for idx, row in top_10.iterrows():
        spread_info = "N/A"
        if pd.notna(row['Bid']) and pd.notna(row['Ask']) and row['Ask'] > 0:
            spread_info = f"{row['Spread']:.2f} ({row['Spread Pct']:.2f}% of ask)"

        print(f"Opportunity {idx + 1}: {row['Ticker']}")
        print(f"Details: {row['Date']}")
        print(f"Open Interest: {row['Options OI']:.0f}")
        print(f"Price: ${row['Price']:.2f}")
        print(f"Bid-Ask Spread: {spread_info}")
        print(f"Rationale: High open interest ({row['Options OI']:.0f}) indicates strong liquidity. "
              f"{'Call' if 'CALL' in row['Date'] else 'Put'} option suggests "
              f"{'bullish' if 'CALL' in row['Date'] else 'bearish'} sentiment for {row['Base Ticker']}.")
        if pd.notna(row['Spread Pct']) and row['Spread Pct'] < 10:
            print(f"- Tight spread ({row['Spread Pct']:.2f}%) enhances cost efficiency.")
        print("- Check underlying price trend and volume to confirm sentiment.")
        print("-" * 50)