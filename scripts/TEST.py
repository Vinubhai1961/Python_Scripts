from tabulate import tabulate
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.common.exceptions import NoSuchElementException
import time
import shutil  # Optional for temp cleanup if you revert later

# Path to the EdgeDriver executable
edge_driver_path = r"C:\Program Files\Web_Drivers_selenium\edgedriver_win64\msedgedriver.exe"

# FIXED PERSISTENT PROFILE PATH - Replace with yours from Step 4 above
PERSISTENT_PROFILE_DIR = r"C:\Users\dipen\AppData\Local\Microsoft\Edge\User Data\SeleniumUBlock"

# Your uBlock path (for reference; flag ignored in 141, but harmless)
UBLOCK_PATH = r"C:\Users\dipen\OneDrive\Documents\GitHub\uBlock0.chromium"


# Function to fetch ticker data
def fetch_ticker_data(base_url):
    # Set up Edge options to use the PERSISTENT profile (uBlock loads on startup)
    edge_options = webdriver.EdgeOptions()
    edge_options.add_argument(f"--user-data-dir={PERSISTENT_PROFILE_DIR}")

    # Fallback: Your original load-extension (ignored in 141, but harmless)
    edge_options.add_argument(f"--load-extension={UBLOCK_PATH}")

    # Other original flags (from your command-line)
    edge_options.add_argument("--disable-background-networking")
    edge_options.add_argument("--disable-client-side-phishing-detection")
    # ... (add more if needed for your setup)

    # Setting up the EdgeDriver service
    edge_service = Service(edge_driver_path)
    edge_service.start()

    # Initialize the Edge WebDriver with the service and options
    driver = webdriver.Edge(service=edge_service, options=edge_options)

    # Initialize variables
    tickers = []

    try:
        # Open the base page to find the total number of pages
        driver.get(base_url)
        time.sleep(3)  # Brief wait for uBlock to settle

        # Find the element containing the page information
        page_info_element = driver.find_element(By.XPATH, '//select[@id="pageSelect"]/option[last()]')

        # Get the text containing page information
        page_info_text = page_info_element.text

        # Extract the total number of pages
        total_pages = int(page_info_text.split("/")[-1].strip())

        # Loop through each page dynamically
        for page_num in range(1, total_pages + 1):
            print(f"Fetching data from Page {page_num}/{total_pages}")

            # Generate URL for the current page
            url = f"{base_url}&r={(page_num - 1) * 20 + 1}"

            # Open the page
            driver.get(url)
            time.sleep(2)  # Allow blocking

            # Extract ticker symbols from the table
            ticker_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="quote.ashx?t="]')
            tickers.extend([ticker.text for ticker in ticker_elements if ticker.text.strip()])

    except NoSuchElementException as e:
        print("Error: ", e)

    finally:
        # Quit the driver when done
        driver.quit()
        edge_service.stop()

        # Optional: If you want temp cleanup (but skip for persistent)
        # shutil.rmtree(temp_user_data_dir)

    return tickers


# Prompt user for the base URL
base_url = input("Please enter the Finviz screener URL: ").strip()

# Fetch ticker data using the user-provided base URL
tickers = fetch_ticker_data(base_url)

# Create a list of lists containing the ticker data
table_data = []
for i in range(0, len(tickers), 11):
    table_data.append([tickers[i + j] for j in range(11) if i + j < len(tickers)])

# Add headers to the table
headers = ["NO", "Ticker", "Company", "Sector", "Industry", "Country", "Market Cap", "P/E", "Price", "Change", "volume"]

# Print the table
print(tabulate(table_data, headers=headers, tablefmt="grid"))

# Extract ticker symbols into another variable
ticker_symbols = []
for data in table_data:
    ticker_symbols.append(data[1])  # Ticker symbol is at index 1 in each row

# Print the extracted ticker symbols without square brackets
print("Ticker Symbols:")
print(", ".join(ticker_symbols))

# Clear variables
del tickers, table_data, ticker_symbols, base_url