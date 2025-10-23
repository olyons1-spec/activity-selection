"""
Cycling Availability Checker
Checks weather conditions for outdoor cycling
"""
from datetime import datetime, timedelta
import requests

# Your Google Maps API key
API_KEY = "AIzaSyCU2WTx7ohmzUCTDz981pVqC_BG1MfHE9U"

# Dublin coordinates (starting point)
DUBLIN_LAT = 53.3498
DUBLIN_LON = -6.2603

# Typical cycling routes and durations
ROUTES = {
    'short': {'name': 'City Loop', 'duration_minutes': 60, 'location': 'Dublin City'},
    'medium': {'name': 'Phoenix Park Circuit', 'duration_minutes': 90, 'location': 'Phoenix Park'},
    'long': {'name': 'Coastal Route', 'duration_minutes': 120, 'location': 'Dublin to Howth'}
}


def get_current_weather(latitude=DUBLIN_LAT, longitude=DUBLIN_LON):
    """Get current weather conditions"""
    base_url = "https://weather.googleapis.com/v1/currentConditions:lookup"

    params = {
        "key": API_KEY,
        "location.latitude": latitude,
        "location.longitude": longitude,
        "unitsSystem": "METRIC"
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass

    return None


def check_cycling_availability(route_type='medium'):
    """
    Check if conditions are good for cycling

    Args:
        route_type: 'short', 'medium', or 'long'

    Returns:
        Dictionary with cycling availability info
    """
    route = ROUTES.get(route_type, ROUTES['medium'])

    weather = get_current_weather()

    if not weather:
        return {
            'available': False,
            'error': 'Unable to fetch weather data'
        }

    # Extract weather info
    condition = weather.get('weatherCondition', {}).get('description', {}).get('text', 'Unknown')
    temp = weather.get('temperature', {}).get('degrees', 0)
    feels_like = weather.get('feelsLikeTemperature', {}).get('degrees', 0)
    wind_speed = weather.get('wind', {}).get('speed', {}).get('value', 0)
    wind_dir = weather.get('wind', {}).get('direction', {}).get('cardinal', 'N/A')
    rain_prob = weather.get('precipitation', {}).get('probability', {}).get('percent', 0)
    visibility = weather.get('visibility', {}).get('distance', 10)

    # Assess cycling conditions
    good_for_cycling = True
    warnings = []
    rating = "EXCELLENT"

    # Temperature check
    if feels_like < 0:
        warnings.append("Very cold - wear warm layers")
        rating = "POOR"
        good_for_cycling = False
    elif feels_like < 5:
        warnings.append("Cold - layer up")
        rating = "FAIR" if rating == "EXCELLENT" else rating
    elif feels_like > 28:
        warnings.append("Very hot - stay hydrated")
        rating = "FAIR" if rating == "EXCELLENT" else rating

    # Wind check
    if wind_speed > 40:
        warnings.append(f"Very windy ({wind_speed} km/h) - dangerous for cycling")
        rating = "POOR"
        good_for_cycling = False
    elif wind_speed > 25:
        warnings.append(f"Windy ({wind_speed} km/h) - challenging ride")
        rating = "FAIR" if rating == "EXCELLENT" else rating

    # Rain check
    if rain_prob > 70:
        warnings.append(f"High rain probability ({rain_prob}%)")
        rating = "POOR"
        good_for_cycling = False
    elif rain_prob > 40:
        warnings.append(f"Moderate rain chance ({rain_prob}%)")
        rating = "FAIR" if rating == "EXCELLENT" else rating

    # Visibility check
    if visibility < 2:
        warnings.append(f"Poor visibility ({visibility} km)")
        rating = "POOR"
        good_for_cycling = False

    # Check for specific bad conditions
    bad_conditions = ['heavy rain', 'thunderstorm', 'snow', 'ice', 'freezing']
    if any(bad in condition.lower() for bad in bad_conditions):
        warnings.append(f"Bad weather: {condition}")
        rating = "POOR"
        good_for_cycling = False

    # Final assessment
    if rating == "EXCELLENT":
        assessment = "Perfect conditions for cycling!"
    elif rating == "FAIR":
        assessment = "Conditions are okay - be prepared"
    else:
        assessment = "Not recommended for cycling today"

    return {
        'available': good_for_cycling,
        'route': route['name'],
        'duration_minutes': route['duration_minutes'],
        'location': route['location'],
        'condition': condition,
        'temperature': temp,
        'feels_like': feels_like,
        'wind_speed': wind_speed,
        'wind_direction': wind_dir,
        'rain_probability': rain_prob,
        'visibility': visibility,
        'rating': rating,
        'warnings': warnings,
        'assessment': assessment
    }


def display_cycling_availability(route_type='medium'):
    """Display cycling availability in a nice format"""

    print("\n" + "="*80)
    print("CYCLING AVAILABILITY CHECKER")
    print("="*80)
    print()

    result = check_cycling_availability(route_type)

    if 'error' in result:
        print(f"Error: {result['error']}")
        return result

    print(f"Route: {result['route']}")
    print(f"Location: {result['location']}")
    print(f"Duration: ~{result['duration_minutes']} minutes")
    print()

    if result['available']:
        print("Status: AVAILABLE [OK]")
    else:
        print("Status: NOT RECOMMENDED [X]")

    print()
    print("Current conditions:")
    print(f"  {result['condition']}")
    print(f"  Temperature: {result['temperature']}°C (feels like {result['feels_like']}°C)")
    print(f"  Wind: {result['wind_speed']} km/h {result['wind_direction']}")
    print(f"  Rain probability: {result['rain_probability']}%")
    print(f"  Visibility: {result['visibility']} km")
    print()
    print(f"Rating: {result['rating']}")
    print(f"Assessment: {result['assessment']}")

    if result['warnings']:
        print()
        print("Warnings:")
        for warning in result['warnings']:
            print(f"  ! {warning}")

    print()
    print("Available routes:")
    print("  - short:  City Loop (~60 min)")
    print("  - medium: Phoenix Park Circuit (~90 min)")
    print("  - long:   Coastal Route to Howth (~120 min)")

    print("\n" + "="*80 + "\n")

    return result


if __name__ == "__main__":
    import sys

    route_type = 'medium'
    if len(sys.argv) > 1:
        route_type = sys.argv[1].lower()
        if route_type not in ROUTES:
            print(f"Unknown route type: {route_type}")
            print("Available: short, medium, long")
            sys.exit(1)

    display_cycling_availability(route_type)
