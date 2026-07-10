import os
import json
import pandas as pd
from yahooquery import Ticker

tickers = ["^CRSLDX"]

def get_first(d, keys, default=None):
    if not isinstance(d, dict):
        return default
    for k in keys:
        v = d.get(k)
        if v is not None:
            return v
    return default

def extract_history_df(data, symbol):
    if data is None or data.empty:
        return None

    if isinstance(data.index, pd.MultiIndex):
        if symbol not in data.index.get_level_values(0):
            return None
        df = data.loc[symbol].reset_index()
    else:
        df = data.reset_index()

    if "date" not in df.columns or "close" not in df.columns:
        return None

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "close"])
    return df

def safe_module_dict(module, symbol):
    if isinstance(module, dict):
        val = module.get(symbol, {})
        return val if isinstance(val, dict) else {}
    return {}

def build_info(symbol):
    t = Ticker(symbol, validate=False)

    price_mod = safe_module_dict(getattr(t, "price", {}), symbol)
    summary_mod = safe_module_dict(getattr(t, "summary_profile", {}), symbol)
    hist = extract_history_df(t.history(period="2y"), symbol)

    last_close = None
    last_volume = None
    if hist is not None and not hist.empty:
        last_close = float(hist["close"].iloc[-1])
        if "volume" in hist.columns:
            lv = hist["volume"].dropna()
            if not lv.empty:
                last_volume = float(lv.iloc[-1])

    info = {
        "Ticker Name": get_first(price_mod, ["shortName", "longName", "symbol"], symbol),
        "Price": get_first(price_mod, ["regularMarketPrice", "preMarketPrice", "postMarketPrice"], last_close),
        "DVol": get_first(price_mod, ["regularMarketVolume", "volume"], last_volume),
        "RVol": get_first(price_mod, ["regularMarketVolume", "volume"], last_volume),
        "Sector": summary_mod.get("sector", "") if isinstance(summary_mod, dict) else "",
        "Industry": summary_mod.get("industry", "") if isinstance(summary_mod, dict) else "",
        "type": get_first(price_mod, ["quoteType"], "Stock"),
        "52WKL": get_first(price_mod, ["fiftyTwoWeekLow"], None),
        "52WKH": get_first(price_mod, ["fiftyTwoWeekHigh"], None),
        "MCAP": get_first(price_mod, ["marketCap"], None),
        "AvgVol": get_first(price_mod, ["averageDailyVolume3Month", "averageVolume", "averageDailyVolume10Day"], None),
        "AvgVol10": get_first(price_mod, ["averageDailyVolume10Day", "averageVolume10days"], None),
        "Exchange": get_first(price_mod, ["fullExchangeName", "exchangeName", "exchange"], ""),
        "FF": get_first(price_mod, ["sharesOutstanding"], None),
        "1YR_Per": get_first(price_mod, ["fiftyTwoWeekChangePercent"], None),
        "DPChange": get_first(price_mod, ["regularMarketChangePercent"], None),
    }

    def fmt_num(x, decimals=2):
        if x is None or pd.isna(x):
            return None
        try:
            return round(float(x), decimals)
        except Exception:
            return x

    for k in ["Price", "52WKL", "52WKH", "MCAP", "FF", "1YR_Per", "DPChange"]:
        info[k] = fmt_num(info[k], 2 if k != "1YR_Per" and k != "DPChange" else 4)

    return info, hist

results = {}
os.makedirs("data", exist_ok=True)

for ticker in tickers:
    info, hist = build_info(ticker)
    results[ticker] = info
    if hist is not None:
        hist.to_csv(f"data/{ticker.replace('^','')}_history.csv", index=False)

with open("data/ticker_info.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)

print(json.dumps(results, indent=2, default=str))