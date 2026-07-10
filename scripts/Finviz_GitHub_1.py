from tabulate import tabulate
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
import os
import subprocess
import smtplib
from email.message import EmailMessage
import time

# ---------- Config ----------
edge_driver_path = r"C:\Program Files\Web_Drivers_selenium\edgedriver_win64\msedgedriver.exe"
github_repo_path = r"C:\Users\dipen\OneDrive\Documents\GitHub\Finviz"
gmail_user = "dpatelj88@gmail.com"
gmail_app_password = "tixo ntnd ghzj zlmx"
spectrum_phone_number = "3369424307"


# ----------------------------
def scrape_finviz(url):
    tickers_info = []
    edge_service = Service(edge_driver_path)
    edge_service.start()
    driver = webdriver.Edge(service=edge_service)

    try:
        driver.get(url)
        time.sleep(3)  # Allow page to load

        # --- Force Light Mode using JS (ignores browser cookie) ---
        try:
            driver.execute_script("""
                localStorage.setItem('finviz-theme', 'light');
                location.reload();
            """)
            time.sleep(3)  # Wait for reload
        except Exception as e:
            print("Failed to set light mode via JS:", e)

        # --- Determine total pages ---
        try:
            page_info_element = driver.find_element(By.XPATH, '//select[@id="pageSelect"]/option[last()]')
            total_pages = int(page_info_element.text.split("/")[-1].strip())
        except NoSuchElementException:
            total_pages = 1

        for page_num in range(1, total_pages + 1):
            print(f"Fetching Page {page_num}/{total_pages}")
            page_url = f"{url}&r={(page_num - 1) * 20 + 1}"
            driver.get(page_url)
            time.sleep(2)

            rows = driver.find_elements(
                By.XPATH,
                '//table[contains(@class,"table-light")]//tr[contains(@class,"table-dark-row-cp") or contains(@class,"table-light-row-cp")]'
            )

            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 11:
                    tickers_info.append([col.text.strip() for col in cols[:11]])

    except NoSuchElementException as e:
        print("Error:", e)
    finally:
        driver.quit()
        edge_service.stop()

    return tickers_info


def save_results(folder, prefix, url, data_rows):
    today = datetime.now().strftime('%Y-%m-%d')
    dir_path = os.path.join(github_repo_path, folder)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, f"finviz_{prefix}_{today}.txt")

    headers = [
        "NO", "Ticker", "Company", "Sector", "Industry", "Country",
        "Market Cap", "P/E", "Price", "Change", "volume"
    ]
    ticker_symbols = [row[1] for row in data_rows if len(row) > 1]

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"Finviz Screener Results - {today}\n")
        f.write("=" * 40 + "\n\n")

        if prefix == "52WK":
            f.write("Screening Criteria:\n")
            f.write("- Price > $50\n")
            f.write("- Avg Volume > 1000\n")
            f.write("- ATR > 3\n")
            f.write("- New 52-week High\n")
            f.write("- Above 50-day SMA\n")
            f.write("- Above 200-day SMA\n\n")
        elif prefix == "ATH":
            f.write("Screening Criteria:\n")
            f.write("- Price > $30\n")
            f.write("- Avg Volume > 1000\n")
            f.write("- ATR > 3\n")
            f.write("- New All-Time High\n")
            f.write("- Above 50-day SMA\n")
            f.write("- Above 200-day SMA\n\n")

        f.write(f"URL:\n{url}\n")
        f.write("-" * 60 + "\n\n")

        if data_rows:
            f.write(tabulate(data_rows, headers=headers, tablefmt="grid"))
            f.write("\n\nTicker Symbols:\n")
            f.write(", ".join(ticker_symbols))
        else:
            f.write(f"No {'ATH' if prefix == 'ATH' else '52-week high'} tickers found today.")

    return file_path, ticker_symbols


def send_sms(tickers, tag):
    msg = EmailMessage()
    msg.set_content(", ".join(tickers) if tickers else f"No {tag} tickers found today.")
    msg["Subject"] = ""
    msg["From"] = gmail_user
    msg["To"] = f"{spectrum_phone_number}@vtext.com"
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_user, gmail_app_password)
        smtp.send_message(msg)
    print(f"{tag} ticker SMS sent.")


# Screener URLs
url_52wk = "https://finviz.com/screener.ashx?v=111&f=sh_avgvol_o1000,sh_price_o50,ta_averagetruerange_o3,ta_highlow52w_nh,ta_sma200_pa,ta_sma50_pa&ft=4&o=-volume"
url_ath = "https://finviz.com/screener.ashx?v=111&f=sh_avgvol_o1000,sh_price_o30,ta_alltime_nh,ta_averagetruerange_o3,ta_sma200_pa,ta_sma50_pa&ft=4&o=-volume"

# Scrape data
data_52wk = scrape_finviz(url_52wk)
data_ath = scrape_finviz(url_ath)

# Save files
file_52wk, symbols_52wk = save_results("52WK-high", "52WK", url_52wk, data_52wk)
file_ath, symbols_ath = save_results("ATH", "ATH", url_ath, data_ath)

# GitHub push
try:
    subprocess.run(["git", "add", file_52wk, file_ath], cwd=github_repo_path)
    subprocess.run([
        "git", "commit", "-m",
        f"Add Finviz results for {datetime.now().strftime('%Y-%m-%d')}",
        "--allow-empty"
    ], cwd=github_repo_path)
    subprocess.run(["git", "push"], cwd=github_repo_path)
    print("GitHub update successful.")
except Exception as e:
    print("Git error:", e)

# Send SMS
try:
    send_sms(symbols_52wk, "52WK-high")
    send_sms(symbols_ath, "ATH")
except Exception as e:
    print("Failed to send SMS:", e)
