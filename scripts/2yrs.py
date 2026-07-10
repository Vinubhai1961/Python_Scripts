from yahooquery import Ticker

tickers = Ticker(["CEMPRO.NS"])

#Get historical data for the last 2 years
historical_data = tickers.history(period="5y")
print(historical_data)