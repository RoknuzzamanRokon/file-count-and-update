from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import os
import time

raw_json_file = r"/var/www/Storage-Contents/Hotel-Supplier-Raw-Contents/agoda"


REPLACEMENTS = {
    "s=312x": "s=996x",
    "max500": "max900",
}


def process_file(json_file: Path):
    """
    Process a single JSON file.

    Returns:
        (updated_file, replacement_count)
    """
    try:
        content = json_file.read_text(encoding="utf-8")

        # Fast skip if no target strings exist
        if all(old not in content for old in REPLACEMENTS):
            return False, 0

        new_content = content
        replacement_count = 0

        for old, new in REPLACEMENTS.items():
            count = new_content.count(old)
            if count:
                new_content = new_content.replace(old, new)
                replacement_count += count

        if replacement_count:
            json_file.write_text(new_content, encoding="utf-8")
            print(f"✔ {json_file.name}: {replacement_count} replacement(s)")
            return True, replacement_count

        return False, 0

    except Exception as e:
        print(f"✖ Error processing {json_file.name}: {e}")
        return False, 0


def update_image_size(json_folder: str):
    folder = Path(json_folder)

    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    files = list(folder.glob("*.json"))

    print(f"Found {len(files)} JSON files.")
    print(f"Using {os.cpu_count() * 2} worker threads...\n")

    updated_files = 0
    updated_values = 0

    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=os.cpu_count() * 2) as executor:
        for updated, replacements in executor.map(process_file, files):
            if updated:
                updated_files += 1
                updated_values += replacements

    elapsed = time.perf_counter() - start

    print("\n" + "=" * 60)
    print("Completed")
    print("=" * 60)
    print(f"Total files scanned      : {len(files)}")
    print(f"Files updated            : {updated_files}")
    print(f"Total replacements       : {updated_values}")
    print(f"Execution time           : {elapsed:.2f} seconds")


if __name__ == "__main__":
    update_image_size(raw_json_file)
