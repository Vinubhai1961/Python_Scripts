from yahooquery import Ticker
import pandas as pd
tickers = ["^CRSLDX"]
try:
    data = Ticker(tickers).history(period="2y")
    for ticker in tickers:
        df = data.loc[ticker].reset_index()[["date", "close"]].rename(columns={"date": "datetime"})
        df["datetime"] = pd.to_datetime(df["datetime"])
        if df["datetime"].dt.tz is not None:
            df["datetime"] = df["datetime"].dt.tz_convert(None)
        df["datetime"] = df["datetime"].astype(int) // 10**9
        print(f"{ticker} processed successfully:\n{df.head()}")
except Exception as e:
    print(f"Error: {e}")