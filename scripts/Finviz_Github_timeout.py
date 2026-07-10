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
        "url": "https://finviz.com/screener.ashx?v=111&f=sh_avgvol_o1000,sh_curvol_o1000,sh_price_o50,ta_averagetruerange_o3,ta_highlow52w_nh,ta_sma200_pa,ta_sma50_pa&ft=4&o=-volume",
        "criteria": "- Avg Volume > 1M\n- Current Volume > 1M\n- Price > $50\n- ATR > 3\n- 52-Week High\n- Above 50/200 SMA"
    },
    "ATH": {
        "url": "https://finviz.com/screener.ashx?v=111&f=sh_avgvol_o1000,sh_curvol_o1000,sh_price_o30,ta_alltime_nh,ta_sma200_pa,ta_sma50_pa&ft=4&o=-volume",
        "criteria": "- Avg Volume > 1M\n- Current Volume > 1M\n- Price > $30\n- All-Time High\n- Above 50/200 SMA"
    },
    "52wk10retrace": {
        "url": "https://finviz.com/screener.ashx?v=111&f=sh_avgvol_o1000,sh_curvol_o1000,sh_price_o50,ta_averagetruerange_o3,ta_highlow52w_b0to10h,ta_sma20_pa,ta_sma200_pa,ta_sma50_pa&ft=4&o=-volume",
        "criteria": "- Avg Volume > 1M\n- Current Volume > 1M\n- Price > $50\n- ATR > 3\n- Recent Pullback (0-10% Below 52-Week High)\n- Above 20/50/200 SMA"
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
    driver = webdriver.Edge(service=service)
    driver.set_page_load_timeout(30)  # Set 30-second page load timeout
    return driver

def scrape_finviz(driver, url, screener_name):
    logging.info(f"Starting scrape for {screener_name}")
    tickers_info = []
    wait = WebDriverWait(driver, 10)

    try:
        for attempt in range(3):
            try:
                driver.get(url)
                page_info = wait.until(EC.presence_of_element_located((By.XPATH, '//select[@id="pageSelect"]/option[last()]')))
                total_pages = int(page_info.text.split("/")[-1].strip())
                logging.info(f"Total pages for {screener_name}: {total_pages}")
                break
            except Exception as e:
                logging.warning(f"Failed to load {url} for {screener_name}, attempt {attempt + 1}/3: {str(e)}")
                time.sleep(3)
        else:
            logging.error(f"Could not determine total pages for {screener_name} after 3 attempts")
            total_pages = 1

        for page_num in range(1, total_pages + 1):
            logging.info(f"Fetching Page {page_num}/{total_pages} for {screener_name}")
            page_url = f"{url}&r={(page_num - 1) * 20 + 1}"
            for attempt in range(3):
                try:
                    driver.get(page_url)
                    wait.until(EC.presence_of_all_elements_located((By.XPATH, '//table[@id="screener-content"]//tr[td]')))
                    time.sleep(3)  # Increased delay for page load
                    rows = driver.find_elements(By.XPATH, '//table[@id="screener-content"]//tr[td]')
                    page_tickers = []
                    for row in rows:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        row_data = [col.text.strip() for col in cols]
                        if len(row_data) == 11 and row_data[1].isupper() and row_data[1].lower() not in ["ticker", "no"]:
                            page_tickers.append(row_data)
                    expected_tickers = 20 if page_num < total_pages else (total_pages * 20 - len(tickers_info))
                    logging.info(f"Page {page_num}/{total_pages} for {screener_name}: {len(page_tickers)} tickers (expected ~{expected_tickers})")
                    if len(page_tickers) < expected_tickers - 5:
                        logging.warning(f"Low ticker count on page {page_num} for {screener_name}")
                    tickers_info.extend(page_tickers)
                    break
                except Exception as e:
                    logging.warning(f"Failed to scrape page {page_url} for {screener_name}, attempt {attempt + 1}/3: {str(e)}")
                    time.sleep(3)
            else:
                logging.error(f"Failed to scrape page {page_num} for {screener_name} after 3 attempts")
    except Exception as e:
        logging.error(f"Unexpected error in scrape_finviz for {screener_name}: {str(e)}")
    logging.info(f"Total tickers for {screener_name}: {len(tickers_info)}")
    return tickers_info

def save_results(data, screener_name, url, criteria):
    headers = ["No", "Ticker", "Company", "Sector", "Industry", "Country", "Market Cap", "P/E", "Price", "Change", "Volume"]
    today = datetime.now().strftime('%Y-%m-%d')
    filename = f"finviz_{screener_name}_{today}.txt"
    if screener_name == "52wk-high":
        subfolder = "52WK-High"
    elif screener_name == "ATH":
        subfolder = "ATH"
    else:
        subfolder = "52Wk10Retrace"
    results_dir = os.path.join(github_repo_path, "Results", subfolder)
    os.makedirs(results_dir, exist_ok=True)
    filepath = os.path.join(results_dir, filename)

    try:
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
        logging.info(f"Saved results to {filepath}")
    except Exception as e:
        logging.error(f"Failed to save results for {screener_name}: {str(e)}")
        return None
    return filepath

def push_to_github(filepath):
    try:
        subprocess.run(["git", "add", filepath], cwd=github_repo_path, check=True)
        result = subprocess.run(
            ["git", "commit", "-m", f"Add Finviz results for {datetime.now().strftime('%Y-%m-%d')}"],
            cwd=github_repo_path,
            capture_output=True,
            text=True
        )
        if "nothing to commit" in result.stdout:
            logging.info(f"No changes to commit for {filepath}")
            return
        subprocess.run(["git", "push"], cwd=github_repo_path, check=True)
        logging.info(f"GitHub push successful for {filepath}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Git operation failed: {e.stderr}")

def send_sms(tickers_52wk, tickers_ath, tickers_52wk10retrace):
    global sms_sent  # Track if SMS was sent in this run
    if 'sms_sent' in globals() and sms_sent:
        logging.info("SMS already sent in this run, skipping")
        return
    message = (
        f"52WK-high: {', '.join(tickers_52wk)}\n"
        f"ATH: {', '.join(tickers_ath)}\n"
        f"52Wk10Retrace: {', '.join(tickers_52wk10retrace)}"
    )
    try:
        logging.info(f"Attempting to send SMS: {message}")
        msg = EmailMessage()
        msg.set_content(message)
        msg["Subject"] = ""
        msg["From"] = gmail_user
        msg["To"] = f"{spectrum_phone_number}@vtext.com"
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(gmail_user, gmail_app_password)
            smtp.send_message(msg)
        logging.info("SMS sent successfully")
        sms_sent = True  # Mark SMS as sent
    except Exception as e:
        logging.error(f"Failed to send SMS: {str(e)}")

# ---------- Main ----------
sms_sent = False  # Initialize SMS sent flag
driver = setup_driver()
try:
    results = {}
    for screener_name, config in SCREENERS.items():
        try:
            data = scrape_finviz(driver, config["url"], screener_name)
            results[screener_name] = data
            filepath = save_results(data, screener_name, config["url"], config["criteria"])
            if filepath:
                push_to_github(filepath)
        except Exception as e:
            logging.error(f"Error processing {screener_name}: {str(e)}")
            continue

    tickers_52wk = [row[1] for row in results.get("52wk-high", [])]
    tickers_ath = [row[1] for row in results.get("ATH", [])]
    tickers_52wk10retrace = [row[1] for row in results.get("52wk10retrace", [])]
    send_sms(tickers_52wk, tickers_ath, tickers_52wk10retrace)

finally:
    driver.quit()