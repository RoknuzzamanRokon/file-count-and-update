import requests
import json
from dotenv import load_dotenv
import os
import time
from datetime import datetime, timedelta
import hashlib

load_dotenv()


start_date = (datetime.now().date() - timedelta(days=1)).isoformat()
print(f"Data: {start_date}")


def get_new_hotels_raw_data(date_added_start):
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


def get_updated_hotels_raw_data(date_added_end):
    EAN_API_KEY = os.getenv("EAN_API_KEY")
    EAN_API_SECRET = os.getenv("EAN_API_SECRET")
    BASE_URL = os.getenv("EAN_BASE_URL")

    timestamp = str(int(time.time()))
    signature_data = f"{EAN_API_KEY}{EAN_API_SECRET}{timestamp}"
    signature = hashlib.sha512(signature_data.encode("utf-8")).hexdigest()

    url = f"{BASE_URL}/v3/properties/content?language=en-US&supply_source=expedia&date_added_end={date_added_end}"

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


def extract_hotel_ids_by_date(raw_json_text, date_field, target_date):
    if not raw_json_text:
        return []
    data = json.loads(raw_json_text)

    hotel_ids = []
    for hotel_id, hotel_data in data.items():
        date_value = hotel_data.get("dates", {}).get(date_field)
        if isinstance(date_value, str) and date_value.startswith(target_date):
            hotel_ids.append(hotel_id)
    return hotel_ids


def save_hotel_ids(hotel_ids, file_name, save_dir):
    save_file_path = os.path.join(save_dir, file_name)
    with open(save_file_path, "w", encoding="utf-8") as f:
        for hotel_id in hotel_ids:
            f.write(f"{hotel_id}\n")
    print(f"Saved {len(hotel_ids)} hotel IDs to {save_file_path}")


if __name__ == "__main__":
    save_dir = os.path.join(os.path.dirname(__file__), "hotel_id")
    os.makedirs(save_dir, exist_ok=True)

    new_hotels_raw = get_new_hotels_raw_data(start_date)
    new_hotel_ids = extract_hotel_ids_by_date(new_hotels_raw, "added", start_date)
    save_hotel_ids(new_hotel_ids, "new_hotel_id_list.txt", save_dir)

    updated_hotels_raw = get_updated_hotels_raw_data(start_date)
    updated_hotel_ids = extract_hotel_ids_by_date(updated_hotels_raw, "updated", start_date)
    save_hotel_ids(updated_hotel_ids, "only_update_hotel_id.txt", save_dir)
