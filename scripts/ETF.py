import json
from yahooquery import Ticker

# 1. Fetching Data for the Ticker
tickers = Ticker(["SI"])

# 2. Retrieving the desired data (e.g., asset_profile)
asset_profiles = tickers.asset_profile

# 3. Formatting into a JSON String
# The 'indent' parameter is key for pretty-printing.
# It specifies the number of spaces for indentation.
json_output = json.dumps(asset_profiles, indent=4) # Using 4 spaces for indentation

# 4. Printing the JSON
print(json_output)