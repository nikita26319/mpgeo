import requests, psycopg2, os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur  = conn.cursor()

# Overpass API query — fetches all hospitals in Madhya Pradesh
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
QUERY = """
[out:json][timeout:60];
area["name"="Madhya Pradesh"]["admin_level"="4"]->.mp;
(
  node["amenity"="hospital"](area.mp);
  node["amenity"="clinic"](area.mp);
  node["healthcare"="hospital"](area.mp);
);
out body;
"""

print("Fetching hospitals from OpenStreetMap...")
resp = requests.post(OVERPASS_URL, data={"data": QUERY})
print("Status Code:", resp.status_code)
print("Response Preview:", resp.text[:500])
data = resp.json()
elements = data.get("elements", [])
print(f"Found {len(elements)} hospitals from OSM")

# District mapping by coordinates (rough bounding boxes for MP districts)
def guess_district(lat, lon):
    if 23.0 <= lat <= 23.6 and 77.2 <= lon <= 77.7: return "Bhopal"
    if 22.5 <= lat <= 23.0 and 75.6 <= lon <= 76.2: return "Indore"
    if 26.0 <= lat <= 26.5 and 77.8 <= lon <= 78.5: return "Gwalior"
    if 22.8 <= lat <= 23.4 and 79.7 <= lon <= 80.2: return "Jabalpur"
    if 23.7 <= lat <= 24.2 and 78.5 <= lon <= 79.2: return "Sagar"
    if 24.3 <= lat <= 24.8 and 81.0 <= lon <= 81.6: return "Rewa"
    if 23.0 <= lat <= 23.5 and 75.5 <= lon <= 76.0: return "Ujjain"
    if 22.5 <= lat <= 23.0 and 77.5 <= lon <= 78.0: return "Narmadapuram"
    if 24.5 <= lat <= 25.0 and 74.8 <= lon <= 75.4: return "Mandsaur"
    if 21.8 <= lat <= 22.4 and 76.3 <= lon <= 77.0: return "Harda"
    if 22.0 <= lat <= 22.6 and 78.5 <= lon <= 79.2: return "Chhindwara"
    if 23.5 <= lat <= 24.0 and 80.8 <= lon <= 81.5: return "Satna"
    if 25.0 <= lat <= 25.6 and 78.3 <= lon <= 79.0: return "Tikamgarh"
    return "Madhya Pradesh"

def guess_type(tags):
    name = (tags.get("name") or "").lower()
    t    = (tags.get("healthcare") or tags.get("amenity") or "").lower()
    if "phc" in name or "primary health" in name: return "PHC"
    if "chc" in name or "community health" in name: return "CHC"
    if "aiims" in name or "medical college" in name: return "Government"
    if "civil" in name or "district" in name or "sadar" in name: return "Government"
    if "private" in name or tags.get("operator:type") == "private": return "Private"
    if t == "hospital": return "Government"
    return "Government"

def guess_beds(tags, htype):
    beds = tags.get("beds")
    if beds:
        try: return int(beds)
        except: pass
    if htype == "PHC":        return 6
    if htype == "CHC":        return 30
    if htype == "Government": return 100
    if htype == "Private":    return 50
    return 20

inserted = 0
skipped  = 0

for el in elements:
    lat  = el.get("lat")
    lon  = el.get("lon")
    tags = el.get("tags", {})
    name = tags.get("name") or tags.get("name:en") or tags.get("name:hi")

    if not lat or not lon or not name:
        skipped += 1
        continue

    htype    = guess_type(tags)
    district = guess_district(lat, lon)
    beds     = guess_beds(tags, htype)

    try:
        cur.execute("""
            INSERT INTO hospitals (name, type, beds, district, geom)
            VALUES (%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            ON CONFLICT DO NOTHING
        """, (name, htype, beds, district, lon, lat))
        inserted += 1
    except Exception as e:
        conn.rollback()
        skipped += 1
        continue

conn.commit()
print(f"Inserted {inserted} hospitals | Skipped {skipped}")
print(f"Total hospitals now: {cur.execute('SELECT COUNT(*) FROM hospitals') or ''}")
cur.execute("SELECT COUNT(*) FROM hospitals")
print(f"Total in DB: {cur.fetchone()[0]}")
cur.close()
conn.close()