from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from tabulate import tabulate
from datetime import datetime
import os
import subprocess
import smtplib
from email.message import EmailMessage
import time
import tempfile
import shutil
import re

# ---------- Config ----------
edge_driver_path = r"C:\Program Files\Web_Drivers_selenium\edgedriver_win64\msedgedriver.exe"
github_repo_path = r"C:\Users\dipen\OneDrive\Documents\GitHub\Finviz"
gmail_user = "dpatelj88@gmail.com"
gmail_app_password = "tixo ntnd ghzj zlmx"
spectrum_phone_number = "3369424307"
EXPECTED_TICKER_COUNT = 5  # Stop after finding 1 ticker
# ----------------------------

def setup_driver():
    temp_user_data_dir = tempfile.mkdtemp()
    options = Options()
    options.add_argument(f"user-data-dir={temp_user_data_dir}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    service = Service(edge_driver_path, log_path="edgedriver.log")
    return webdriver.Edge(service=service, options=options), temp_user_data_dir

def close_popup(driver):
    try:
        popup_close = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='close'], a[class*='close'], div[id*='modal'] button, div[class*='modal'] button"))
        )
        popup_close.click()
        print("✅ Popup ad closed.")
        time.sleep(0.5)
    except (NoSuchElementException, TimeoutException):
        print("ℹ️ No popup found.")

def parse_volume(volume_str):
    """Convert volume string (e.g., '4,046,780') to integer."""
    try:
        return int(volume_str.replace(",", ""))
    except (ValueError, AttributeError):
        return 0

def parse_price(price_str):
    """Convert price string (e.g., '164.33') to float."""
    try:
        return float(price_str)
    except (ValueError, AttributeError):
        return 0.0

def is_valid_row(row_data, screener_name, valid_tickers):
    """Validate row meets screener criteria."""
    if len(row_data) != 11:
        return False, f"Invalid column count: {len(row_data)}"
    ticker = row_data[1].strip()
    company = row_data[2].lower()
    industry = row_data[4].lower()
    volume = parse_volume(row_data[10])
    price = parse_price(row_data[8])
    # Check ticker format
    if not ticker or not ticker.isupper() or re.match(r'[\d.B]+', ticker):
        return False, f"Invalid ticker format: {ticker}"
    # Ensure ticker is in valid_tickers
    if valid_tickers and ticker not in valid_tickers:
        return False, f"Ticker not in valid list: {ticker}"
    # Exclude ETFs
    if "etf" in company or "etf" in industry or "exchange traded" in industry:
        return False, "Row is an ETF"
    # Check volume and price
    if volume < 1_000_000:
        return False, f"Volume too low: {volume}"
    if screener_name == "52wk-high" and price < 50:
        return False, f"Price too low for 52wk-high: {price}"
    if screener_name == "ATH" and price < 30:
        return False, f"Price too low for ATH: {price}"
    # Skip header rows
    if row_data[1].lower() in ["ticker", "no", "company"] or row_data[0].lower() == "no":
        return False, "Header row"
    return True, ""

