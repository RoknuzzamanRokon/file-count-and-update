import os
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from sqlalchemy import create_engine, text

load_dotenv()

# # THis path for local file path.
# master_hotel_id_list = r"D:/Rokon/ofc_git/new_hotel__get_id/supplier/paximumhotel/hotel_id/new_hotel_id_list.txt"
# missing_hotel_id_file = r"D:/Rokon/ofc_git/new_hotel__get_id/supplier/paximumhotel/hotel_id/missing_hotel_id_list.txt"

## This path for remote file path.
master_hotel_id_list = r"/var/www/ScriptEngine/Python-Application/New-Hotel-Id-Collection-Function/supplier/paximumhotel/hotel_id/new_hotel_id_list.txt"
missing_hotel_id_file = r"/var/www/ScriptEngine/Python-Application/New-Hotel-Id-Collection-Function/supplier/paximumhotel/hotel_id/missing_hotel_id_list.txt"

table = "s_paximumhotel_master"

MAX_WORKERS = int(os.getenv("MAX_WORKERS", "20"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))

db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

connection_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
engine = create_engine(
    connection_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=20,
    max_overflow=30,
)

file_lock = threading.Lock()
print_lock = threading.Lock()

http_session = requests.Session()
http_adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100)
http_session.mount("https://", http_adapter)
http_session.mount("http://", http_adapter)


UPSERT_QUERY = text(f"""
    INSERT IGNORE INTO {table} (
        ittid,
        hotel_id,
        name,
        local_name,
        property_type,
        star_rating,
        lat,
        lon,
        country_code,
        postal_code,
        state,
        city,
        address_1,
        address_2,
        photo
    ) VALUES (
        :ittid,
        :hotel_id,
        :name,
        :local_name,
        :property_type,
        :star_rating,
        :lat,
        :lon,
        :country_code,
        :postal_code,
        :state,
        :city,
        :address_1,
        :address_2,
        :photo
    )
""")


def safe_print(message):
    with print_lock:
        print(message)


def ensure_file_exists(file_path):
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8"):
            pass


