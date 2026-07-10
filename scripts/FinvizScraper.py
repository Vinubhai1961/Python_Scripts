from tabulate import tabulate
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.common.exceptions import NoSuchElementException

# Path to the EdgeDriver executable
edge_driver_path = r"C:\Program Files\Web_Drivers_selenium\edgedriver_win64\msedgedriver.exe"

# Setting up the EdgeDriver service
edge_service = Service(edge_driver_path)
edge_service.start()

# Initialize the Edge WebDriver with the service
driver = webdriver.Edge(service=edge_service)

# Base URL of the Finviz screener
base_url = "https://finviz.com/screener.ashx?v=111&f=fa_fpe_u30%2Csh_price_o40%2Cta_highlow52w_nh&ft=4&o=-volume"

# Initialize variables
tickers = []

try:
    # Open the page
    driver.get(base_url)

    # Find the element containing page information
    page_info_element = driver.find_element(By.XPATH, '//select[@id="pageSelect"]/option[last()]')

    # Get the text containing page information
    page_info_text = page_info_element.text

    # Extract the total number of pages
    total_pages = int(page_info_text.split("/")[-1].strip())

    # Loop through pages dynamically
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
    edge_service.stop()
    driver.quit()

# Create a list of lists containing the ticker data
table_data = []
for i in range(0, len(tickers), 11):
    table_data.append([tickers[i+j] for j in range(11)])

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
