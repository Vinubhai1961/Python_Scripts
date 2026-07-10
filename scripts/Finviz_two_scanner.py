from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tabulate import tabulate
from datetime import datetime
import os
import subprocess
import smtplib
from email.message import EmailMessage
import time
import logging

# ---------- Config ----------
edge_driver_path = r"C:\Program Files\Web_Drivers_selenium\edgedriver_win64\msedgedriver.exe"
github_repo_path = r"C:\Users\dipen\OneDrive\Documents\GitHub\Finviz"
gmail_user = "dpatelj88@gmail.com"
gmail_app_password = "tixo ntnd ghzj zlmx"
spectrum_phone_number = "3369424307"
SCREENERS = {
    "52wk-high": {
        "url": "https://finviz.com/screener.ashx?v=111&f=sh_avgvol_o1000,sh_price_o50,ta_averagetruerange_o3,ta_highlow52w_nh,ta_sma200_pa,ta_sma50_pa&ft=4&o=-volume",
        "criteria": "- Avg Volume > 1M\n- Price > $50\n- ATR > 3\n- 52-Week High\n- Above 50/200 SMA"
    },
    "ATH": {
        "url": "https://finviz.com/screener.ashx?v=111&f=sh_avgvol_o1000,sh_price_o30,ta_alltime_nh,ta_sma200_pa,ta_sma50_pa&ft=4&o=-volume",
        "criteria": "- Avg Volume > 1M\n- Price > $30\n- All-Time High\n- ATR > 3\n- Above 50/200 SMA"
    }
}
# Set up logging to save to logs folder
log_dir = r"C:\Users\dipen\OneDrive\Documents\GitHub\logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, 'finviz_scraper.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ---------- Functions ----------
def setup_driver():
    service = Service(edge_driver_path)
    return webdriver.Edge(service=service)

def scrape_finviz(driver, url, screener_name):
    logging.info(f"Starting scrape for {screener_name}")
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    tickers_info = []

    try:
        page_info = wait.until(EC.presence_of_element_located((By.XPATH, '//select[@id="pageSelect"]/option[last()]')))
        total_pages = int(page_info.text.split("/")[-1].strip())
    except:
        total_pages = 1

    for page_num in range(1, total_pages + 1):
        logging.info(f"Fetching Page {page_num}/{total_pages} for {screener_name}")
        page_url = f"{url}&r={(page_num - 1) * 20 + 1}"
        driver.get(page_url)
        time.sleep(1)

        rows = driver.find_elements(By.XPATH, '//table[contains(@class, "table")]//tr[td]')
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            row_data = [col.text.strip() for col in cols]
            if len(row_data) == 11 and row_data[1].isupper() and row_data[1].lower() not in ["ticker", "no"]:
                tickers_info.append(row_data)

    return tickers_info

def save_results(data, screener_name, url, criteria):
    headers = ["No", "Ticker", "Company", "Sector", "Industry", "Country", "Market Cap", "P/E", "Price", "Change", "Volume"]
    today = datetime.now().strftime('%Y-%m-%d')
    filename = f"finviz_{screener_name}_{today}.txt"
    subfolder = "52WK-High" if screener_name == "52wk-high" else "ATH"
    results_dir = os.path.join(github_repo_path, "Results", subfolder)
    os.makedirs(results_dir, exist_ok=True)
    filepath = os.path.join(results_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Finviz Screener Results - {screener_name} - {today}\n")
        f.write("=" * 40 + "\n\n")
        f.write("Screening Criteria:\n")
        f.write(criteria + "\n\n")
        f.write("URL:\n")
        f.write(url + "\n")
        f.write("-" * 60 + "\n\n")
        if data:
            f.write(tabulate(data, headers=headers, tablefmt="grid"))
            f.write("\n\nTicker Symbols:\n")
            tickers = [row[1] for row in data]
            f.write(", ".join(tickers))
        else:
            f.write("No tickers found.\n")

    return filepath

def push_to_github(filepath):
    subprocess.run(["git", "add", filepath], cwd=github_repo_path)
    result = subprocess.run(
        ["git", "commit", "-m", f"Add Finviz results for {datetime.now().strftime('%Y-%m-%d')}"],
        cwd=github_repo_path,
        capture_output=True,
        text=True
    )
    if "nothing to commit" in result.stdout:
        logging.info("No changes to commit.")
        return
    subprocess.run(["git", "push"], cwd=github_repo_path)
    logging.info("GitHub update successful.")

def send_sms(tickers_52wk, tickers_ath):
    message = f"52WK-high: {', '.join(tickers_52wk)}\nATH: {', '.join(tickers_ath)}"
    msg = EmailMessage()
    msg.set_content(message)
    msg["Subject"] = ""
    msg["From"] = gmail_user
    msg["To"] = f"{spectrum_phone_number}@vtext.com"
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_user, gmail_app_password)
        smtp.send_message(msg)
    logging.info("SMS sent.")

# ---------- Main ----------
driver = setup_driver()
try:
    results = {}
    for screener_name, config in SCREENERS.items():
        data = scrape_finviz(driver, config["url"], screener_name)
        results[screener_name] = data
        filepath = save_results(data, screener_name, config["url"], config["criteria"])
        push_to_github(filepath)

    tickers_52wk = [row[1] for row in results.get("52wk-high", [])]
    tickers_ath = [row[1] for row in results.get("ATH", [])]
    send_sms(tickers_52wk, tickers_ath)

finally:
    driver.quit()