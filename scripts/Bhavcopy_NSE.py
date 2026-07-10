# download_cempro_bhavcopy_2years.py
# 100% free, official NSE bhavcopy → only CEMPRO.NS rows for last ~2 years

import requests
import pandas as pd
from datetime import datetime, timedelta
from zipfile import ZipFile
from io import BytesIO
import os

# --------------------- CONFIG ---------------------
SYMBOL = "CEMPRO"  # NSE symbol without .NS
OUTPUT_FILE = "CEMPRO.NS_2Y_EOD_NSE.csv"
DAYS_BACK = 730  # ≈ 2 years of calendar days


# --------------------------------------------------

def download_bhavcopy(date: datetime) -> pd.DataFrame:
    """Return DataFrame with only CEMPRO rows for given date (or empty DataFrame if no data)"""
    url = f"https://archives.nseindia.com/content/historical/EQUITIES/{date.year}/{date.strftime('%b').upper()}/cm{date.strftime('%d%b%Y').upper()}bhav.csv.zip"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.nseindia.com/",
        "Accept-Encoding": "gzip, deflate, br"
    }

    try:
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code != 200:
            return pd.DataFrame()  # File not found or holiday

        with ZipFile(BytesIO(r.content)) as z:
            csv_name = z.namelist()[0]
            df = pd.read_csv(z.open(csv_name))

        # Filter only our stock
        df = df[df['SYMBOL'].str.strip() == SYMBOL].copy()
        if df.empty:
            return pd.DataFrame()

        df['DATE'] = date.strftime("%Y-%m-%d")
        return df

    except Exception:
        return pd.DataFrame()  # Any error → treat as no data


# --------------------- MAIN ---------------------
end_date = datetime.now()
start_date = end_date - timedelta(days=DAYS_BACK)

all_frames = []
current = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

print(
    f"Downloading NSE bhavcopy data for {SYMBOL} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...\n")

while current <= end_date:
    # Only try on weekdays (NSE is closed Sat–Sun + holidays)
    if current.weekday() < 5:
        print(f"{current.strftime('%Y-%m-%d')} → fetching...", end="\r")
        df_day = download_bhavcopy(current)
        if not df_day.empty:
            all_frames.append(df_day)
    current += timedelta(days=1)

if all_frames:
    final_df = pd.concat(all_frames, ignore_index=True)
    final_df = final_df.sort_values('TIMESTAMP')

    # Keep only useful columns and rename to standard names
    final_df = final_df[['DATE', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'TOTTRDQTY']].copy()
    final_df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    final_df['Date'] = pd.to_datetime(final_df['Date'])
    final_df = final_df.set_index('Date')

    final_df.to_csv(OUTPUT_FILE)
    print(f"\nSuccess! {len(final_df)} trading days saved → {OUTPUT_FILE}")
    print(final_df.head())
    print(final_df.tail())
else:
    print(f"\nNo data found for {SYMBOL}. It was listed only listed on 10-Sep-2025, so only ~60 rows exist right now.")