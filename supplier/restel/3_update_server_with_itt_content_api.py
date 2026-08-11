import requests
import json
import time
import os

base_dir = os.path.abspath(os.path.dirname(__file__))
new = os.path.join(base_dir, "hotel_id", "new_hotel_id_list.txt")
no_data_found_file = os.path.join(base_dir, "hotel_id", "no_data_found.txt")


# Read hotel IDs from files
with open(new, "r") as f:
    new_ids = [line.strip() for line in f if line.strip()]


url = "https://mappingapi.innsightmap.com/hotel/pushhotel"
headers = {"Content-Type": "application/json"}


def write_ids(file_path, ids):
    with open(file_path, "w") as f:
        for hotel_id in ids:
            f.write(hotel_id + "\n")


def append_no_data_found(ids):
    if not ids:
        return

    existing_ids = set()
    if os.path.exists(no_data_found_file):
        with open(no_data_found_file, "r") as f:
            existing_ids = {line.strip() for line in f if line.strip()}

    with open(no_data_found_file, "a") as f:
        for hotel_id in ids:
            if hotel_id not in existing_ids:
                f.write(hotel_id + "\n")
                existing_ids.add(hotel_id)


def get_no_data_found_ids(response):
    try:
        data = response.json()
    except ValueError:
        return []

    return [
        str(result.get("hotel_id"))
        for result in data.get("results", [])
        if result.get("reason") == "no_data_found" and result.get("hotel_id")
    ]


# Function to send batches
def send_batches(ids, source_name):
    remaining_ids = ids.copy()

    for i in range(0, len(ids), 2):
        batch = ids[i : i + 2]
        payload = json.dumps({"supplier_code": "restel", "hotel_id": batch})
        response = requests.request("POST", url, headers=headers, data=payload)
        print(f"Response for {source_name} batch {i//2 + 1}: {response.text}")

        no_data_found_ids = get_no_data_found_ids(response)
        if no_data_found_ids:
            no_data_found_set = set(no_data_found_ids)
            remaining_ids = [hotel_id for hotel_id in remaining_ids if hotel_id not in no_data_found_set]
            write_ids(new, remaining_ids)
            append_no_data_found(no_data_found_ids)
            print(f"Moved no_data_found IDs: {', '.join(no_data_found_ids)}")

        time.sleep(2)


# Send new IDs first
send_batches(new_ids, "new_hotel_id_list")

