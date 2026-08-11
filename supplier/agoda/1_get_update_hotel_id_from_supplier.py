import requests
import json
from dotenv import load_dotenv
import os
import time
from datetime import datetime, timedelta

load_dotenv()

AGODA_API_KEY=os.getenv("AGODA_API_KEY")
AGODA_SITEID=os.getenv("AGODA_SITEID")
AGODA_FEED_URL=os.getenv("AGODA_FEED_URL")
DATE=datetime.now() - timedelta(days=1)
MDATE=DATE.strftime("%Y%m%d")

url = f"{AGODA_FEED_URL}/getfeed?feed_id=32&apikey={AGODA_API_KEY}&site_id={AGODA_SITEID}&mdate={MDATE}&mtypeid=2"

payload = ""
headers = {"Content-Type": "application/json"}

response = requests.request("GET", url, headers=headers, data=payload)

if response.status_code == 200:
    data = response.json()
    hotel_ids = data.get("changedHotelFeed", {}).get("changed", {}).get("hotels", {}).get("hotel_id", [])

    if hotel_ids:
        # Define the save path
        save_dir = os.path.join(os.path.dirname(__file__), "hotel_id")
        os.makedirs(save_dir, exist_ok=True)
        save_file_path = os.path.join(save_dir, "update_hotel_id_list.txt")

        with open(save_file_path, "w") as f:
            for hid in hotel_ids:
                f.write(f"{hid}\n")

        print(f"Saved {len(hotel_ids)} hotel IDs to {save_file_path}")
    else:
        print("No hotel IDs found in response")
else:
    print(f"Error: {response.status_code}")
    print(response.text)

