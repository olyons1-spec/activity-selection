import requests

# Your Google Maps API key
API_KEY = "AIzaSyCU2WTx7ohmzUCTDz981pVqC_BG1MfHE9U"

# Your default home location
HOME = "Capital Dock Residence, Dublin 2, Ireland"

def get_travel_time(origin, destination, mode="driving"):
    """
    Get travel time between two locations.

    Args:
        origin: Starting location (address or place name)
        destination: Ending location (address or place name)
        mode: Travel mode - "driving", "transit", "walking", or "bicycling"

    Returns:
        Dictionary with duration, distance, and other info
    """
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    params = {
        "origins": origin,
        "destinations": destination,
        "mode": mode,
        "departure_time": "now",  # For real-time traffic
        "key": API_KEY
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if data["status"] != "OK":
        return {"error": f"API Error: {data['status']}"}

    element = data["rows"][0]["elements"][0]

    if element["status"] != "OK":
        return {"error": f"Route Error: {element['status']}"}

    result = {
        "origin": data["origin_addresses"][0],
        "destination": data["destination_addresses"][0],
        "mode": mode,
        "distance": element["distance"]["text"],
        "duration": element["duration"]["text"]
    }

    # For driving, also get traffic-aware time if available
    if mode == "driving" and "duration_in_traffic" in element:
        result["duration_in_traffic"] = element["duration_in_traffic"]["text"]

    return result


def compare_modes(origin, destination):
    """Compare driving vs transit vs cycling times"""
    print(f"\n{'='*60}")
    print(f"From: {origin}")
    print(f"To:   {destination}")
    print(f"{'='*60}\n")

    # Check driving
    driving = get_travel_time(origin, destination, "driving")
    if "error" not in driving:
        print(f"DRIVING:")
        print(f"   Distance: {driving['distance']}")
        print(f"   Normal time: {driving['duration']}")
        if "duration_in_traffic" in driving:
            print(f"   With current traffic: {driving['duration_in_traffic']}")
    else:
        print(f"DRIVING: {driving['error']}")

    print()

    # Check transit
    transit = get_travel_time(origin, destination, "transit")
    if "error" not in transit:
        print(f"PUBLIC TRANSIT:")
        print(f"   Distance: {transit['distance']}")
        print(f"   Duration: {transit['duration']}")
    else:
        print(f"PUBLIC TRANSIT: {transit['error']}")

    print()

    # Check cycling
    cycling = get_travel_time(origin, destination, "bicycling")
    if "error" not in cycling:
        print(f"CYCLING:")
        print(f"   Distance: {cycling['distance']}")
        print(f"   Duration: {cycling['duration']}")
    else:
        print(f"CYCLING: {cycling['error']}")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    import sys

    # Check travel time from home
    origin = HOME

    # Get destination from command line argument, or use default
    if len(sys.argv) > 1:
        # Join all arguments in case destination has spaces
        destination = " ".join(sys.argv[1:])
        # Add Dublin, Ireland if not already specified
        if "dublin" not in destination.lower() and "ireland" not in destination.lower():
            destination = f"{destination}, Dublin, Ireland"
    else:
        # Default destination
        destination = "IADT College, Dun Laoghaire, Dublin, Ireland"

    # Compare both modes
    compare_modes(origin, destination)
