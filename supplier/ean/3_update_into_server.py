import os
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
HOTEL_DIR = os.path.join(BASE_DIR, "hotel_id")
FILE_PATH = os.path.join(HOTEL_DIR, "new_hotel_id_list.txt")
ERROR_FILE = os.path.join(HOTEL_DIR, "error_id_list.txt")

URL = "https://mappingapi.innsightmap.com/hotel/pushhotel"
HEADERS = {"Content-Type": "application/json"}
SUPPLIER_CODE = "ean"

BATCH_SIZE = 50
MAX_WORKERS = 5
MAX_RETRIES = 2
RETRY_DELAY = 10
TIMEOUT = 120

session = requests.Session()

saved_ids = set()
failed_ids = set()

saved_lock = threading.Lock()
failed_lock = threading.Lock()
print_lock = threading.Lock()

def load_hotel_ids():
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]

def update_remaining_file(all_ids):
    remaining = [x for x in all_ids if x not in saved_ids]
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        if remaining:
            f.write("\n".join(remaining) + "\n")

def save_error_file():
    final_errors = sorted(failed_ids - saved_ids)
    with open(ERROR_FILE, "w", encoding="utf-8") as f:
        if final_errors:
            f.write("\n".join(final_errors) + "\n")
    print(f"\nError IDs: {len(final_errors)} -> {ERROR_FILE}")

def push_batch(batch, batch_no):
    retry = 0
    while retry < MAX_RETRIES:
        try:
            payload = {
                "supplier_code": SUPPLIER_CODE,
                "hotel_id": batch
            }

            start = time.time()
            response = session.post(
                URL,
                headers=HEADERS,
                json=payload,
                timeout=TIMEOUT
            )
            elapsed = time.time() - start

            result = response.json()

            local_saved = []
            local_error = []

            for item in result.get("results", []):
                hid = item.get("hotel_id")
                if item.get("status") == "saved":
                    local_saved.append(hid)
                else:
                    local_error.append(hid)

            with saved_lock:
                saved_ids.update(local_saved)

            with failed_lock:
                failed_ids.update(local_error)
                failed_ids.difference_update(local_saved)

            with print_lock:
                print(f"Batch {batch_no:04d} | HTTP {response.status_code} | Saved {len(local_saved):02d}/{len(batch)} | Error {len(local_error):02d} | {elapsed:.2f}s")

            if len(local_error) == len(batch):
                retry += 1
                if retry < MAX_RETRIES:
                    print(f"Retry batch {batch_no} ({retry}/{MAX_RETRIES})...")
                    time.sleep(RETRY_DELAY)
                    continue
            return

        except Exception as e:
            retry += 1
            print(f"Batch {batch_no} Exception: {e}")
            if retry < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

def main():
    start = time.time()
    hotel_ids = load_hotel_ids()
    print(f"Total Hotels: {len(hotel_ids)}")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        batch_no = 1
        for i in range(0, len(hotel_ids), BATCH_SIZE):
            futures.append(executor.submit(push_batch, hotel_ids[i:i+BATCH_SIZE], batch_no))
            batch_no += 1
        for f in as_completed(futures):
            f.result()

    update_remaining_file(hotel_ids)
    save_error_file()

    print("\nCompleted")
    print(f"Saved: {len(saved_ids)}")
    print(f"Remaining: {len(hotel_ids)-len(saved_ids)}")
    print(f"Time: {time.time()-start:.2f}s")

if __name__ == "__main__":
    main()

