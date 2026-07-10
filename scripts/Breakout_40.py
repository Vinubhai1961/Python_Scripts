import pandas as pd

# === File path ===
file_path = r"C:\Users\dipen\Downloads\rs_stocks.csv"

# === Load data ===
df = pd.read_csv(file_path)

# === Calculate percentage from 52-week high ===
df['pct_from_52WKH'] = (df['52WKH'] - df['Price']) / df['52WKH'] * 100

# === Apply your filters ===
breakout_candidates = df[
    (df['RS Percentile'] >= 90) &
    (df['1M_RS Percentile'] >= 85) &
    (df['3M_RS Percentile'] >= 85) &
    (df['6M_RS Percentile'] >= 85) &
    (df['pct_from_52WKH'] <= 5) &
    (df['DVol'] > df['AvgVol'])
].copy()

# === Calculate volume surge ratio ===
breakout_candidates['vol_surge_ratio'] = breakout_candidates['DVol'] / breakout_candidates['AvgVol']

# === Sort by RS Percentile & volume surge ratio ===
breakout_candidates = breakout_candidates.sort_values(
    by=['RS Percentile', 'vol_surge_ratio'], ascending=[False, False]
)

# === Select top 40 ===
top_40 = breakout_candidates.head(40).copy()

# === Sort by MCAP (highest first) then DVol (highest first) ===
top_40 = top_40.sort_values(by=['MCAP', 'DVol'], ascending=[False, False])

# === Create comma-separated ticker list ===
ticker_list = ", ".join(top_40['Ticker'].astype(str))

# === Print ticker list ===
print("\n=== Ticker List (MCAP Highest → Lowest, then Volume) ===\n")
print(ticker_list)

# === Optional: Save to text file ===
output_txt = r"C:\Users\dipen\Downloads\top_40_tickers_by_MCAP_and_Volume.txt"
with open(output_txt, "w") as f:
    f.write(ticker_list)
print(f"\nSaved ticker list to: {output_txt}")
