from yahooquery import Ticker
import logging
logging.basicConfig(level=logging.DEBUG)
t = Ticker("SPCX")
print("History:", t.history(period="1d"))

