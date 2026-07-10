from tabulate import tabulate
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
import tempfile, shutil, time

# Path to your EdgeDriver
edge_driver_path = r"C:\Program Files\Web_Drivers_selenium\edgedriver_win64\msedgedriver.exe"

def fetch_screener_and_details(base_url):
    temp_user_data_dir = tempfile.mkdtemp()
    edge_options = webdriver.EdgeOptions()
    edge_options.add_argument(f"user-data-dir={temp_user_data_dir}")
    service = Service(edge_driver_path)
    driver = webdriver.Edge(service=service, options=edge_options)

    all_data = []
    try:
        # Step 1: Go to base screener page
        driver.get(base_url)
        time.sleep(2)

        # Get number of pages
        pages = driver.find_elements(By.XPATH, '//select[@id="pageSelect"]/option')
        total_pages = len(pages)

        for page_num in range(1, total_pages + 1):
            url = f"{base_url}&r={(page_num - 1) * 20 + 1}"
            driver.get(url)
            time.sleep(2)

            # Get tickers on this page
            ticker_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="quote.ashx?t="]')
            tickers = [el.text for el in ticker_elements if el.text.strip()]

            # For each ticker, fetch detail stats
            for ticker in tickers:
                detail_url = f"https://finviz.com/quote.ashx?t={ticker}"
                driver.get(detail_url)
                time.sleep(1)

                # Scrape snapshot table
                snapshot_rows = driver.find_elements(By.CSS_SELECTOR, "table.snapshot-table2 tr")
                stats = {}
                for row in snapshot_rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    for i in range(0, len(cells), 2):
                        key = cells[i].text.strip()
                        val = cells[i+1].text.strip()
                        stats[key] = val

                # Pick fields we want
                row_data = [
                    ticker,
                    stats.get("Company", ""),
                    stats.get("Country", ""),
                    stats.get("Industry", ""),
                    stats.get("Market Cap", ""),
                    stats.get("P/E", ""),
                    stats.get("Price", ""),
                    stats.get("Volume", ""),
                    stats.get("Perf Week", ""),
                    stats.get("Perf Month", ""),
                    stats.get("Perf Quarter", ""),
                    stats.get("Perf Year", ""),
                    stats.get("Perf YTD", ""),
                    stats.get("ATR", ""),
                    stats.get("Volatility W", ""),
                    stats.get("Volatility M", ""),
                    stats.get("SMA20", ""),
                    stats.get("SMA50", ""),
                    stats.get("SMA200", ""),
                    stats.get("RSI (14)", ""),
                    stats.get("Rel Volume", ""),
                    stats.get("Short Float", ""),
                    stats.get("52W High", ""),
                    stats.get("52W Low", "")
                ]

                all_data.append(row_data)

    finally:
        driver.quit()
        shutil.rmtree(temp_user_data_dir)

    return all_data

# Example usage
base_url = "https://finviz.com/screener.ashx?v=350&f=sh_price_o30,sh_relvol_o3,ta_averagetruerange_o2,ta_sma200_pa&ft=4&o=-volume"
data = fetch_screener_and_details(base_url)

headers = ["Ticker", "Company", "Country", "Industry", "Market Cap", "P/E", "Price", "Volume",
           "Perf Week", "Perf Month", "Perf Quarter", "Perf Year", "Perf YTD",
           "ATR", "Volatility W", "Volatility M", "SMA20", "SMA50", "SMA200",
           "RSI(14)", "Rel Volume", "Short Float", "52W High", "52W Low"]

print(tabulate(data, headers=headers, tablefmt="grid"))