import os
import datetime
from bhavcopy import bhavcopy

# ✅ Where to store data
data_storage = r"C:\Users\dipen\Downloads\Bhavcopy"
os.makedirs(data_storage, exist_ok=True)
os.chdir(data_storage)

# ✅ Config
MAX_DAYS_BACK = 7
WAIT_TIME = [1, 2]
CATEGORIES = ["indices", "equities", "derivatives"]
MIN_FILE_SIZE_KB = 10  # Treat files under this size as invalid

# ✅ Helper: Construct expected file path for given category and date
def expected_filename(category, date):
    day = date.strftime("%d")
    month = date.strftime("%b").upper()
    year = date.strftime("%Y")

    if category == "equities":
        return os.path.join(data_storage, f"cm{day}{month}{year}bhav.csv.zip")
    elif category == "derivatives":
        return os.path.join(data_storage, f"fo{day}{month}{year}bhav.csv.zip")
    elif category == "indices":
        return os.path.join(data_storage, f"indices_{date.strftime('%d%m%y')}.csv")
    else:
        return None

# ✅ Download with file size check
def try_download(category, target_date):
    print(f"\n📥 Downloading {category} bhavcopy for {target_date}")
    try:
        nse = bhavcopy(category, target_date, target_date, data_storage, WAIT_TIME)
        nse.get_data()

        # Validate file exists and size is sufficient
        filepath = expected_filename(category, target_date)
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return False

        size_kb = os.path.getsize(filepath) / 1024
        if size_kb < MIN_FILE_SIZE_KB:
            print(f"⚠️ File too small ({size_kb:.2f} KB) — treating as invalid.")
            return False

        print(f"✅ Valid {category} data ({size_kb:.2f} KB)")
        return True

    except Exception as e:
        if "404" in str(e):
            print(f"⚠️ 404 Not Found for {category} on {target_date}. Trying previous day...")
        else:
            print(f"❌ Failed to fetch {category} on {target_date}: {e}")
        return False

# ✅ Main function: go back in time and find valid day
def get_latest_available_data():
    today = datetime.date.today()
    for i in range(1, MAX_DAYS_BACK + 1):
        test_date = today - datetime.timedelta(days=i)
        if test_date.weekday() >= 5:  # Skip Sat/Sun
            continue

        try_download("indices", test_date)

        eq_success = try_download("equities", test_date)
        der_success = try_download("derivatives", test_date)

        if eq_success and der_success:
            print(f"\n✅ All valid data found for {test_date}")
            return

    print("\n⚠️ Could not find valid bhavcopy data in the last 7 days.")

# 🚀 Run
get_latest_available_data()
