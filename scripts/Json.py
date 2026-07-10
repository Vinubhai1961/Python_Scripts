import json
import os
import logging
from yahooquery import Ticker
from tqdm import tqdm
import time
from datetime import timedelta
import math

# File paths
INPUT_PATH = r"C:\Users\dipen\Downloads\ticker_info.json"
OUTPUT_PATH = r"C:\Users\dipen\Downloads\ticker_price_master.json"
FAILED_TICKERS_PATH = r"C:\Users\dipen\Downloads\failed_tickers.json"
LOG_PATH = r"C:\Users\dipen\Downloads\ticker_price_fetch.log"

# Batch sizes and constants
PHASE1_BATCH_SIZE = 500
PHASE2_BATCH_SIZE = 200
MAX_RETRIES = 2
BATCH_DELAY = 1  # Seconds to wait between batches to avoid rate limiting

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)


def load_ticker_data(file_path):
    if not os.path.exists(file_path):
        logging.error(f"Input file {file_path} does not exist")
        raise FileNotFoundError(f"Input file {file_path} does not exist")
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        if not data:
            logging.error("Input JSON file is empty")
            raise ValueError("Input JSON file is empty")
        return data
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON format in {file_path}: {str(e)}")
        raise


def save_ticker_data(data, file_path):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logging.info(f"Saved data to {file_path}")
    except Exception as e:
        logging.error(f"Failed to save data to {file_path}: {str(e)}")
        raise


def fetch_prices(tickers, ticker_data, batch_size, phase, retry_count=0):
    batch_results = {'pass': 0, 'below_5': 0, 'fail_error': 0, 'retry': 0}
    excluded_tickers = []
    price_data = ticker_data.copy()

    try:
        yq_tickers = Ticker(tickers)
        price_info = yq_tickers.price

        for ticker in tickers:
            try:
                ticker_price = price_info.get(ticker, {}).get('regularMarketPrice', None)
                if ticker_price is not None and isinstance(ticker_price, (int, float)):
                    if ticker_price >= 5:
                        price_data[ticker]['info']['Price'] = ticker_price
                        batch_results['pass'] += 1
                    else:
                        batch_results['below_5'] += 1
                        excluded_tickers.append(ticker)
                else:
                    batch_results['fail_error'] += 1
                    excluded_tickers.append(ticker)
            except Exception as e:
                logging.error(f"Phase {phase} - Error processing {ticker}: {str(e)}")
                batch_results['fail_error'] += 1
                excluded_tickers.append(ticker)

    except Exception as e:
        logging.error(f"Phase {phase} - Batch error: {str(e)}")
        if retry_count < MAX_RETRIES:
            logging.info(f"Phase {phase} - Retrying batch (attempt {retry_count + 2}/{MAX_RETRIES + 1})")
            time.sleep(2 ** retry_count)  # Exponential backoff
            retry_results, retry_excluded, retry_data = fetch_prices(tickers, price_data, batch_size, phase,
                                                                     retry_count + 1)
            batch_results['retry'] += 1
            batch_results['pass'] += retry_results['pass']
            batch_results['below_5'] += retry_results['below_5']
            batch_results['fail_error'] += retry_results['fail_error']
            price_data.update(retry_data)
            excluded_tickers.extend(retry_excluded)
        else:
            logging.error(f"Phase {phase} - Max retries reached for this batch")
            batch_results['fail_error'] += len(tickers)
            excluded_tickers.extend(tickers)

    return batch_results, excluded_tickers, price_data


