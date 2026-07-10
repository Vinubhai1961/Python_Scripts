# fetch_cempro_2y.py
import requests
import pandas as pd
from datetime import datetime, timedelta
import time

# === PUT YOUR TWELVE DATA API KEY HERE ===
API_KEY = "a43ef7caf21a44ecbc4f031e004a7e3c"   # ←← Replace this!

SYMBOL = "CEMPRO"
INTERVAL = "1day"
OUTPUTSIZE = 5000          # Maximum allowed on most plans (enough for >10 years)

# Optional: force 2-year window (uncomment if you want exactly 2 years in the future)
# )
# end_date   = datetime.now()
# start_date = end_date - timedelta(days=730)   # 2 years
# params = {
#     "symbol": SYMBOL,
#     "interval": INTERVAL,
#     "start_date": start_date.strftime("%Y-%m-%d"),
#     "end_date":   end_date.strftime("%Y-%m-%d"),
#     "apikey": API_KEY,
#     "outputsize": OUTPUTSIZE,
#     "format": "JSON"
# }

# Recommended way → let Twelve Data return everything available (best for newly listed stocks)
params = {
    "symbol": SYMBOL,
    "interval": INTERVAL,
    "apikey": API_KEY,
    "outputsize": OUTPUTSIZE,
    "format": "JSON"
}

url = "https://api.twelvedata.com/time_series"

print(f"Fetching historical data for {SYMBOL} from Twelve Data...")
response = requests.get(url, params=params)

if response.status_code != 200:
    raise Exception(f"API error {response.status_code}: {response.text}")

data = response.json()

if data.get("status") == "error":
    raise Exception(f"Twelve Data error: {data.get('message')} (code {data.get('code')})")

# Extract the values list
values = data["values"]

print(f"Received {len(values)} daily candles")

# Convert to pandas DataFrame (nicest format)
df = pd.DataFrame(values)
df["datetime"] = pd.to_datetime(df["datetime"])
df = df.set_index("datetime")
df = df.sort_index()   # oldest → newest

# Convert columns to proper types
for col in ["open", "high", "low", "close", "volume"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

print("\nFirst 5 rows:")
print(df.head())

print("\nLast 5 rows:")
print(df.tail())

# Save to CSV (optional)
csv_filename = "CEMPRO_NS_daily.csv"
df.to_csv(csv_filename)
print(f"\nData saved to {csv_filename}")

# Bonus: also save as Excel if you want
# df.to_excel("CEMPRO_NS_daily.xlsx")