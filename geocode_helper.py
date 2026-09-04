import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
# Nominatim's usage policy requires a real identifying User-Agent — replace
# the email below with yours, or requests can get rate-limited/blocked.
HEADERS = {"User-Agent": "AnaajBot/1.0 (contact: ankushshenoy07@gmail.com)"}


def reverse_geocode(lat, lon):
    """Converts lat/lon into a human-readable address.
    Returns None on failure so callers can fall back to raw coordinates."""
    if lat is None or lon is None:
        return None
    try:
        params = {
            "format": "json",
            "lat": lat,
            "lon": lon,
            "zoom": 18,
            "addressdetails": 1
        }
        response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get("display_name")
    except (requests.RequestException, ValueError) as e:
        print("Reverse geocoding failed:", e)
        return None