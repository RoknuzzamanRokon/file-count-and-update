#!/bin/bash

cd "$(dirname "$0")" || exit 1

SCRIPTS=(
    "agoda/1_get_update_hotel_id_from_supplier.py"
    "agoda/2_get_new_id.py"
    "agoda/3_update_server_with_itt_content_api.py"
    "hotelbeds/1_get_update_hotel_id_from_supplier.py"
    "hotelbeds/2_get_new_id.py"
    "hotelbeds/3_update_server_with_itt_content_api.py"
    "ean/get_update_hotel_and_save_json_into_server.py"
    "hyperguestdirect/1_get_all_id.py"
    "hyperguestdirect/2_get_new_id.py"
    "hyperguestdirect/3_update_server_with_itt_content_api.py"
    "restel/1_get_all_update_hotel.py"
    "restel/2_get_new_id.py"
    "restel/3_update_server_with_itt_content_api.py"
    "innstant/1_get_all_update_hotel.py"
    "innstant/2_get_new_id.py"
    "innstant/3_update_server_with_itt_content_api.py"
)

for script in "${SCRIPTS[@]}"; do
    echo "Running $script"
    pipenv run python3 "$script"
done


