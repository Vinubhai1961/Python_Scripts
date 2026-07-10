from tabulate import tabulate
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.common.exceptions import NoSuchElementException
import tempfile
import shutil

# Path to the EdgeDriver executable
edge_driver_path = r"C:\Program Files\Web_Drivers_selenium\edgedriver_win64\msedgedriver.exe"

# Function to fetch ticker data
def fetch_ticker_data(base_url):
    # Create a temporary directory for the Edge user data
    temp_user_data_dir = tempfile.mkdtemp()

    # Set up Edge options to use the temporary user data directory
    edge_options = webdriver.EdgeOptions()
    edge_options.add_argument(f"user-data-dir={temp_user_data_dir}")

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

            # Extract ticker symbols from the table
            ticker_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="quote.ashx?t="]')
            tickers.extend([ticker.text for ticker in ticker_elements if ticker.text.strip()])

    except NoSuchElementException as e:
        # NoSuchElementException will be raised when no more pages are available
        print("Error: ", e)

    finally:
        # Stop the service and quit the driver when done
        driver.quit()
        edge_service.stop()

        # Delete the temporary user data directory
        shutil.rmtree(temp_user_data_dir)

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
