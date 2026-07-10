import pandas as pd

# === File path ===
file_path = r"C:\Users\dipen\Downloads\rs_stocks.csv"

# === Load data ===
df = pd.read_csv(file_path)

# === Calculate percentage from 52-week high ===
df['pct_from_52WKH'] = (df['52WKH'] - df['Price']) / df['52WKH'] * 100

# === Filter breakout candidates ===
breakout_candidates = df[
    (df['RS Percentile'] >= 95) &                  # Strong RS
    (df['pct_from_52WKH'] <= 5) &                  # Near 52W high (within 5%)
    (df['DVol'] > df['AvgVol'])                    # Volume > average
].copy()

# === Calculate volume surge ratio ===
breakout_candidates['vol_surge_ratio'] = breakout_candidates['DVol'] / breakout_candidates['AvgVol']

# === Sort by RS Percentile and volume surge ratio ===
breakout_candidates = breakout_candidates.sort_values(
    by=['RS Percentile', 'vol_surge_ratio'], ascending=[False, False]
)

# === Select top 20 ===
top_20_opportunities = breakout_candidates.head(20)

# === Print results ===
print("\n=== Top 20 Breakout Candidates ===\n")
print(top_20_opportunities[['Rank', 'Ticker', 'Price', 'Sector', 'Industry',
                            'RS Percentile', '1M_RS Percentile', '3M_RS Percentile',
                            'pct_from_52WKH', 'vol_surge_ratio']])

# === Optional: Save to CSV ===
output_path = r"C:\Users\dipen\Downloads\top_20_breakouts.csv"
top_20_opportunities.to_csv(output_path, index=False)
print(f"\nSaved top 20 breakout list to: {output_path}")