def scrape_finviz(driver, url, screener_name):
    wait = WebDriverWait(driver, 20)
    tickers_info = []
    max_retries = 3
    xpath_attempts = [
        '//table[contains(@class, "table") or contains(@id, "screener")]//tr[td]',
        '//table[contains(@class, "screener")]//tr[td]',
        '//table//tr[td]'  # Broad fallback
    ]

    try:
        # Step 1: Set light mode and load page
        driver.get("https://finviz.com")
        driver.add_cookie({"name": "theme", "value": "light", "domain": "finviz.com"})
        driver.get(url)
        print(f"ℹ️ Loaded URL: {url}")

        # Step 2: Close ad popup if present
        close_popup(driver)

        # Step 3: Get total number of pages
        try:
            page_info = wait.until(
                EC.presence_of_element_located((By.XPATH, '//select[@id="pageSelect"]/option[last()]'))
            )
            total_pages = int(page_info.text.split("/")[-1].strip())
            print(f"ℹ️ Total pages: {total_pages}")
        except (NoSuchElementException, TimeoutException):
            print(f"⚠️ Could not find page selector for {screener_name}. Assuming 1 page.")
            total_pages = 1

        # Step 4: Loop through pages
        for page_num in range(1, total_pages + 1):
            print(f"Fetching Page {page_num}/{total_pages} for {screener_name}")
            page_url = f"{url}&r={(page_num - 1) * 20 + 1}"
            driver.get(page_url)

            # Get valid tickers from CSS selector for validation
            try:
                ticker_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="quote.ashx?t="]')
                valid_tickers = set([ticker.text.strip() for ticker in ticker_elements if ticker.text.strip() and ticker.text.isupper() and not re.match(r'[\d.B]+', ticker.text.strip())])
                print(f"ℹ️ Valid tickers from CSS selector: {valid_tickers}")
            except Exception as e:
                print(f"⚠️ Error getting valid tickers: {str(e)}")
                valid_tickers = set()

            # Try table scraping with multiple XPath attempts
            rows = None
            for attempt, xpath in enumerate(xpath_attempts, 1):
                for retry in range(max_retries):
                    try:
                        print(f"ℹ️ Trying XPath {attempt}/{len(xpath_attempts)}: {xpath}, retry {retry + 1}/{max_retries}")
                        wait.until(
                            EC.visibility_of_element_located((By.XPATH, xpath))
                        )
                        table = driver.find_element(By.XPATH, xpath + "/ancestor::table")
                        table_class = table.get_attribute("class") or table.get_attribute("id") or "unknown"
                        print(f"ℹ️ Table found with class/ID: {table_class}")
                        rows = driver.find_elements(By.XPATH, xpath)
                        break
                    except (TimeoutException, NoSuchElementException):
                        print(f"❌ Timeout or no element for XPath {attempt}, retry {retry + 1}/{max_retries}")
                        if retry == max_retries - 1:
                            break
                        time.sleep(2)
                if rows:
                    break

            if not rows:
                print(f"❌ All XPath attempts failed, falling back to CSS selector")
                try:
                    tickers = list(valid_tickers)[:EXPECTED_TICKER_COUNT]
                    print(f"ℹ️ Fallback: Using {len(tickers)} tickers: {tickers}")
                    for ticker in tickers:
                        try:
                            # Try to find the row for the ticker
                            row = driver.find_element(By.XPATH, f'//tr[td/a[contains(@href, "quote.ashx?t={ticker}")]]')
                            cols = row.find_elements(By.TAG_NAME, "td")
                            row_data = [col.text.strip() for col in cols]
                            if len(row_data) == 11:
                                is_valid, reason = is_valid_row(row_data, screener_name, valid_tickers)
                                if is_valid:
                                    tickers_info.append(row_data)
                                    print(f"✅ Fallback row: {row_data}")
                                else:
                                    print(f"⚠️ Fallback row invalid: {reason} - {row_data}")
                            else:
                                print(f"⚠️ Fallback row has {len(row_data)} columns: {row_data}")
                        except NoSuchElementException:
                            print(f"⚠️ Could not find row for ticker {ticker}, using placeholder")
                            tickers_info.append([str(len(tickers_info) + 1), ticker] + [""] * 9)
                        if len(tickers_info) >= EXPECTED_TICKER_COUNT:
                            return tickers_info
                except Exception as e:
                    print(f"❌ Fallback error on page {page_num}: {str(e)}")
                return tickers_info

            # Process table rows
            print(f"ℹ️ Found {len(rows)} rows on page {page_num}")
            for row in rows:
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    row_data = [col.text.strip() for col in cols]
                    print(f"ℹ️ Raw row: {row_data}")
                    is_valid, reason = is_valid_row(row_data, screener_name, valid_tickers)
                    if is_valid:
                        tickers_info.append(row_data)
                        print(f"✅ Valid row: {row_data}")
                    else:
                        print(f"⚠️ Skipping row: {reason} - {row_data}")
                    if len(tickers_info) >= EXPECTED_TICKER_COUNT:
                        print(f"ℹ️ Stopping after finding {EXPECTED_TICKER_COUNT} ticker(s)")
                        return tickers_info
                except Exception as e:
                    print(f"⚠️ Error processing row: {str(e)}")

            # Check for no-results message
            try:
                no_results = driver.find_element(By.XPATH, '//b[contains(text(), "No stocks found")]')
                print(f"⚠️ No stocks found for {screener_name} on page {page_num}")
                continue
            except NoSuchElementException:
                pass

            time.sleep(1)

    except Exception as e:
        print(f"❌ Error during scraping {screener_name}: {str(e)}")
        import traceback
        traceback.print_exc()

    return tickers_info

