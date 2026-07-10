from yahooquery import Ticker
import pandas as pd

tickers = ["^NSEI"]

try:
    data = Ticker(tickers).history(period="2y")

    for ticker in tickers:
        df = data.loc[ticker].reset_index()[["date", "close"]].rename(columns={"date": "datetime"})

        # Convert datetime safely and ensure all are timezone-naive
        df["datetime"] = pd.to_datetime(df["datetime"], utc=True)  # Always make UTC first
        df["datetime"] = df["datetime"].dt.tz_convert(None)  # Then remove timezone info

        # Convert to Unix timestamp (seconds)
        df["datetime"] = df["datetime"].astype("int64") // 10 ** 9

        print(f"{ticker} processed successfully:\n{df.head()}")

except Exception as e:
    print(f"Error: {e}")
