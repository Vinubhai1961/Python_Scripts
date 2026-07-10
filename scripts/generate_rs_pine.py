import pandas as pd

# === CONFIGURATION ===
INPUT_CSV = "C:\\Users\\dipen\\Downloads\\rs_opportunities_07262025.csv"
OUTPUT_PINE = "C:\\Users\\dipen\\Downloads\\RS_Overlay_TradingView.pine"

# === READ LOCAL CSV FILE ===
df = pd.read_csv(INPUT_CSV)

# Ensure Ticker is uppercase and stripped
df["Ticker"] = df["Ticker"].astype(str).str.strip().str.upper()

# === START BUILDING PINE SCRIPT ===
pine_lines = [
    "//@version=5",
    'indicator("🟢 RS Overlay from CSV", overlay=true)',
    "",
    "ticker = syminfo.ticker",
    "",
    "float rs_val = na",
    "float rs_1m = na",
    "float rs_3m = na",
    "float rs_6m = na",
    'string category = ""',
    ""
]

# === CONVERT EACH ROW TO PINE BLOCK ===
for _, row in df.iterrows():
    try:
        ticker = str(row['Ticker']).strip().upper()
        rs_val = int(row['Relative Strength Percentile'])
        rs_1m = int(row['1 Month Ago Percentile'])
        rs_3m = int(row['3 Months Ago Percentile'])
        rs_6m = int(row['6 Months Ago Percentile'])

        section = str(row.get("Section", "N/A")).strip()

        block = [
            f'if (ticker == "{ticker}")',
            f'    rs_val := {rs_val}',
            f'    rs_1m := {rs_1m}',
            f'    rs_3m := {rs_3m}',
            f'    rs_6m := {rs_6m}',
            f'    category := "{section}"',
            ""
        ]
        pine_lines.extend(block)
    except Exception as e:
        print(f"⚠️ Skipping row due to error: {e}")

# === DISPLAY LABEL ON CHART ===
pine_lines.extend([
    "text = '📊 RS Info: ' + category + '\\n' +",
    '       "Now: " + str.tostring(rs_val) + " | " +',
    '       "1M: " + str.tostring(rs_1m) + " | " +',
    '       "3M: " + str.tostring(rs_3m) + " | " +',
    '       "6M: " + str.tostring(rs_6m)',
    "",
    "if not na(rs_val)",
    "    label.new(bar_index, high, text,",
    "        style=label.style_label_up,",
    "        color=color.new(color.green, 0),",
    "        textcolor=color.white,",
    "        size=size.small)",
    ""
])

# === WRITE TO FILE ===
with open(OUTPUT_PINE, "w", encoding="utf-8") as f:
    f.write("\n".join(pine_lines))

print(f"✅ Pine script saved to:\n{OUTPUT_PINE}")