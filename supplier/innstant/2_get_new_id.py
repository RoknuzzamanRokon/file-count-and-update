import os

# Save directory
save_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "hotel_id")
os.makedirs(save_dir, exist_ok=True)

# Project root
project_root = os.path.abspath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "..")
)

# Files
a_path = os.path.join(
    project_root,
    "all_hotel_count_id_list",
    "master_innstant_hotel_id_list_n.txt",
)

b_path = os.path.join(save_dir, "update_hotel_id_list.txt")
c_path = os.path.join(save_dir, "new_hotel_id_list.txt")

# Folder containing Innstant JSON files
source_folder = "/var/www/Storage-Contents/Hotel-Supplier-Raw-Contents/innstant"


def build_master_file(json_folder, output_file):
    """Create master_innstant_hotel_id_list_n.txt from JSON filenames."""
    if not os.path.isdir(json_folder):
        print(f"JSON folder not found: {json_folder}")
        return False

    hotel_ids = set()

    for filename in os.listdir(json_folder):
        if filename.lower().endswith(".json"):
            hotel_id = os.path.splitext(filename)[0].strip()
            if hotel_id:
                hotel_ids.add(hotel_id)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        for hotel_id in sorted(hotel_ids):
            f.write(f"{hotel_id}\n")

    print(f"Created master file: {output_file}")
    print(f"Total IDs: {len(hotel_ids)}")
    return True


def read_id_set(path):
    if not os.path.exists(path):
        return set()

    with open(path, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


# Step 1: Create master file from JSON filenames
build_master_file(source_folder, a_path)

# Step 2: Read files
master_ids = read_id_set(a_path)
update_ids = read_id_set(b_path)

# Step 3: Find new hotel IDs
new_ids = update_ids - master_ids

# Step 4: Save new hotel IDs
with open(c_path, "w", encoding="utf-8") as f:
    for hotel_id in sorted(new_ids):
        f.write(f"{hotel_id}\n")

print(f"Master IDs : {len(master_ids)}")
print(f"Update IDs : {len(update_ids)}")
print(f"New IDs    : {len(new_ids)}")
print(f"Saved to   : {c_path}")

