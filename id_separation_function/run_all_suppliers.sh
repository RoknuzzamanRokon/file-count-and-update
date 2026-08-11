#!/bin/bash

# Stop if any command fails
set -e

SUPPLIERS=(
    agoda
    amadeushotel
    didahotel
    dotw
    ean
    ebookinghotel
    goglobal
    grnconnect
    hotelbeds
    hotelston
    hyperguestdirect
    illusionshotel
    innstant
    juniperhotel
    kiwihotel
    mgholiday
    paximumhotel
    rakuten
    ratehawkhotel
    restel
    rnrhotel
    roomerang
    stuba
    tbohotel
    travelrobothotel
)

# Change to the directory containing main.py
cd /var/www/ScriptEngine/Python-Application/New-Hotel-Id-Collection-Function/id_separation_function

echo "==========================================="
echo "Started at: $(date)"
echo "==========================================="

for supplier in "${SUPPLIERS[@]}"; do
    echo
    echo "==========================================="
    echo "Running supplier: $supplier"
    echo "Start Time: $(date)"
    echo "==========================================="

    pipenv run python main.py "$supplier"
    
    echo "Finished: $supplier"
    echo "End Time: $(date)"
done

echo
echo "==========================================="
echo "All suppliers completed."
echo "Finished at: $(date)"
echo "==========================================="
