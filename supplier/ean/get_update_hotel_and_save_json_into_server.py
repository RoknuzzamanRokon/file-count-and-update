import requests
import json
from dotenv import load_dotenv
import hashlib
import time
import os
from datetime import datetime, timedelta

load_dotenv()
file_path = r"/var/www/Storage-Contents/Hotel-Supplier-Raw-Contents/ean"
# When working with file paths, it's often best to use os.path.join for better compatibility across different operating systems. However, since you provided a raw string with forward slashes, it should work fine on Windows as well. Just ensure that the path exists and is correct.
# output_dir = os.path.join(os.path.dirname(__file__), "file_path")

week = 2
# start_date = "2026-06-14"
start_date = (datetime.now().date() - timedelta(days=1)).isoformat()


def get_supplier_own_raw_data(date_added_start):
    EAN_API_KEY = os.getenv("EAN_API_KEY")
    EAN_API_SECRET = os.getenv("EAN_API_SECRET")
    BASE_URL = os.getenv("EAN_BASE_URL")

    timestamp = str(int(time.time()))
    signature_data = f"{EAN_API_KEY}{EAN_API_SECRET}{timestamp}"
    signature = hashlib.sha512(signature_data.encode("utf-8")).hexdigest()

    url = f"{BASE_URL}/v3/properties/content?language=en-US&supply_source=expedia&date_added_start={date_added_start}"

    headers = {
        "Accept": "application/json",
        "Authorization": f"EAN APIKey={EAN_API_KEY},Signature={signature},timestamp={timestamp}",
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers, timeout=100)

    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        print(response.text)
        return None


def save_hotels_to_individual_files(data_json_str, output_dir):
    """
    Parse hotel data and save each hotel to a separate JSON file.
    File format: {property_id}.json
    """
    try:
        # Parse the JSON response
        data = json.loads(data_json_str)

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Iterate through each hotel and save to individual file
        for hotel_id, hotel_data in data.items():
            file_name = f"{hotel_id}.json"
            file_full_path = os.path.join(output_dir, file_name)

            # Write each hotel's data to its own JSON file
            with open(file_full_path, "w", encoding="utf-8") as f:
                json.dump(hotel_data, f, indent=4, ensure_ascii=False)

            print(f"Saved: {file_name}")

        print(f"\nTotal hotels saved: {len(data)}")

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"Error saving files: {e}")


# Fetch and save data for multiple dates
# Convert start_date string to datetime
start = datetime.strptime(start_date, "%Y-%m-%d")

# Generate date range (going backwards from start_date for 'week' number of days)
num_days = week * 7
print(f"Fetching data for {num_days} days starting from {start_date}\n")

for day_offset in range(num_days):
    current_date = start - timedelta(days=day_offset)
    date_str = current_date.strftime("%Y-%m-%d")

    print(f"Fetching data for date: {date_str}")
    data = get_supplier_own_raw_data(date_str)

    if data:
        save_hotels_to_individual_files(data, file_path)

    # Sleep 5 seconds before next request (except after the last request)
    if day_offset < num_days - 1:
        print(f"Sleeping 5 seconds...\n")
        time.sleep(5)

print(f"\nCompleted fetching data for all {num_days} days")