def get_hotel_details(hotel_id, timeout=REQUEST_TIMEOUT):
    url = "https://mappingapi.innsightmap.com/hotel/details"
    payload = {"supplier_code": "paximumhotel_new", "hotel_id": hotel_id}
    headers = {"Content-Type": "application/json"}

    try:
        response = http_session.post(
            url, headers=headers, json=payload, timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        safe_print(f"[API FAILED] Hotel ID {hotel_id}: {e}")
        return None


def normalize_paximumhotel_hotel_details(hotel_details):
    address = hotel_details.get("address") or {}

    def safe_float(value):
        try:
            return float(value) if value not in (None, "") else None
        except (ValueError, TypeError):
            return None

    def safe_str(value):
        if value is None:
            return None
        value = str(value).strip()
        return value if value else None

    return {
        "ittid": None,
        "hotel_id": safe_str(hotel_details.get("hotel_id")),
        "name": safe_str(hotel_details.get("name")),
        "local_name": safe_str(
            hotel_details.get("name_local") or hotel_details.get("hotel_formerly_name")
        ),
        "property_type": safe_str(hotel_details.get("property_type")),
        "star_rating": safe_float(hotel_details.get("star_rating")),
        "address_1": safe_str(address.get("address_line_1")),
        "address_2": safe_str(address.get("address_line_2")),
        "lat": safe_float(address.get("latitude")),
        "lon": safe_float(address.get("longitude")),
        "country_code": safe_str(
            hotel_details.get("country_code") or address.get("country_code")
        ),
        "city": safe_str(address.get("city")),
        "postal_code": safe_str(address.get("postal_code")),
        "state": safe_str(address.get("state")),
        "photo": safe_str(hotel_details.get("primary_photo")),
    }


def remove_single_id_from_list(file_path, hotel_id):
    hotel_id = str(hotel_id).strip()
    if not hotel_id:
        return False

    with file_lock:
        ensure_file_exists(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            ids = [line.strip() for line in f if line.strip()]

        original_count = len(ids)
        ids = [hid for hid in ids if hid != hotel_id]

        if len(ids) == original_count:
            safe_print(f"[FILE SKIP] Hotel ID {hotel_id} not found in list.")
            return False

        with open(file_path, "w", encoding="utf-8") as f:
            for hid in ids:
                f.write(hid + "\n")

    safe_print(f"[FILE REMOVED] Hotel ID {hotel_id} removed from master list.")
    return True


def append_id_to_missing_file(missing_file_path, hotel_id):
    hotel_id = str(hotel_id).strip()
    if not hotel_id:
        return False

    with file_lock:
        ensure_file_exists(missing_file_path)

        existing_ids = set()
        with open(missing_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    existing_ids.add(line)

        if hotel_id in existing_ids:
            safe_print(
                f"[MISSING SKIP] Hotel ID {hotel_id} already exists in missing file."
            )
            return True

        with open(missing_file_path, "a", encoding="utf-8") as f:
            f.write(hotel_id + "\n")

    safe_print(
        f"[MISSING ADDED] Hotel ID {hotel_id} added to missing_hotel_id_list.txt"
    )
    return True


def move_id_to_missing(master_file_path, missing_file_path, hotel_id):
    hotel_id = str(hotel_id).strip()
    if not hotel_id:
        return False

    with file_lock:
        ensure_file_exists(master_file_path)
        ensure_file_exists(missing_file_path)

        with open(master_file_path, "r", encoding="utf-8") as f:
            ids = [line.strip() for line in f if line.strip()]

        original_count = len(ids)
        updated_ids = [hid for hid in ids if hid != hotel_id]

        if len(updated_ids) != original_count:
            with open(master_file_path, "w", encoding="utf-8") as f:
                for hid in updated_ids:
                    f.write(hid + "\n")
            safe_print(
                f"[MASTER REMOVED] Hotel ID {hotel_id} removed from paximumhotel_master_hotel_id_list.txt"
            )
        else:
            safe_print(
                f"[MASTER SKIP] Hotel ID {hotel_id} not found in paximumhotel_master_hotel_id_list.txt"
            )

        existing_missing_ids = set()
        with open(missing_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    existing_missing_ids.add(line)

        if hotel_id not in existing_missing_ids:
            with open(missing_file_path, "a", encoding="utf-8") as f:
                f.write(hotel_id + "\n")
            safe_print(
                f"[MISSING ADDED] Hotel ID {hotel_id} added to missing_hotel_id_list.txt"
            )
        else:
            safe_print(
                f"[MISSING SKIP] Hotel ID {hotel_id} already exists in missing_hotel_id_list.txt"
            )

    return True


def insert_into_master_table(data):
    if not data["hotel_id"]:
        safe_print("[DB SKIP] Missing hotel_id, skipping insert.")
        return "skipped"

    try:
        with engine.begin() as connection:
            result = connection.execute(UPSERT_QUERY, data)

        if getattr(result, "rowcount", 0) == 0:
            safe_print(
                f"[DB SKIP] Hotel ID {data['hotel_id']} already exists in database."
            )
            return "already_exists"

        safe_print(f"[DB UPSERTED] Hotel ID {data['hotel_id']}")
        return "success"
    except Exception as e:
        safe_print(f"[DB FAILED] Hotel ID {data['hotel_id']}: {e}")
        return "db_failed"


def process_hotel(hotel_id):
    details = get_hotel_details(hotel_id)
    if not details:
        return {"hotel_id": hotel_id, "status": "api_failed"}

    data = normalize_paximumhotel_hotel_details(details)

    if not data["hotel_id"]:
        safe_print(
            f"[MISSING] Missing hotel_id in API response for requested ID {hotel_id}"
        )
        move_id_to_missing(master_hotel_id_list, missing_hotel_id_file, hotel_id)
        return {"hotel_id": hotel_id, "status": "missing_hotel_id"}

    hotel_name = data.get("name") or ""
    country_code = data.get("country_code") or ""

    safe_print(
        f"[PROCESSING] {data['hotel_id']:<12} | {hotel_name[:35]:<35} | {country_code}"
    )

    db_status = insert_into_master_table(data)
    if db_status == "already_exists":
        return {"hotel_id": hotel_id, "status": "already_exists"}
    if db_status == "success":
        return {"hotel_id": hotel_id, "status": "success"}

    return {"hotel_id": hotel_id, "status": "db_failed"}


def main():
    if not all([db_host, db_user, db_password, db_name]):
        raise ValueError(
            "Database environment variables are missing. Check your .env file."
        )

    ensure_file_exists(master_hotel_id_list)
    ensure_file_exists(missing_hotel_id_file)

    with open(master_hotel_id_list, "r", encoding="utf-8") as f:
        hotel_ids = [line.strip() for line in f if line.strip()]

    safe_print(f"📋 Total hotel IDs to process: {len(hotel_ids)}")
    safe_print(f"🚀 Starting concurrent processing with {MAX_WORKERS} workers...")
    safe_print("-" * 100)

    success_count = 0
    api_fail_count = 0
    db_fail_count = 0
    missing_id_count = 0
    already_exists_count = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_hotel_id = {
            executor.submit(process_hotel, hotel_id): hotel_id for hotel_id in hotel_ids
        }

        for idx, future in enumerate(as_completed(future_to_hotel_id), start=1):
            hotel_id = future_to_hotel_id[future]

            try:
                result = future.result()
                status = result["status"]

                if status == "success":
                    success_count += 1
                elif status == "api_failed":
                    api_fail_count += 1
                elif status == "db_failed":
                    db_fail_count += 1
                elif status == "missing_hotel_id":
                    missing_id_count += 1
                elif status == "already_exists":
                    already_exists_count += 1

                if idx % 100 == 0:
                    safe_print(
                        f"-" * 50 + "\n" + f"📊 [PROGRESS] {idx}/{len(hotel_ids)} | "
                        f"✅ Success: {success_count} | "
                        f"❌ API Failed: {api_fail_count} | "
                        f"🗄️ DB Failed: {db_fail_count} | "
                        f"⚠️ Missing hotel_id: {missing_id_count} | "
                        f"⏭️ Already Exists: {already_exists_count}"
                        f"\n" + "-" * 50
                    )

            except Exception as e:
                safe_print(f"💥 [THREAD ERROR] Hotel ID {hotel_id}: {e}")

    safe_print("-" * 100)
    safe_print("🏁 Finished processing all hotel IDs.")
    safe_print(f"✅ Success: {success_count}")
    safe_print(f"❌ API Failed: {api_fail_count}")
    safe_print(f"🗄️ DB Failed: {db_fail_count}")
    safe_print(f"⚠️ Missing hotel_id: {missing_id_count}")
    safe_print(f"⏭️ Already Exists: {already_exists_count}")


if __name__ == "__main__":
    main()

