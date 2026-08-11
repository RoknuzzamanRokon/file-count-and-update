import os
import requests
import ijson
from dotenv import load_dotenv

load_dotenv()

HYPERGUEST_TOKEN = os.getenv("HYPERGUEST_TOKEN")

url = "https://hg-static.hyperguest.com/hotels.json"

headers = {
    "Authorization": f"Bearer {HYPERGUEST_TOKEN}",
    "Accept": "application/json",
}

save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hotel_id")
os.makedirs(save_dir, exist_ok=True)

save_file_path = os.path.join(save_dir, "update_hotel_id_list.txt")

count = 0

with requests.get(url, headers=headers, stream=True, timeout=300) as response:
    response.raise_for_status()

    print("Status:", response.status_code)
    print("Content-Type:", response.headers.get("Content-Type"))
    print("Content-Encoding:", response.headers.get("Content-Encoding"))

    # Tell urllib3 to transparently decompress gzip
    response.raw.decode_content = True

    with open(save_file_path, "w", encoding="utf-8") as f:
        for hotel in ijson.items(response.raw, "item"):
            hotel_id = hotel.get("hotel_id")
            if hotel_id:
                f.write(f"{hotel_id}\n")
                count += 1

                if count % 10000 == 0:
                    print(f"Processed {count:,} hotels")

print(f"\nDone! Saved {count:,} hotel IDs.")
