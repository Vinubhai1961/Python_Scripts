import json
from yahooquery import Ticker

# Assuming 'your_200_tickers' is a list of your 200 ticker symbols
your_200_tickers = ["MU", ...] # Replace with your actual list

tickers = Ticker(your_200_tickers)

# 1. Summary Details:
summary_details = tickers.summary_detail

# Format into a JSON string with indentation
json_output = json.dumps(summary_details, indent=4) # Using 4 spaces for indentation

# Print the JSON output
print(json_output)