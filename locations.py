import time
import requests
import csv
from dotenv import load_dotenv
import os

load_dotenv()
# Replace with your Google Places API key
API_KEY = os.environ.get("GOOGLE_API_KEY")

# Initial search locations and radius
INITIAL_LOCATIONS = [
    "33.7490,-84.3880",  # Atlanta center
    "33.8600,-84.4000",  # Northern Atlanta
    "33.6800,-84.4000",  # Southern Atlanta
    "33.7500,-84.3000",  # Eastern Atlanta
    "33.7500,-84.5200",  # Western Atlanta
    "34.0522,-84.2817",  # Alpharetta
    "33.9070,-84.2746",  # Sandy Springs
    "33.6400,-84.4300",  # Hartsfield-Jackson Airport
    "33.5731,-84.5038",  # Union City
    "33.9604,-84.0376",  # Lawrenceville
    "33.9234,-83.9916",  # Snellville
    "33.4511,-84.1469",  # McDonough
    "32.8407,-83.6324",
    "33.4735,-82.0105",  # Augusta
    "32.4609,-84.9877",  # Columbus
    "32.0809,-81.0912",  # Savannah
    "33.9519,-83.3576",  # Athens
]
RADIUS = 10000  # 50 km
TARGET_COUNT = 200  # Target number of unique Waffle House locations

# Google Places API endpoints
PLACES_API_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
GEOCODE_API_URL = "https://maps.googleapis.com/maps/api/geocode/json"

def find_waffle_houses(api_key, location, radius, keyword="Waffle House"):
    """Fetch Waffle Houses near a specific location."""
    results = []
    next_page_token = None

    while True:
        params = {
            "key": api_key,
            "location": location,
            "radius": radius,
            "keyword": keyword,
        }
        if next_page_token:
            params["pagetoken"] = next_page_token
            time.sleep(2)  # Wait for next_page_token to become valid

        response = requests.get(PLACES_API_URL, params=params)
        data = response.json()

        if "results" in data:
            results.extend(data["results"])

        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break

    return results

def deduplicate_results(results):
    """Remove duplicates by place_id."""
    unique_places = {}
    for place in results:
        place_id = place["place_id"]
        if place_id not in unique_places:
            unique_places[place_id] = place
    return list(unique_places.values())

def get_detailed_info(api_key, place):
    """Fetch detailed address and location info."""
    params = {"place_id": place["place_id"], "key": api_key}
    response = requests.get(GEOCODE_API_URL, params=params)
    data = response.json()

    if data.get("results"):
        address_components = data["results"][0].get("address_components", [])
        formatted_address = data["results"][0].get("formatted_address", "")
        geometry = data["results"][0].get("geometry", {}).get("location", {})

        details = {
            "Name": place.get("name"),
            "Type": ", ".join(place.get("types", [])),
            "Address": formatted_address,
            "County": None,
            "City": None,
            "State": None,
            "Zip_code": None,
            "Latitude": geometry.get("lat"),
            "Longitude": geometry.get("lng")
        }
        for component in address_components:
            if "administrative_area_level_2" in component["types"]:
                details["County"] = component["long_name"]
            if "locality" in component["types"]:
                details["City"] = component["long_name"]
            if "administrative_area_level_1" in component["types"]:
                details["State"] = component["short_name"]
            if "postal_code" in component["types"]:
                details["Zip_code"] = component["long_name"]

        return details
    return None

# Main logic to collect 180 unique Waffle House locations
def collect_waffle_houses(api_key, target_count, initial_locations, radius):
    collected_results = []
    search_centers = initial_locations.copy()

    while len(collected_results) < target_count:
        if not search_centers:
            print("Ran out of search centers. Expanding manually.")
            search_centers = [
                f"{float(initial_locations[0].split(',')[0]) + 0.1},{float(initial_locations[0].split(',')[1]) + 0.1}"
            ]

        location = search_centers.pop(0)
        print(f"Searching around {location}...")
        results = find_waffle_houses(api_key, location, radius)
        deduped_results = deduplicate_results(results)
        
        # Add new search points around current location
        for result in deduped_results:
            lat = result["geometry"]["location"]["lat"]
            lng = result["geometry"]["location"]["lng"]
            search_centers.append(f"{lat},{lng}")

        collected_results.extend(deduped_results)
        collected_results = deduplicate_results(collected_results)

        print(f"Collected {len(collected_results)} unique Waffle House locations so far...")

    return collected_results[:target_count]

# Fetch data
waffle_houses = collect_waffle_houses(API_KEY, TARGET_COUNT, INITIAL_LOCATIONS, RADIUS)

# Fetch detailed information and save to CSV
detailed_waffle_houses = []
for waffle_house in waffle_houses:
    details = get_detailed_info(API_KEY, waffle_house)
    if details:
        detailed_waffle_houses.append(details)

# Save to CSV
with open("atlanta_waffle_houses.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=detailed_waffle_houses[0].keys())
    writer.writeheader()
    writer.writerows(detailed_waffle_houses)

print(f"Saved {len(detailed_waffle_houses)} Waffle Houses to atlanta_waffle_houses.csv")