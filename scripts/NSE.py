import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL of the NSE India page for Wipro
url = "https://www.nseindia.com/get-quotes/equity?symbol=WIPRO"

# Headers for the HTTP request to avoid getting blocked
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

# Make the HTTP request
response = requests.get(url, headers=headers)
response.raise_for_status()  # Ensure the request was successful

# Parse the HTML content
soup = BeautifulSoup(response.text, 'html.parser')

# Find the element containing the "% of Deliverable / Traded Quantity"
perc_deliverable_tag = soup.find(id="percOfDeliverable_TradedQty")

# Extract the text
perc_deliverable_text = perc_deliverable_tag.text.strip() if perc_deliverable_tag else "N/A"

# Data to be written to Excel
data = {
    "Metric": ["% of Deliverable / Traded Quantity"],
    "Value": [perc_deliverable_text]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Export to Excel
df.to_excel("Wipro_Percentage_of_Deliverable_Traded_Quantity.xlsx", index=False)

print("Data successfully scraped and saved to Wipro_Percentage_of_Deliverable_Traded_Quantity.xlsx")
