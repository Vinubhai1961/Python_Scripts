from tabulate import tabulate
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
import os
import subprocess
import smtplib
from email.message import EmailMessage
import time

# ---------- Config ----------
edge_driver_path = r"C:\Program Files\Web_Drivers_selenium\edgedriver_win64\msedgedriver.exe"
github_repo_path = r"C:\Users\dipen\OneDrive\Documents\GitHub\Finviz"  # e.g., C:\Users\You\Documents\GitHub\Finviz
gmail_user = "dpatelj88@gmail.com"
gmail_app_password = "tixo ntnd ghzj zlmx"  # generated from Google App Passwords
spectrum_phone_number = "3369424307"
# ----------------------------

# Set up Edge driver
edge_service = Service(edge_driver_path)
edge_service.start()
driver = webdriver.Edge(service=edge_service)

# Finviz Screener URL
base_url = "https://finviz.com/screener.ashx?v=111&f=sh_avgvol_o1000%2Csh_price_o10%2Cta_highlow52w_nh&ft=4&o=-volume"
tickers = []

try:
    driver.get(base_url)
    page_info_element = driver.find_element(By.XPATH, '//select[@id="pageSelect"]/option[last()]')
    total_pages = int(page_info_element.text.split("/")[-1].strip())

    for page_num in range(1, total_pages + 1):
        print(f"Fetching Page {page_num}/{total_pages}")
        url = f"{base_url}&r={(page_num - 1) * 20 + 1}"
        driver.get(url)
        time.sleep(1)  # Pause between requests

        ticker_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="quote.ashx?t="]')
        tickers.extend([ticker.text for ticker in ticker_elements if ticker.text.strip()])

except NoSuchElementException as e:
    print("Error:", e)

finally:
    driver.quit()
    edge_service.stop()

# Build table
table_data = []
for i in range(0, len(tickers), 11):
    table_data.append([tickers[i + j] for j in range(11) if i + j < len(tickers)])

headers = ["NO", "Ticker", "Company", "Sector", "Industry", "Country", "Market Cap", "P/E", "Price", "Change", "volume"]
ticker_symbols = [row[1] for row in table_data if len(row) > 1]

# Save results
today = datetime.now().strftime('%Y-%m-%d')
file_name = f"finviz_{today}.txt"
results_dir = os.path.join(github_repo_path, "results")
os.makedirs(results_dir, exist_ok=True)
file_path = os.path.join(results_dir, file_name)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(f"Finviz Screener Results - {today}\n")
    f.write("=" * 40 + "\n\n")
    f.write("Screening Criteria:\n")
    f.write("- Price > $50\n")
    f.write("- Avg Volume > 1000\n")
    f.write("- ATR > 3\n")
    f.write("- New 52-week High\n")
    f.write("- Above 50-day SMA\n")
    f.write("- Above 200-day SMA\n\n")
    f.write("URL:\n")
    f.write(
        "https://finviz.com/screener.ashx?v=111&f=sh_avgvol_o1000,sh_price_o50,ta_averagetruerange_o3,ta_highlow52w_nh,ta_sma200_pa,ta_sma50_pa&ft=4&o=-volume\n")
    f.write("-" * 60 + "\n\n")

    f.write(tabulate(table_data, headers=headers, tablefmt="grid"))
    f.write("\n\nTicker Symbols:\n")
    f.write(", ".join(ticker_symbols))

# Git push
try:
    subprocess.run(["git", "add", file_path], cwd=github_repo_path)
    subprocess.run(["git", "commit", "-m", f"Add Finviz results for {today}"], cwd=github_repo_path)
    subprocess.run(["git", "push"], cwd=github_repo_path)
    print("GitHub update successful.")
except Exception as e:
    print("Git error:", e)

# Send SMS via Gmail (just tickers)
try:
    msg = EmailMessage()
    msg.set_content(", ".join(ticker_symbols))  # Only tickers in message
    msg["Subject"] = ""
    msg["From"] = gmail_user
    msg["To"] = f"{spectrum_phone_number}@vtext.com"

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_user, gmail_app_password)
        smtp.send_message(msg)

    print("Ticker SMS sent via Gmail.")
except Exception as e:
    print("Failed to send SMS:", e)