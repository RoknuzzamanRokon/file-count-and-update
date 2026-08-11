import urllib.parse
import requests
import xml.etree.ElementTree as ET
import os

base_dir = os.path.abspath(os.path.dirname(__file__))
output_file = os.path.join(base_dir, "hotel_id", "update_hotel_id_list.txt")


# XML data
xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<peticion>
  <tipo>17</tipo>
  <nombre>Servicio de listado de hoteles</nombre>
  <agencia>Agencia prueba</agencia>
</peticion>"""

# URL-encode the XML data
encoded_xml = urllib.parse.quote(xml_data)

# Construct the URL with the encoded XML
url = f"http://xml.hotelresb2b.com/xml/listen_xml.jsp?codigousu=ZVYE&clausu=xml514142&afiliacio=RS&secacc=151003&xml={encoded_xml}"

headers = {"Cookie": "JSESSIONID=aaaodjlEZaLhM_vAad2xz"}

response = requests.get(url, headers=headers)

# Parse the XML response
root = ET.fromstring(response.text)

# Find all hotel elements and extract codpobhot
hotel_ids = []
for hotel in root.findall(".//hotel"):
    codpobhot = hotel.find("codpobhot")
    if codpobhot is not None and codpobhot.text:
        hotel_ids.append(codpobhot.text.strip())


def format_hotel_id(hotel_id):
    if not hotel_id.isdigit():
        raise ValueError(f"Hotel ID is not numeric: {hotel_id}")

    if len(hotel_id) > 6:
        raise ValueError(f"Hotel ID is greater than 6 digits: {hotel_id}")

    return hotel_id.ljust(6, "0")

# Write to file
with open(output_file, "w") as f:
    for hotel_id in hotel_ids:
        f.write(format_hotel_id(hotel_id) + "\n")

print("Hotel IDs saved to update_hotel_id.txt")