def save_results(name_prefix, data, screener_name, url):
    headers = ["No", "Ticker", "Company", "Sector", "Industry", "Country", "Market Cap", "P/E", "Price", "Change", "Volume"]
    today = datetime.now().strftime('%Y-%m-%d')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    filename = f"{name_prefix}_{today}.txt"
    subfolder = "52WK-High" if screener_name == "52wk-high" else "ATH"
    results_dir = os.path.join(github_repo_path, "results", subfolder)
    os.makedirs(results_dir, exist_ok=True)
    filepath = os.path.join(results_dir, filename)

    description = f"""Finviz Stock Screener Results
Scan Name: {screener_name}
Date and Time: {timestamp}
URL: {url}
Scan Details:
"""
    if screener_name == "52wk-high":
        description += """- Average Volume: Over 1,000,000
- Price: Over $50
- Average True Range: Over 3
- 52-Week High: New High
- 200-Day SMA: Price Above
- 50-Day SMA: Price Above
- Sort: By Volume (Descending)
"""
    else:  # ATH
        description += """- Average Volume: Over 1,000,000
- Price: Over $30
- All-Time High: New High
- Average True Range: Over 3
- 200-Day SMA: Price Above
- 50-Day SMA: Price Above
- Sort: By Volume (Descending)
"""
    description += "\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(description)
        if not data:
            print(f"⚠️ No data to save for {filename}")
            f.write(f"No tickers found for {screener_name}.\n")
        else:
            f.write(tabulate(data, headers=headers, tablefmt="grid"))
            f.write("\n\nTicker Symbols:\n")
            tickers = [row[1] for row in data if len(row) > 1 and row[1].strip() and row[1].isupper() and not re.match(r'[\d.B]+', row[1])]
            f.write(", ".join(tickers) if tickers else "No tickers found.")
            f.write(f"\nTotal Tickers: {len(tickers)}\n")

    return filepath, filename

def push_to_github(filepath, filename):
    try:
        add_result = subprocess.run(["git", "add", filepath], cwd=github_repo_path, capture_output=True, text=True, check=True)
        print(f"ℹ️ Git add output: {add_result.stdout}")

        status_result = subprocess.run(["git", "status", "--porcelain"], cwd=github_repo_path, capture_output=True, text=True, check=True)
        if not status_result.stdout.strip():
            print("ℹ️ No changes to commit for GitHub.")
            return

        commit_result = subprocess.run(
            ["git", "commit", "-m", f"Add Finviz results for {datetime.now().strftime('%Y-%m-%d')}"],
            cwd=github_repo_path,
            capture_output=True,
            text=True,
            check=False
        )
        if commit_result.returncode != 0:
            print(f"ℹ️ Git commit skipped: {commit_result.stderr}")
            return

        subprocess.run(["git", "push"], cwd=github_repo_path, check=True)
        print("✅ GitHub update successful.")
    except subprocess.CalledProcessError as e:
        print(f"❌ GitHub push error: {e.stderr}")

def send_sms(message):
    try:
        msg = EmailMessage()
        msg.set_content(message)
        msg["Subject"] = ""
        msg["From"] = gmail_user
        msg["To"] = f"{spectrum_phone_number}@vtext.com"

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(gmail_user, gmail_app_password)
            smtp.send_message(msg)

        print("✅ SMS sent.")
    except Exception as e:
        print(f"❌ SMS failed: {e}")

# --- URLs for screener types ---
finviz_52wk_high_url = "https://finviz.com/screener.ashx?v=111&f=sh_avgvol_o1000,sh_price_o50,ta_averagetruerange_o3,ta_highlow52w_nh,ta_sma200_pa,ta_sma50_pa&ft=4&o=-volume"
finviz_ath_url = "https://finviz.com/screener.ashx?v=111&f=sh_avgvol_o1000,sh_price_o30,ta_alltime_nh,ta_sma200_pa,ta_sma50_pa&ft=4&o=-volume"

# --- Run scraper and save results ---
driver, temp_user_data_dir = setup_driver()
try:
    # Scrape 52-week high
    data_52wk = scrape_finviz(driver, finviz_52wk_high_url, "52wk-high")
    print(f"ℹ️ 52wk-high: Found {len(data_52wk)} tickers: {[row[1] for row in data_52wk if len(row) > 1]}")
    path_52wk, file_52wk = save_results("finviz_52wk", data_52wk, "52wk-high", finviz_52wk_high_url)
    push_to_github(path_52wk, file_52wk)
    send_sms(f"✅ 52WK-high ticker scan complete.\nGitHub updated with: {file_52wk}")

    # Scrape ATH
    data_ath = scrape_finviz(driver, finviz_ath_url, "ATH")
    print(f"ℹ️ ATH: Found {len(data_ath)} tickers: {[row[1] for row in data_ath if len(row) > 1]}")
    path_ath, file_ath = save_results("finviz_ath", data_ath, "ATH", finviz_ath_url)
    push_to_github(path_ath, file_ath)
    send_sms(f"✅ ATH ticker scan complete.\nGitHub updated with: {file_ath}")

finally:
    driver.quit()
    shutil.rmtree(temp_user_data_dir)