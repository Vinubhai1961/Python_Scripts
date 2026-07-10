import json
import time
from yahooquery import Ticker
from tqdm import tqdm
import os

# Configurable paths
file_path = r"C:\Users\dipen\Downloads\unresolved_tickers.txt"
output_json_path = r"C:\Users\dipen\Downloads\ticker_profiles.json"
batch_size = 250
sleep_between_batches = 2
max_retries = 3

# Step 1: Read ticker list
with open(file_path, 'r') as file:
    tickers_list = [line.strip() for line in file if line.strip()]

# Load existing data if any (for resuming)
if os.path.exists(output_json_path):
    with open(output_json_path, 'r') as f:
        final_output = json.load(f)
else:
    final_output = {}

# Filter out already processed tickers
pending_tickers = [t for t in tickers_list if t not in final_output]

# Helper: split into chunks
def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]

# Step 2: Process with progress bar and retries
for batch in tqdm(list(chunked(pending_tickers, batch_size)), desc="Processing Batches"):
    for attempt in range(max_retries):
        try:
            tickers = Ticker(batch)
            profiles = tickers.asset_profile

            for ticker, profile in profiles.items():
                if isinstance(profile, dict):
                    final_output[ticker] = {
                        'sector': profile.get('sector'),
                        'industry': profile.get('industry')
                    }
            time.sleep(sleep_between_batches)
            break  # Success, exit retry loop
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed for batch {batch[0]}-{batch[-1]}: {e}")
            time.sleep(3)
    else:
        print(f"❌ Failed to process batch {batch[0]}-{batch[-1]} after {max_retries} attempts")

    # Save after each batch
    with open(output_json_path, 'w') as f:
        json.dump(final_output, f, indent=4)

print(f"\n✅ Completed! Output saved to: {output_json_path}")