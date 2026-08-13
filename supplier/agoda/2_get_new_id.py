import os

# Save directory inside the supplier/agoda folder
save_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "hotel_id")
os.makedirs(save_dir, exist_ok=True)

# Project root is two levels up from this file (.. / ..)
project_root = os.path.abspath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "..")
)

# Define paths
a_path = os.path.join(project_root, "all_hotel_count_id_list", "agoda_hotel_id_list.txt")
b_path = os.path.join(save_dir, "update_hotel_id_list.txt")
c_path = os.path.join(save_dir, "new_hotel_id_list.txt")
d_path = os.path.join(save_dir, "only_update_hotel_id.txt")

# Build `agoda_hotel_id_list.txt` from a folder of JSON files (filenames like 123.json)
# Default source folder: project_root/agoda (can be changed to an absolute path)
# Prefer an explicit folder if it exists (your provided path)
explicit_folder = "/var/www/Storage-Contents/Hotel-Supplier-Raw-Contents/agoda"
explicit_folder = os.path.abspath(explicit_folder)
if os.path.isdir(explicit_folder):
    default_source_folder = explicit_folder
else:
    default_source_folder = os.path.join(project_root, "agoda")

# Allow overriding the source folder via environment variable `AGODA_JSON_FOLDER`
source_folder = os.environ.get("AGODA_JSON_FOLDER", default_source_folder)


def build_global_mapping_from_json_folder(source_folder, dest_file):
    if not os.path.isdir(source_folder):
        return False
    ids = set()
    for name in os.listdir(source_folder):
        if name.lower().endswith(".json"):
            stem = os.path.splitext(name)[0].strip()
            if stem:
                ids.add(stem)
    if not ids:
        return False
    os.makedirs(os.path.dirname(dest_file), exist_ok=True)

    # Sort numerically when possible
    def sort_key(x):
        return int(x) if x.isdigit() else x

    with open(dest_file, "w", encoding="utf-8") as f:
        for id in sorted(ids, key=sort_key):
            f.write(id + "\n")
    return True


# Attempt to (re)build the global mapping file from JSON filenames before continuing
try:
    built = build_global_mapping_from_json_folder(source_folder, a_path)
    if built:
        print(f"Built global mapping file from {source_folder} -> {a_path}")
    else:
        print(
            f"No JSON files found in {source_folder}; using existing {a_path} if present"
        )
except Exception as exc:
    print(f"Warning: failed to build global mapping from {source_folder}: {exc}")


# Helper to read an ID file into a set (returns empty set if file missing)
def read_id_set(path):
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


set_a = read_id_set(a_path)
set_b = read_id_set(b_path)

# Compute difference: c = b - a
c = set_b - set_a

# Write to file, sorted numerically
with open(c_path, "w", encoding="utf-8") as f:
    for id in sorted(c, key=int):
        f.write(id + "\n")

print(f"New hotel IDs saved to {c_path}")

# Compute only-update IDs: those in update list but not in new list
# Formula: only_update = update_hotel_id_list.txt - new_hotel_id_list.txt
only_update = set_b - c

# Write only-update IDs
with open(d_path, "w", encoding="utf-8") as f:
    for id in sorted(only_update, key=int):
        f.write(id + "\n")

print(f"Only-update hotel IDs saved to {d_path}")

