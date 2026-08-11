import os
import requests
import json

base_dir = os.path.abspath(os.path.dirname(__file__))
new = os.path.join(base_dir, "hotel_id", "new_hotel_id_list.txt")

# Read hotel IDs from files
with open(new, "r", encoding="utf-8") as f:
    new_ids = [line.strip() for line in f if line.strip()]

url = "https://mappingapi.innsightmap.com/hotel/pushhotel"
headers = {"Content-Type": "application/json"}


# Function to send batches
def send_batches(ids, source_name):
    for i in range(0, len(ids), 10):
        batch = ids[i : i + 10]
        payload = json.dumps({"supplier_code": "agoda", "hotel_id": batch})
        response = requests.request("POST", url, headers=headers, data=payload)
        print(
            f"Response for {source_name} batch {i//10 + 1}: Complied with status code {response.status_code}"
        )


# Send new IDs first
send_batches(new_ids, "new_hotel_id_list")