def process_phase(tickers, ticker_data, batch_size, phase):
    total_results = {'pass': 0, 'below_5': 0, 'fail_error': 0, 'retry': 0}
    all_excluded_tickers = []
    price_data = ticker_data.copy()

    # Calculate total batches
    total_batches = math.ceil(len(tickers) / batch_size)
    logging.info(f"Phase {phase} - Total batches to process: {total_batches}")

    for i in range(0, len(tickers), batch_size):
        batch_tickers = tickers[i:i + batch_size]
        logging.info(
            f"Phase {phase} - Processing batch {i // batch_size + 1}/{total_batches} ({len(batch_tickers)} tickers)")

        # Start timing for the batch
        batch_start_time = time.time()

        # Progress bar with estimated time remaining
        with tqdm(total=len(batch_tickers), desc=f"Phase {phase} - Batch {i // batch_size + 1}/{total_batches}",
                  unit="ticker") as pbar:
            batch_results, batch_excluded, batch_price_data = fetch_prices(batch_tickers, price_data, batch_size, phase)
            pbar.update(len(batch_tickers))

        # Calculate batch execution time
        batch_end_time = time.time()
        batch_execution_time = timedelta(seconds=batch_end_time - batch_start_time)

        # Update overall results
        price_data.update(batch_price_data)
        total_results['pass'] += batch_results['pass']
        total_results['below_5'] += batch_results['below_5']
        total_results['fail_error'] += batch_results['fail_error']
        total_results['retry'] += batch_results['retry']
        all_excluded_tickers.extend(batch_excluded)

        # Print batch summary
        logging.info(f"Phase {phase} - Batch {i // batch_size + 1}/{total_batches} results: "
                     f"Pass={batch_results['pass']}, "
                     f"Below $5={batch_results['below_5']}, "
                     f"Fail (Error)={batch_results['fail_error']}, "
                     f"Retry={batch_results['retry']}, "
                     f"Time={batch_execution_time}")

        # Clear batch variables to free memory
        del batch_tickers
        del batch_price_data
        del batch_excluded

        # Delay between batches
        time.sleep(BATCH_DELAY)

    return total_results, all_excluded_tickers, price_data


def main():
    start_time = time.time()

    # Validate and load ticker data
    try:
        ticker_data = load_ticker_data(INPUT_PATH)
    except Exception as e:
        logging.error(f"Failed to load ticker data: {str(e)}")
        return

    tickers = list(ticker_data.keys())
    total_tickers = len(tickers)
    logging.info(f"Total tickers to process: {total_tickers}")

    # Phase 1: Initial processing with batch size 500
    logging.info("\nStarting Phase 1 (Batch size: 500)")
    phase1_results, excluded_tickers, price_data = process_phase(tickers, ticker_data, PHASE1_BATCH_SIZE, 1)

    # Print Phase 1 summary
    logging.info("\nPhase 1 Summary:")
    logging.info(f"Pass: {phase1_results['pass']}")
    logging.info(f"Below $5: {phase1_results['below_5']}")
    logging.info(f"Fail (Error): {phase1_results['fail_error']}")
    logging.info(f"Retry: {phase1_results['retry']}")
    logging.info(f"Excluded tickers to retry in Phase 2: {len(excluded_tickers)}")

    # Clear Phase 1 variables
    del tickers

    # Phase 2: Process excluded tickers with batch size 200
    if excluded_tickers:
        logging.info(f"\nStarting Phase 2 (Batch size: 200, {len(excluded_tickers)} excluded tickers)")
        phase2_results, remaining_excluded, price_data = process_phase(excluded_tickers, price_data, PHASE2_BATCH_SIZE,
                                                                       2)

        # Print Phase 2 summary
        logging.info("\nPhase 2 Summary:")
        logging.info(f"Pass: {phase2_results['pass']}")
        logging.info(f"Below $5: {phase2_results['below_5']}")
        logging.info(f"Fail (Error): {phase2_results['fail_error']}")
        logging.info(f"Retry: {phase2_results['retry']}")
        logging.info(f"Remaining excluded tickers: {len(remaining_excluded)}")

        # Save excluded tickers
        excluded_ticker_data = {ticker: ticker_data[ticker] for ticker in remaining_excluded}
        save_ticker_data(excluded_ticker_data, FAILED_TICKERS_PATH)
    else:
        phase2_results = {'pass': 0, 'below_5': 0, 'fail_error': 0, 'retry': 0}
        remaining_excluded = []

    # Phase 3: Save final results
    logging.info("\nPhase 3: Saving results")
    save_ticker_data(price_data, OUTPUT_PATH)

    # Calculate total execution time
    end_time = time.time()
    execution_time = timedelta(seconds=end_time - start_time)

    # Print final summary
    total_pass = phase1_results['pass'] + phase2_results['pass']
    total_below_5 = phase2_results['below_5']
    total_fail_error = phase2_results['fail_error']
    total_retry = phase1_results['retry'] + phase2_results['retry']
    total_output_tickers = len(price_data)

    logging.info("\nFinal Summary:")
    logging.info(f"Total Tickers in Output: {total_output_tickers}")
    logging.info(f"Total Pass: {total_pass}")
    logging.info(f"Total Below $5: {total_below_5}")
    logging.info(f"Total Failed (Error): {total_fail_error}")
    logging.info(f"Total Retry: {total_retry}")
    logging.info(f"Total Execution Time: {execution_time}")
    logging.info(f"Results saved to {OUTPUT_PATH}")
    if remaining_excluded:
        logging.info(f"Excluded tickers saved to {FAILED_TICKERS_PATH}")


if __name__ == "__main__":
    main()