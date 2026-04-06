import os, requests
from dotenv import load_dotenv

load_dotenv()

ORS_KEY = os.getenv("ORS_API_KEY")

def geocode_location(place_name: str) -> tuple[float, float] | None:
    """
    Convert a place name to (lat, lon) using Nominatim.
    e.g. "Collectorate Bhopal" -> (23.2599, 77.4126)
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": f"{place_name}, Madhya Pradesh, India",
        "format": "json",
        "limit": 1,
        "countrycodes": "in"
    }
    headers = {"User-Agent": "MPGeoPortal/1.0"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        results = resp.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None


def get_route(origin_lon, origin_lat, dest_lon, dest_lat) -> dict | None:
    """
    Get driving route between two points using OpenRouteService.
    Returns GeoJSON LineString + distance/duration.
    """
    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    headers = {
        "Authorization": ORS_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "coordinates": [
            [origin_lon, origin_lat],
            [dest_lon,   dest_lat]
        ]
    }
    try:
        resp = requests.post(url, json=body, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            feature  = data["features"][0]
            props    = feature["properties"]["summary"]
            return {
                "geojson":      feature["geometry"],
                "distance_km":  round(props["distance"] / 1000, 1),
                "duration_min": round(props["duration"] / 60, 0)
            }
        else:
            print(f"ORS error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Routing error: {e}")
    return None