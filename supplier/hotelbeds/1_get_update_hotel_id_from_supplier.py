import requests
from dotenv import load_dotenv
import hashlib
import time
import os
from datetime import datetime

load_dotenv()


current_date = datetime.now().strftime("%Y-%m-%d")
# file_path = r"D:/Rokon/ofc_git/new_hotel__get_id/supplier/hotelbeds/hotel_id"
## Server path.
# file_path = r"D:/Rokon/ofc_git/new_hotel__get_id/hotelbeds/hotel_id"


api_secret = os.getenv("HOTELBEDS_API_SECRET")
api_key = os.getenv("HOTELBEDS_API_KEY")
timestamp = str(int(time.time()))

signature_data = f"{api_key}{api_secret}{timestamp}"
signature = hashlib.sha256(signature_data.encode("utf-8")).hexdigest()

# print("Generated Signature:", signature)

url = f"https://api.hotelbeds.com/hotel-content-api/1.0/hotels?fields=code, name&language=ENG&useSecondaryLanguage=false&lastUpdateTime={current_date}&fields=lastUpdate&from=1&to=1000"

payload = {}
headers = {
    "Api-key": api_key,
    "X-Signature": signature,
    "Accept-Encoding": "gzip",
}

response = requests.request("GET", url, headers=headers, data=payload)


if response.status_code == 200:
    data = response.json()
    hotels = data.get("hotels", [])

    # Define the save path
    save_dir = os.path.join(os.path.dirname(__file__), "hotel_id")
    os.makedirs(save_dir, exist_ok=True)

    save_file_path = os.path.join(save_dir, "update_hotel_id_list.txt")

    # Fully replace the existing file but only save hotels updated today
    updated_count = 0
    with open(save_file_path, "w", encoding="utf-8") as f:
        for hotel in hotels:
            code = hotel.get("code")
            last_update = hotel.get("lastUpdate")
            if not (code and last_update):
                continue
            # Accept exact date or datetime-like strings that start with the date
            if isinstance(last_update, str) and last_update.startswith(current_date):
                f.write(f"{code}\n")
                updated_count += 1

    print(f"Updated {updated_count} hotel IDs in {save_file_path}")

else:
    print(f"Error: {response.status_code}")
    print(response.text)
