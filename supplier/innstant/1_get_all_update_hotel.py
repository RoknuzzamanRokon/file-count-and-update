import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


INNESTENT_HOTEL_KEY=os.getenv("INNESTENT_HOTEL_KEY")
INNESTENT_HOTEL_TOKEN=os.getenv("INNESTENT_HOTEL_TOKEN")


current_date = datetime.now().strftime("%Y-%m-%d")


base_dir = os.path.abspath(os.path.dirname(__file__))
update_hotel_id = os.path.join(base_dir, "hotel_id", "new_hotel_id_list.txt")

url = f"https://static-data.innstant-servers.com/hotels-diff/{current_date}"

payload = ""
headers = {
    "aether-application-key": INNESTENT_HOTEL_KEY,
    "aether-access-token": INNESTENT_HOTEL_TOKEN,
}

response = requests.request("GET", url, headers=headers, data=payload)


if response.status_code == 200:
    data = response.json()
    # print(data)

    if isinstance(data, list):
        hotel_ids = data
    elif isinstance(data, dict):
        hotel_ids = data.get("hotel_ids") or data.get("data") or []
    else:
        raise ValueError(f"Unexpected response type: {type(data).__name__}")

    hotel_ids = [
        str(hotel_id).strip() for hotel_id in hotel_ids if str(hotel_id).strip()
    ]

    with open(update_hotel_id, "w", encoding="utf-8") as f:
        for hotel_id in hotel_ids:
            f.write(hotel_id + "\n")
        print(f"Saved: {len(hotel_ids)} hotel ID")
else:
    print(f"Error: {response.status_code}")
    print(response.text)

