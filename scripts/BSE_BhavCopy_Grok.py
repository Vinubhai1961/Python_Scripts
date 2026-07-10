import requests
import pandas as pd
from datetime import datetime

# 1️⃣ Build URL for today's date
today = datetime.today().strftime("%Y%m%d")  # e.g., '20250804'
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
print("Available columns:", df.columns.tolist())

# 4️⃣ Save the entire DataFrame to CSV
output_filename = "bse_data.csv"
df.to_csv(output_filename, index=False)
print(f"✅ File saved: {output_filename}")