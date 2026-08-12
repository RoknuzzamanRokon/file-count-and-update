import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# -----------------------------
# Validate supplier argument
# -----------------------------
if len(sys.argv) < 2:
    print("Usage: python main.py <supplier>")
    sys.exit(1)

supplier = sys.argv[1].lower()

# -----------------------------
# History Path
# -----------------------------
history_dir = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    "history",
    supplier,
)
os.makedirs(history_dir, exist_ok=True)

today_date = datetime.now()
today_start = today_date.replace(hour=0, minute=0, second=0, microsecond=0)
tomorrow_start = today_start + timedelta(days=1)
today = today_date.strftime("%Y-%m-%d")
history_file = os.path.join(
    history_dir, today_date.strftime("%Y-%m-%d.json")
)


# -----------------------------
# Database Connection
# -----------------------------
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

# -----------------------------
# Paths
# -----------------------------
json_dir = rf"/var/www/Storage-Contents/Hotel-Supplier-Raw-Contents/{supplier}"

save_dir = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "supplier", supplier
)

os.makedirs(save_dir, exist_ok=True)

# Daily per-hotel change-log files: Supplier-Change-Log/<date>/<supplier>/<hotel_id>.jsonl
change_log_dir = os.path.join(
    r"/var/www/Storage-Contents/Supplier-Change-Log",
    today,
    supplier,
)

print(f"Supplier: {supplier}")
print(f"JSON Path: {json_dir}")
print(f"Output Path: {save_dir}")

# -----------------------------
# Get server file list
# -----------------------------
server_ids = set()

if not os.path.exists(json_dir):
    raise FileNotFoundError(f"Folder not found: {json_dir}")

for filename in os.listdir(json_dir):
    if filename.lower().endswith(".json"):
        hotel_id = os.path.splitext(filename)[0]
        server_ids.add(hotel_id)

print(f"Server JSON Count: {len(server_ids)}")

# -----------------------------
# Get DB hotel ids
# -----------------------------
table_name = f"s_{supplier}_master"

query = text(f"""
SELECT hotel_id
FROM {table_name}
WHERE hotel_id IS NOT NULL
""")

db_ids = set()

with engine.connect() as conn:
    result = conn.execute(query)

    for row in result:
        hotel_id = str(row[0]).strip()
        if hotel_id:
            db_ids.add(hotel_id)

print(f"Database Hotel Count: {len(db_ids)}")


# -----------------------------
# Get DB hotel ids created today
# -----------------------------
new_database_query = text(f"""
SELECT hotel_id
FROM {table_name}
WHERE hotel_id IS NOT NULL
  AND created_at >= :today_start
  AND created_at < :tomorrow_start
""")

database_new_ids = set()

with engine.connect() as conn:
    result = conn.execute(
        new_database_query,
        {
            "today_start": today_start,
            "tomorrow_start": tomorrow_start,
        },
    )

    for row in result:
        hotel_id = str(row[0]).strip()
        if hotel_id:
            database_new_ids.add(hotel_id)

database_new_ids = sorted(database_new_ids)

print(f"Database New Today Count: {len(database_new_ids)}")


# -----------------------------
# ITTID Statistics
# -----------------------------
ittid_done_query = text(f"""
SELECT COUNT(*)
FROM {table_name}
WHERE ittid IS NOT NULL
""")

pending_ittid_query = text(f"""
SELECT COUNT(*)
FROM {table_name}
WHERE ittid IS NULL
""")

with engine.connect() as conn:
    total_ittid_done = conn.execute(ittid_done_query).scalar()
    pending_ittid = conn.execute(pending_ittid_query).scalar()

print(f"ITTID Done: {total_ittid_done}")
print(f"Pending ITTID: {pending_ittid}")


# -----------------------------
# Compare
# -----------------------------
server_not_db = sorted(server_ids - db_ids)
db_not_server = sorted(db_ids - server_ids)

# -----------------------------
# Update Hotel IDs (existing hotels flagged as updated by supplier)
# -----------------------------
update_server_ids = set()

if os.path.isdir(change_log_dir):
    for filename in os.listdir(change_log_dir):
        if filename.lower().endswith(".jsonl"):
            hotel_id = os.path.splitext(filename)[0].strip()
            if hotel_id:
                update_server_ids.add(hotel_id)

print(f"Update Hotel IDs (server): {len(update_server_ids)}")

# -----------------------------
# Today's Accumulated Snapshot IDs
# -----------------------------
daily_server_not_db = server_not_db
daily_database_new_ids = database_new_ids
daily_update_server_ids = sorted(update_server_ids)

