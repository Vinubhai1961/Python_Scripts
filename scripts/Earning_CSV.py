import pandas as pd
from pathlib import Path

# ========================= CONFIG =========================
INPUT_FILE  = Path("C:/Users/dipen/Downloads/May_2026_Earnings.csv")   # Change if needed
OUTPUT_FILE = Path("C:/Users/dipen/Downloads/May_2026_Earnings_CLEANED.csv")

MIN_ATR = 3.0
# =======================================================

def clean_earnings_file():
    if not INPUT_FILE.exists():
        print(f"❌ File not found: {INPUT_FILE}")
        return

    print(f"Reading: {INPUT_FILE.name}")
    df = pd.read_csv(INPUT_FILE)

    original_count = len(df)
    print(f"Total rows loaded: {original_count}")

    # Convert ATR to numeric
    if "ATR" in df.columns:
        df["ATR"] = pd.to_numeric(df["ATR"], errors='coerce')
    else:
        print("⚠️ ATR column not found!")
        return

    # Count how many will be removed
    low_atr = df[(df["ATR"] < MIN_ATR) & df["ATR"].notna()]
    print(f"Rows with ATR < {MIN_ATR}: {len(low_atr)}")

    # Keep rows where:
    # - ATR >= 3.0 OR
    # - ATR is NaN (unknown) OR
    # - Sector is ETF
    mask_keep = (
        (df["ATR"] >= MIN_ATR) |
        (df["ATR"].isna()) |
        (df.get("Sector", "") == "ETF")
    )

    cleaned = df[mask_keep].copy()

    print(f"✅ After cleaning: {len(cleaned)} rows remain (removed {original_count - len(cleaned)})")

    # Save cleaned file
    cleaned.to_csv(OUTPUT_FILE, index=False)
    print(f"💾 Cleaned file saved as: {OUTPUT_FILE.name}")

    # Optional: Show summary
    print("\nSummary by Sector:")
    print(cleaned.groupby("Sector", dropna=False).size())

if __name__ == "__main__":
    clean_earnings_file()