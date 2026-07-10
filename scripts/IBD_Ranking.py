# =========================================================
# EXACT TRADINGVIEW IBD RS RATING SYSTEM
# =========================================================

import re
import pandas as pd
import numpy as np

# =========================================================
# FILES
# =========================================================

INPUT_FILE = r"C:\Users\dipen\Downloads\Missing_RS.log"
OUTPUT_FILE = r"C:\Users\dipen\Downloads\Final_IBD_RS.csv"

# =========================================================
# LOAD LOG
# =========================================================

with open(INPUT_FILE, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# =========================================================
# PARSE LOG
# =========================================================

pattern = re.compile(
    r"\[(.*?)\].*?FINAL → RS=([\d\.]+),\s*1M=([\d\.nan\-]+),\s*3M=([\d\.nan\-]+),\s*6M=([\d\.nan\-]+)",
    re.DOTALL
)

matches = pattern.findall(content)

# =========================================================
# BUILD DATAFRAME
# =========================================================

rows = []

def safe_float(x):
    try:
        return float(x)
    except:
        return np.nan

for m in matches:

    rows.append({
        "Ticker": m[0].strip(),
        "RAW_RS": safe_float(m[1]),
        "RS_1M": safe_float(m[2]),
        "RS_3M": safe_float(m[3]),
        "RS_6M": safe_float(m[4]),
    })

df = pd.DataFrame(rows)

# =========================================================
# CLEAN
# =========================================================

df = df.drop_duplicates(subset=["Ticker"])
df = df.dropna(subset=["RAW_RS"])

# =========================================================
# BUILD THRESHOLDS FROM UNIVERSE
# =========================================================

def build_thresholds(series):

    s = series.dropna()

    return {
        "p98": np.percentile(s, 98),
        "p89": np.percentile(s, 89),
        "p69": np.percentile(s, 69),
        "p49": np.percentile(s, 49),
        "p29": np.percentile(s, 29),
        "p09": np.percentile(s, 9),
        "p01": np.percentile(s, 1),
    }

# =========================================================
# EXACT PINE LOGIC
# =========================================================

def rs_rating(score, t):

    if np.isnan(score):
        return np.nan

    p98 = t["p98"]
    p89 = t["p89"]
    p69 = t["p69"]
    p49 = t["p49"]
    p29 = t["p29"]
    p09 = t["p09"]
    p01 = t["p01"]

    r = 1

    if score >= p98:
        r = 99

    elif score >= p89:
        r = 90 + round(8 * (score - p89) / (p98 - p89))

    elif score >= p69:
        r = 70 + round(19 * (score - p69) / (p89 - p69))

    elif score >= p49:
        r = 50 + round(19 * (score - p49) / (p69 - p49))

    elif score >= p29:
        r = 30 + round(19 * (score - p29) / (p49 - p29))

    elif score >= p09:
        r = 10 + round(19 * (score - p09) / (p29 - p09))

    elif score >= p01:
        r = 2 + round(7 * (score - p01) / (p09 - p01))

    return int(max(1, min(99, r)))

# =========================================================
# BUILD THRESHOLDS
# =========================================================

th_raw = build_thresholds(df["RAW_RS"])

th_1m = build_thresholds(df["RS_1M"])

th_3m = build_thresholds(df["RS_3M"])

th_6m = build_thresholds(df["RS_6M"])

# =========================================================
# APPLY RATINGS
# =========================================================

df["IBD_RS"] = df["RAW_RS"].apply(
    lambda x: rs_rating(x, th_raw)
)

df["IBD_RS_1M"] = df["RS_1M"].apply(
    lambda x: rs_rating(x, th_1m)
)

df["IBD_RS_3M"] = df["RS_3M"].apply(
    lambda x: rs_rating(x, th_3m)
)

df["IBD_RS_6M"] = df["RS_6M"].apply(
    lambda x: rs_rating(x, th_6m)
)

# =========================================================
# COMPOSITE SCORE
# =========================================================

df["Composite_RS"] = (
    df["IBD_RS_1M"] * 0.20 +
    df["IBD_RS_3M"] * 0.40 +
    df["IBD_RS_6M"] * 0.40
).round(2)

# =========================================================
# FINAL COMPOSITE RATING
# =========================================================

th_comp = build_thresholds(df["Composite_RS"])

df["FINAL_IBD_RS"] = df["Composite_RS"].apply(
    lambda x: rs_rating(x, th_comp)
)

# =========================================================
# SORT
# =========================================================

df = df.sort_values(
    by=["FINAL_IBD_RS", "Composite_RS"],
    ascending=False
)

# =========================================================
# FINAL OUTPUT
# =========================================================

final_cols = [

    "Ticker",

    "RAW_RS",
    "RS_1M",
    "RS_3M",
    "RS_6M",

    "IBD_RS",
    "IBD_RS_1M",
    "IBD_RS_3M",
    "IBD_RS_6M",

    "Composite_RS",
    "FINAL_IBD_RS"
]

df = df[final_cols]

# =========================================================
# SAVE
# =========================================================

df.to_csv(OUTPUT_FILE, index=False)

# =========================================================
# DISPLAY THRESHOLDS
# =========================================================

print("\n================ THRESHOLDS ================\n")

for k, v in th_raw.items():
    print(f"{k} = {v:.2f}")

# =========================================================
# SUMMARY
# =========================================================

print("\n============================================")
print("FINAL IBD RS FILE GENERATED")
print("============================================")

print(f"\nTotal Stocks : {len(df)}")

print("\nTOP 25 STOCKS\n")

print(df.head(25).to_string(index=False))

print("\nSaved To:")
print(OUTPUT_FILE)

print("\nDONE")