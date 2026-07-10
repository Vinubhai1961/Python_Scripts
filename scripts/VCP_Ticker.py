import pandas as pd
import glob
import os

# Define the path pattern to scan all vcp_*.csv files
folder_path = r"C:\Users\dipen\Downloads\watchlist"
file_pattern = os.path.join(folder_path, "vcp_*.csv")

# Find all matching CSV files
csv_files = glob.glob(file_pattern)

# Collect tickers and MCAP data
ticker_mcap_data = []

for file in csv_files:
    try:
        df = pd.read_csv(file)
        if 'Ticker' in df.columns and 'MCAP' in df.columns:
            # Select only Ticker and MCAP columns
            temp_df = df[['Ticker', 'MCAP']].dropna()
            temp_df['Ticker'] = temp_df['Ticker'].astype(str)
            ticker_mcap_data.append(temp_df)
        else:
            print(f"Skipping file (missing 'Ticker' or 'MCAP' column): {file}")
    except Exception as e:
        print(f"Error reading {file}: {e}")

# Combine all dataframes
if ticker_mcap_data:
    combined_df = pd.concat(ticker_mcap_data, ignore_index=True)

    # Remove duplicates by keeping the latest entry (if any)
    # Assuming the latest file has the most recent MCAP data
    combined_df = combined_df.sort_values(by='MCAP', ascending=False).drop_duplicates(subset='Ticker', keep='first')

    # Sort by MCAP in descending order
    sorted_df = combined_df.sort_values(by='MCAP', ascending=False)

    # Extract tickers
    tickers = sorted_df['Ticker'].tolist()

    # Join tickers into a single string
    ticker_line = ", ".join(tickers)

    # Output results
    print("Tickers for TradingView (sorted by MCAP, highest to lowest):")
    print(ticker_line)
    print(f"\nTotal number of unique tickers: {len(tickers)}")
else:
    print("No valid data found in the CSV files.")