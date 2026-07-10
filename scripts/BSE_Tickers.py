import requests
import pandas as pd
from datetime import datetime

# 1️⃣ Build URL for today's date
today = datetime.today().strftime("%Y%m%d")  # e.g., '20250801'
csv_filename = f"BhavCopy_BSE_CM_0_0_0_{today}_F_0000.csv"
url = f"https://www.bseindia.com/download/BhavCopy/Equity/{csv_filename}"

print(f"Downloading BSE Bhavcopy for {today} ...")
print(f"URL: {url}")

# 2️⃣ Download CSV
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Referer": "https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    with open(csv_filename, "wb") as f:
        f.write(response.content)
    print(f"✅ Downloaded {csv_filename}")
else:
    print(f"❌ Failed to download file. Status code: {response.status_code}")
    exit(1)

# 3️⃣ Read CSV
df = pd.read_csv(csv_filename)

print(f"Total Records: {len(df)}")

# 4️⃣ Separate Stocks and ETFs
# ETF is usually identified in SC_GROUP as 'ETF' or SC_TYPE as 'ETF'
etf_df = df[(df['SC_GROUP'].str.upper() == 'ETF') | (df['SC_TYPE'].str.upper() == 'ETF')]
stocks_df = df[~df.index.isin(etf_df.index)]  # everything else

print(f"ETFs found: {len(etf_df)}")
print(f"Stocks found: {len(stocks_df)}")

# 5️⃣ Save to CSV
etf_df.to_csv("bse_etfs.csv", index=False)
stocks_df.to_csv("bse_stocks.csv", index=False)

print("✅ Files saved: bse_etfs.csv, bse_stocks.csv")