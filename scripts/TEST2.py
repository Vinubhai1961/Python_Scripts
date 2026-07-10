from yahooquery import Ticker

# Example with a list of symbols
symbols = ['SI']
tickers = Ticker(symbols)

# Retrieve summary detail for all symbols
faang_summary = tickers.summary_detail
print(faang_summary)


