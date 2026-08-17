import requests
import json
import time
import os

base_dir = os.path.abspath(os.path.dirname(__file__))
file_path = os.path.join(base_dir, "hotel_id", "only_update_hotel_id.txt")

url = "https://mappingapi.innsightmap.com/hotel/pushhotelWithChangeLog"
headers = {"Content-Type": "application/json"}

BATCH_SIZE = 5
MAX_RETRIES = 2
RETRY_DELAY = 10


def load_hotel_ids():
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]


def remove_saved_ids(saved_ids):
    if not saved_ids:
        return

    with open(file_path, "r") as f:
        current_ids = [line.strip() for line in f if line.strip()]

    remaining_ids = [hotel_id for hotel_id in current_ids if hotel_id not in saved_ids]

    with open(file_path, "w") as f:
        if remaining_ids:
            f.write("\n".join(remaining_ids) + "\n")

    print(f"\n🗑 Removed {len(saved_ids)} saved hotel(s) from file")


def push_batch(batch, batch_no):
    retry_count = 0

    while retry_count < MAX_RETRIES:
        try:
            payload = {"supplier_code": "hotelbeds", "hotel_id": batch}

            response = requests.post(url, headers=headers, json=payload, timeout=120)

            print("\n" + "=" * 80)
            print(f"Batch: {batch_no}")
            print(f"Attempt: {retry_count + 1}")
            print(f"Hotel IDs: {batch}")
            print(f"HTTP Status: {response.status_code}")

            result = response.json()

            print("Response:")
            print(json.dumps(result, indent=4, ensure_ascii=False))

            saved_ids = []
            error_ids = []

            for item in result.get("results", []):
                hotel_id = item.get("hotel_id")
                status = item.get("status")

                if status == "saved":
                    print(f"✅ SAVED : {hotel_id}")
                    saved_ids.append(hotel_id)
                else:
                    print(f"❌ ERROR : {hotel_id}")
                    error_ids.append(hotel_id)

            # Remove successful IDs from file
            if saved_ids:
                remove_saved_ids(saved_ids)

            # If all hotels returned error, retry
            if len(error_ids) == len(batch):
                retry_count += 1

                if retry_count < MAX_RETRIES:
                    print(
                        f"\n⚠ All hotels returned 'error'. "
                        f"Waiting {RETRY_DELAY} seconds before retry "
                        f"({retry_count + 1}/{MAX_RETRIES})..."
                    )
                    time.sleep(RETRY_DELAY)
                    continue

                print(f"\n❌ Batch {batch_no} failed after " f"{MAX_RETRIES} retries.")

            return

        except Exception as e:
            retry_count += 1

            print(f"\n❌ Exception: {e}")

            if retry_count < MAX_RETRIES:
                print(
                    f"⚠ Waiting {RETRY_DELAY} seconds before retry "
                    f"({retry_count + 1}/{MAX_RETRIES})..."
                )
                time.sleep(RETRY_DELAY)
            else:
                print(f"\n❌ Batch {batch_no} failed after " f"{MAX_RETRIES} retries.")


def main():
    hotel_ids = load_hotel_ids()

    print(f"Total Hotels Found: {len(hotel_ids)}")

    batch_no = 1

    for i in range(0, len(hotel_ids), BATCH_SIZE):
        batch = hotel_ids[i : i + BATCH_SIZE]

        push_batch(batch, batch_no)

        batch_no += 1

        # Small pause between batches
        time.sleep(2)

    print("\n🎉 Processing Completed")


if __name__ == "__main__":
    main()
