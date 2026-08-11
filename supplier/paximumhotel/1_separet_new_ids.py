import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# -----------------------------
# Files
# -----------------------------

## local file paths
# CSV_FILE = r"D:\Rokon\ofc_git\new_hotel__get_id\supplier\paximumhotel\paximum-static-data\paximumhotels.csv"
# OUTPUT_FILE = r"D:\Rokon\ofc_git\new_hotel__get_id\supplier\paximumhotel\hotel_id\new_hotel_id_list.txt"

# Remote file paths
CSV_FILE = r"/var/www/ScriptEngine/Python-Application/Content-Create-API/static/read/paximumhotel/paximum-static-data/paximumhotels.csv"
OUTPUT_FILE = r"/var/www/ScriptEngine/Python-Application/New-Hotel-Id-Collection-Function/supplier/paximumhotel/hotel_id/new_hotel_id_list.txt"

TABLE = "s_paximumhotel_master"

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
    pool_size=10,
    max_overflow=20,
)

# -----------------------------
# Load hotel IDs from database
# -----------------------------
print("Loading hotel IDs from database...")

with engine.connect() as conn:
    db_ids = {
        str(row[0]).strip()
        for row in conn.execute(
            text(f"SELECT hotel_id FROM {TABLE} WHERE hotel_id IS NOT NULL")
        )
    }

print(f"Loaded {len(db_ids):,} hotel IDs from database.")

# -----------------------------
# Compare CSV with DB
# -----------------------------
processed = 0
new_count = 0

with open(CSV_FILE, "r", encoding="utf-8-sig") as csv_file, open(
    OUTPUT_FILE, "w", encoding="utf-8"
) as out_file:

    # Skip header
    next(csv_file)

    for line in csv_file:
        processed += 1

        # First column before the first |
        hotel_id = line.split("|", 1)[0].strip()

        if hotel_id and hotel_id not in db_ids:
            out_file.write(hotel_id + "\n")
            new_count += 1

        # Show progress every 100,000 rows
        if processed % 100000 == 0:
            print(
                f"Processed: {processed:,} | " f"New IDs: {new_count:,}",
                end="\r",
                flush=True,
            )

print("\n-----------------------------------")
print(f"Total Processed : {processed:,}")
print(f"New Hotel IDs   : {new_count:,}")
print(f"Output File     : {OUTPUT_FILE}")
print("-----------------------------------")

