from yahooquery import Ticker
import pandas as pd

tickers = ["WMB", "FANG", "ON", "NETWEB.BO", "TSLA"]

t = Ticker(tickers)
data = t.calendar_events or {}

rows = []

for symbol in tickers:
    ce = data.get(symbol, {})  # keys are uppercase in your output
    earnings = ce.get("earnings", {})
    ed_list = earnings.get("earningsDate")

    if not ed_list:
        continue

    # Take the first earningsDate string
    raw = ed_list[0]          # e.g. "2026-05-04 16:00:S"
    # Strip the trailing ":S" if present so pandas can parse it cleanly
    cleaned = raw.replace(":S", "")

    dt = pd.to_datetime(cleaned, errors="coerce")
    if pd.isna(dt):
        continue

    rows.append({
        "Ticker_Name": symbol,
        "E_Date": dt.strftime("%m-%d-%Y")
    })

df = pd.DataFrame(rows).sort_values("Ticker_Name")
print(df.to_string(index=False))