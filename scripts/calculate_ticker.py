import json


def count_tickers(file_path):
    try:
        # Load the JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Count the number of top-level keys (tickers)
        ticker_count = len(data)

        print(f"Total number of tickers: {ticker_count}")
        return ticker_count

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in the file.")
        return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None


if __name__ == "__main__":
    file_path = "C:/Users/dipen/Downloads/ticker_price_new.json"
    count_tickers(file_path)