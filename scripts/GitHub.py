from tabulate import tabulate
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from datetime import datetime
from email.message import EmailMessage
import tempfile
import shutil
import smtplib
import random
import os
import sys
import time

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15"
]

def fetch_ticker_data(base_url):
    temp_user_data_dir = tempfile.mkdtemp()
    edge_options = webdriver.EdgeOptions()
    edge_options.add_argument(f"user-data-dir={temp_user_data_dir}")
    edge_options.add_argument("--headless")
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    edge_options.add_argument("--window-size=1920,1080")
    edge_options.add_argument("--disable-extensions")
    edge_options.add_argument("--disable-logging")
    edge_options.add_argument("--disable-web-security")
    edge_options.add_argument("--ignore-certificate-errors")
    edge_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    edge_options.add_argument("--disable-blink-features=AutomationControlled")
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = None
    try:
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=edge_options)
        wait = WebDriverWait(driver, 60)
        tickers = []

        print("Loading main page...")
        driver.get(base_url)
        time.sleep(5)

        if "captcha" in driver.page_source.lower() or "Access Denied" in driver.title:
            print("Blocked by Finviz. Try rotating user-agent or running non-headless.")
            with open("page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return []

        try:
            page_info = wait.until(EC.presence_of_element_located((By.XPATH, '//select[@id="pageSelect"]/option[last()]')))
            total_pages = int(page_info.text.split("/")[-1].strip())
        except:
            print("Could not determine total pages. Defaulting to 1.")
            total_pages = 1

        for page_num in range(1, total_pages + 1):
            page_url = f"{base_url}&r={(page_num - 1) * 20 + 1}"
            print(f"Fetching page {page_num}/{total_pages}: {page_url}")
            driver.get(page_url)
            time.sleep(3)

            try:
                elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href*="quote.ashx?t="]')))
                tickers += [el.text for el in elements if el.text.strip()]
                print(f"Found {len(elements)} tickers on page {page_num}")
            except TimeoutException:
                print(f"No tickers found on page {page_num}, skipping.")

    except WebDriverException as e:
        print("WebDriver error:", e)
    except Exception as e:
        print("Unexpected error:", e)
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        shutil.rmtree(temp_user_data_dir, ignore_errors=True)

    return tickers

def send_sms(message_text):
    try:
        msg = EmailMessage()
        msg["Subject"] = "Finviz 52W Highs"
        msg["From"] = os.environ["EMAIL_USER"]
        msg["To"] = "3369424307@vtext.com"
        msg.set_content(message_text)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASS"])
            smtp.send_message(msg)
        print("SMS sent successfully.")
    except Exception as e:
        print(f"Failed to send SMS: {e}")

def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else input("Enter Finviz URL: ").strip()
    tickers = fetch_ticker_data(base_url)

    today_str = datetime.today().strftime('%Y-%m-%d')
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"finviz_{today_str}.txt")

    if not tickers:
        msg_text = f"📈 52-Week High Tickers — {today_str}\n\nNo tickers found for the given criteria."
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(msg_text)
        send_sms(msg_text)
        print("No tickers found. Saved empty result and sent SMS.")
        sys.exit(0)

    # Group tickers in 11-column rows
    table_data = [[tickers[i + j] for j in range(11) if i + j < len(tickers)] for i in range(0, len(tickers), 11)]
    headers = ["NO", "Ticker", "Company", "Sector", "Industry", "Country", "Market Cap", "P/E", "Price", "Change", "volume"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

    ticker_symbols = [row[1] for row in table_data if len(row) > 1]
    print("Ticker Symbols:")
    print(", ".join(ticker_symbols))

    msg_text = f"""📈 52-Week High Tickers — {today_str}

Ticker Symbols:
{', '.join(ticker_symbols)}

Total: {len(ticker_symbols)} tickers
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(msg_text)

    send_sms(msg_text)

if __name__ == "__main__":
    main()