if os.path.exists(history_file):
    with open(history_file, "r", encoding="utf-8") as f:
        existing_snapshot = json.load(f)

    daily_server_not_db = sorted(
        set(existing_snapshot.get("new_hotels_server_id", [])) | set(server_not_db)
    )
    daily_database_new_ids = sorted(
        set(existing_snapshot.get("new_hotels_database_id", []))
        | set(database_new_ids)
    )
    daily_update_server_ids = sorted(
        set(existing_snapshot.get("update_hotels_server_id", []))
        | update_server_ids
    )

# -----------------------------
# Save Files
# -----------------------------
files_to_write = {
    "server_file_list.txt": sorted(server_ids),
    "db_hotel_id_list.txt": sorted(db_ids),
    "server_present_but_db_id_not_present_list.txt": server_not_db,
    "db_present_but_server_json_not_present.txt": db_not_server,
}

for filename, data in files_to_write.items():
    file_path = os.path.join(save_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(f"{item}\n")

    print(f"Saved: {file_path} ({len(data)} records)")

print("\nDone.")


# -----------------------------
# Snapshot Counts
# -----------------------------
last_day_server = len(daily_server_not_db)
last_day_database = len(daily_database_new_ids)
last_7_days_server = 0
last_7_days_database = 0

for day_offset in range(1, 8):
    previous_file = os.path.join(
        history_dir,
        (today_date - timedelta(days=day_offset)).strftime("%Y-%m-%d.json"),
    )

    if not os.path.exists(previous_file):
        continue

    with open(previous_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    last_7_days_server += len(data.get("new_hotels_server_id", []))
    last_7_days_database += len(data.get("new_hotels_database_id", []))


# -----------------------------
# Update Summary Table
# -----------------------------
summary_query = text("""
INSERT INTO zz_masterdata_summary (
    supplier,
    total_hotels_server,
    total_hotels_database,
    new_hotels_server,
    new_hotels_database,
    update_hotels_server,
    total_ittid_done,
    pending_ittid,
    last_day_add_hotel_id_into_server,
    last_day_add_hotel_id_into_database,
    last_7_days_add_hotel_id_into_server,
    last_7_days_add_hotel_id_into_database
)
VALUES (
    :supplier,
    :server_total,
    :db_total,
    :new_server,
    :new_db,
    :update_server,
    :ittid_done,
    :pending_ittid,
    :last_day_server,
    :last_day_database,
    :last_7_days_server,
    :last_7_days_database
)
ON DUPLICATE KEY UPDATE
    total_hotels_server = VALUES(total_hotels_server),
    total_hotels_database = VALUES(total_hotels_database),
    new_hotels_server = VALUES(new_hotels_server),
    new_hotels_database = VALUES(new_hotels_database),
    update_hotels_server = VALUES(update_hotels_server),
    total_ittid_done = VALUES(total_ittid_done),
    pending_ittid = VALUES(pending_ittid),
    last_day_add_hotel_id_into_server = VALUES(last_day_add_hotel_id_into_server),
    last_day_add_hotel_id_into_database = VALUES(last_day_add_hotel_id_into_database),
    last_7_days_add_hotel_id_into_server = VALUES(last_7_days_add_hotel_id_into_server),
    last_7_days_add_hotel_id_into_database = VALUES(last_7_days_add_hotel_id_into_database),
    updated_at = CURRENT_TIMESTAMP
""")

with engine.begin() as conn:
    conn.execute(
        summary_query,
        {
            "supplier": supplier,
            "server_total": len(server_ids),
            "db_total": len(db_ids),
            "new_server": len(daily_server_not_db),
            "new_db": len(daily_database_new_ids),
            "update_server": len(daily_update_server_ids),
            "ittid_done": total_ittid_done,
            "pending_ittid": pending_ittid,
            "last_day_server": last_day_server,
            "last_day_database": last_day_database,
            "last_7_days_server": last_7_days_server,
            "last_7_days_database": last_7_days_database,
        },
    )

print("\nDone.")
print("Summary table updated.")

snapshot = {
    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "supplier": supplier,
    "server_total": len(server_ids),
    "database_total": len(db_ids),
    "ittid_done": total_ittid_done,
    "pending_ittid": pending_ittid,
    "new_hotels_server": len(daily_server_not_db),
    "new_hotels_server_id": daily_server_not_db,
    "new_hotels_database": len(daily_database_new_ids),
    "new_hotels_database_id": daily_database_new_ids,
    "update_hotels_server": len(daily_update_server_ids),
    "update_hotels_server_id": daily_update_server_ids,
}

with open(history_file, "w", encoding="utf-8") as f:
    json.dump(snapshot, f, indent=4)

print(f"History saved: {history_file}")

