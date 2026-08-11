import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# ---------- DB CONFIG ----------
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

supplier = "ratehawkhotel"
INPUT_FILE = "ratehawk_old_hotel_id_1.txt"
BATCH_SIZE = 1000


def read_hotel_ids(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


hotel_ids = read_hotel_ids(INPUT_FILE)

print(f"Total Hotel IDs: {len(hotel_ids)}")



BATCH_SIZE = 1000

with engine.begin() as conn:
    deleted = 0

    for i in range(0, len(hotel_ids), BATCH_SIZE):
        batch = hotel_ids[i:i+BATCH_SIZE]

        placeholders = ", ".join([f":id{j}" for j in range(len(batch))])

        query = text(f"""
            DELETE FROM mapping
            WHERE supplier = :supplier
            AND hotel_id IN ({placeholders})
        """)

        params = {"supplier": supplier}
        params.update({f"id{j}": hid for j, hid in enumerate(batch)})

        result = conn.execute(query, params)
        deleted += result.rowcount

        print(
            f"Batch {(i//BATCH_SIZE)+1} | "
            f"Processed: {min(i+BATCH_SIZE, len(hotel_ids))}/{len(hotel_ids)} | "
            f"Deleted: {deleted}"
        )

print(f"\nDone. Total deleted rows: {deleted}")
