import yfinance as yf
import pandas as pd
import datetime

# Define the ticker symbol
symbol = 'TSLA'
ticker = yf.Ticker(symbol)

# --- 1. Get Current and Previous Day's Prices ---
# In yfinance, info is a dictionary that needs to be accessed slightly differently
# We fetch the info dictionary once
data_info = ticker.info
current_price = data_info.get('currentPrice') or data_info.get(
    'ask')  # Fallback to 'ask' if 'currentPrice' isn't immediately available
previous_close = data_info.get('previousClose')

if current_price is None or previous_close is None:
    print("Could not retrieve current or previous close price data.")
    exit()

print(f"TSLA Current Price: ${current_price:.2f}")
print(f"TSLA Previous Close: ${previous_close:.2f}\n")

# --- 2. Define Target Price Points and Ranges ---
price_targets = {
    "Current Price Range": current_price,
    "Previous Close Range": previous_close
}
price_delta = 5.0

# --- 3. Get Options Chain Data ---
# In yfinance, the options data is accessed via a method, not a direct attribute
options_data = None
try:
    # yfinance requires you to specify a date first if you want specific options
    # The simplest way is to iterate through all dates provided by the library:
    all_options_dfs = []
    for date in ticker.options:
        opt_chain = ticker.option_chain(date)
        # Combine calls and puts into a single DataFrame per date
        calls = opt_chain.calls
        puts = opt_chain.puts
        # Add a column to identify option type (required for my previous logic)
        calls['optionType'] = 'call'
        puts['optionType'] = 'put'

        # Combine for easier filtering later
        combined = pd.concat([calls, puts])
        combined['expirationDate'] = date  # Add the date as a column
        all_options_dfs.append(combined)

    options_data = pd.concat(all_options_dfs)

except Exception as e:
    print(f"Error retrieving options data with yfinance: {e}")
    exit()

if options_data.empty:
    print("Could not retrieve options data.")
else:
    # --- 4. Filter and Display Results for Each Price Target ---
    for target_name, target_price in price_targets.items():
        lower_bound = target_price - price_delta
        upper_bound = target_price + price_delta

        print(f"--- Options Open Interest around {target_name} (${target_price:.2f} +/- ${price_delta}) ---")
        print(f"Search Range: ${lower_bound:.2f} to ${upper_bound:.2f}\n")

        # Iterate through unique expiration dates in the combined dataframe
        for expiration_date in options_data['expirationDate'].unique():
            exp_data = options_data[options_data['expirationDate'] == expiration_date]

            # Filter for strike prices within the desired range
            filtered_calls = exp_data[exp_data['optionType'] == 'call']
            filtered_calls = filtered_calls[
                (filtered_calls['strike'] >= lower_bound) &
                (filtered_calls['strike'] <= upper_bound)
                ]

            filtered_puts = exp_data[exp_data['optionType'] == 'put']
            filtered_puts = filtered_puts[
                (filtered_puts['strike'] >= lower_bound) &
                (filtered_puts['strike'] <= upper_bound)
                ]

            # Display results if any options are found for that expiration date
            if not filtered_calls.empty or not filtered_puts.empty:
                print(f"Expiration Date: {expiration_date}")
                if not filtered_calls.empty:
                    print("  Calls (Open Interest | Strike):")
                    # Use .iterrows() or .itertuples() for clean printing
                    for index, row in filtered_calls.iterrows():
                        # yfinance usually returns openInterest as a float/int
                        print(f"    {int(row['openInterest']):,} | ${row['strike']:.2f}")
                if not filtered_puts.empty:
                    print("  Puts (Open Interest | Strike):")
                    for index, row in filtered_puts.iterrows():
                        print(f"    {int(row['openInterest']):,} | ${row['strike']:.2f}")
                print("-" * 20)