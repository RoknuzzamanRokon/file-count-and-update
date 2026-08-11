import pandas as pd
import os

# Excel file
input_file_path = os.path.join(
    os.path.dirname(__file__), "Top_hotels_with_availability_ratio.xlsx"
)

# Output txt file
save_dir = os.path.join(os.path.dirname(__file__), "hotel_id")
os.makedirs(save_dir, exist_ok=True)

save_file_path = os.path.join(save_dir, "update_hotel_id_list.txt")

# Read Excel
df = pd.read_excel(input_file_path)

# Column name
column_name = "ratehawk id"

# Write hotel IDs to txt
with open(save_file_path, "w", encoding="utf-8") as f:
    for hotel_id in df[column_name].dropna():
        f.write(f"{str(hotel_id).strip()}\n")

print(f"Saved {len(df[column_name].dropna())} hotel IDs to {save_file_path}")

