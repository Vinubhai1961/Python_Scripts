import pandas as pd

# Use raw string for Windows path
file_path = r"C:\Users\dipen\Downloads\vcp_08042025.csv"


# Load CSV and drop rows with missing Section or Ticker
df = pd.read_csv(file_path, on_bad_lines='skip')
df = df.dropna(subset=["Section", "Ticker"])

# Maintain section order as it appears in the file
ordered_sections = df["Section"].dropna().drop_duplicates()

# Track all tickers
all_tickers = set()

# Build the combined output
combined_parts = []
for section in ordered_sections:
    section_df = df[df["Section"] == section]
    section_tickers = section_df["Ticker"].dropna().drop_duplicates().tolist()  # preserve order
    all_tickers.update(section_tickers)
    combined_parts.append(f"{section}, " + ", ".join(section_tickers))

# Create the final single line
final_line = ", ".join(combined_parts)

# Output results
print(final_line)
print(f"\n✅ Total unique tickers: {len(all_tickers)}")