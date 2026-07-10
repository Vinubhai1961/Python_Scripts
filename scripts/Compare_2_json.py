import json


def load_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}


def find_missing_tickers(file1_path, file2_path):
    # Load JSON files
    data1 = load_json_file(file1_path)
    data2 = load_json_file(file2_path)

    # Extract tickers (keys) from both files
    tickers1 = set(data1.keys())
    tickers2 = set(data2.keys())

    # Find missing tickers
    missing_in_file1 = tickers2 - tickers1
    missing_in_file2 = tickers1 - tickers2

    # Print results with counts
    print(f"Total tickers in ticker_price.json: {len(tickers1)}")
    print(f"Total tickers in ticker_price_new.json: {len(tickers2)}")
    print(f"\nTickers in ticker_price_new.json but missing in ticker_price.json ({len(missing_in_file1)}):")
    print(sorted(missing_in_file1))
    print(f"\nTickers in ticker_price.json but missing in ticker_price_new.json ({len(missing_in_file2)}):")
    print(sorted(missing_in_file2))

    return missing_in_file1, missing_in_file2


if __name__ == "__main__":
    file1_path = "C:/Users/dipen/Downloads/ticker_price.json"
    file2_path = "C:/Users/dipen/Downloads/ticker_price_new.json"
    find_missing_tickers(file1_path, file2_path)