import requests
from datetime import datetime, timedelta

# Your Google Maps API key (same one works for Weather API)
API_KEY = "AIzaSyCU2WTx7ohmzUCTDz981pVqC_BG1MfHE9U"

# Dublin coordinates (Capital Dock area)
DUBLIN_LAT = 53.3498
DUBLIN_LON = -6.2603

# Wicklow town coordinates
WICKLOW_LAT = 52.9808
WICKLOW_LON = -6.0433


def get_current_weather(latitude, longitude, units="metric"):
    """
    Get current weather conditions for a location.

    Args:
        latitude: Location latitude
        longitude: Location longitude
        units: "metric" (default) or "imperial"

    Returns:
        Dictionary with current weather data
    """
    base_url = "https://weather.googleapis.com/v1/currentConditions:lookup"

    params = {
        "key": API_KEY,
        "location.latitude": latitude,
        "location.longitude": longitude,
        "unitsSystem": units.upper()
    }

    response = requests.get(base_url, params=params)

    if response.status_code != 200:
        return {"error": f"API Error: {response.status_code} - {response.text}"}

    data = response.json()
    return data


def get_daily_forecast(latitude, longitude, days=5, units="metric"):
    """
    Get daily weather forecast for a location.

    Args:
        latitude: Location latitude
        longitude: Location longitude
        days: Number of days to forecast (1-10)
        units: "metric" (default) or "imperial"

    Returns:
        Dictionary with forecast data
    """
    base_url = "https://weather.googleapis.com/v1/forecast/days:lookup"

    params = {
        "key": API_KEY,
        "location.latitude": latitude,
        "location.longitude": longitude,
        "days": days,
        "unitsSystem": units.upper()
    }

    response = requests.get(base_url, params=params)

    if response.status_code != 200:
        return {"error": f"API Error: {response.status_code} - {response.text}"}

    data = response.json()
    return data


def display_current_weather(location_name, latitude, longitude):
    """Display current weather in a nice format"""
    print(f"\n{'='*60}")
    print(f"CURRENT WEATHER: {location_name}")
    print(f"{'='*60}\n")

    weather = get_current_weather(latitude, longitude)

    if "error" in weather:
        print(f"Error: {weather['error']}")
        return

    # Extract and display key information
    condition = weather.get('weatherCondition', {}).get('description', {}).get('text', 'Unknown')
    temp = weather.get('temperature', {}).get('degrees', 'N/A')
    feels_like = weather.get('feelsLikeTemperature', {}).get('degrees', 'N/A')
    humidity = weather.get('relativeHumidity', 'N/A')
    wind_speed = weather.get('wind', {}).get('speed', {}).get('value', 'N/A')
    wind_dir = weather.get('wind', {}).get('direction', {}).get('cardinal', 'N/A')
    rain_prob = weather.get('precipitation', {}).get('probability', {}).get('percent', 0)
    uv = weather.get('uvIndex', 'N/A')
    visibility = weather.get('visibility', {}).get('distance', 'N/A')
    cloud_cover = weather.get('cloudCover', 'N/A')

    print(f"Condition: {condition}")
    print(f"Temperature: {temp}°C (feels like {feels_like}°C)")
    print(f"Humidity: {humidity}%")
    print(f"Wind: {wind_speed} km/h {wind_dir}")
    print(f"Rain Probability: {rain_prob}%")
    print(f"UV Index: {uv}")
    print(f"Cloud Cover: {cloud_cover}%")
    print(f"Visibility: {visibility} km")

    # Show 24hr history if available
    history = weather.get('currentConditionsHistory', {})
    if history:
        temp_change = history.get('temperatureChange', {}).get('degrees', 0)
        max_temp = history.get('maxTemperature', {}).get('degrees', 'N/A')
        min_temp = history.get('minTemperature', {}).get('degrees', 'N/A')
        rainfall_24h = history.get('qpf', {}).get('quantity', 0)

        print(f"\nLast 24 Hours:")
        print(f"  Temp Range: {min_temp}°C to {max_temp}°C (change: {temp_change:+.1f}°C)")
        print(f"  Rainfall: {rainfall_24h} mm")

    print(f"\n{'='*60}\n")


def get_historical_rainfall(latitude, longitude, days_back=7):
    """
    Get historical rainfall data using Open-Meteo API (FREE, no key needed!)

    Args:
        latitude: Location latitude
        longitude: Location longitude
        days_back: Number of days to look back (default 7)

    Returns:
        Dictionary with historical rainfall data
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    # Format dates for API
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    # Open-Meteo API endpoint
    base_url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_str,
        "end_date": end_str,
        "hourly": "precipitation",
        "timezone": "auto"
    }

    response = requests.get(base_url, params=params)

    if response.status_code != 200:
        return {"error": f"API Error: {response.status_code} - {response.text}"}

    data = response.json()
    return data


def calculate_ground_saturation(latitude, longitude, days_back=7):
    """
    Calculate ground saturation level based on recent rainfall.

    Args:
        latitude: Location latitude
        longitude: Location longitude
        days_back: Number of days to analyze (default 7)

    Returns:
        Dictionary with rainfall totals and ground condition assessment
    """
    rainfall_data = get_historical_rainfall(latitude, longitude, days_back)

    if "error" in rainfall_data:
        return rainfall_data

    # Extract precipitation data
    hourly = rainfall_data.get('hourly', {})
    precipitation = hourly.get('precipitation', [])

    if not precipitation:
        return {"error": "No precipitation data available"}

    # Calculate total rainfall
    total_rainfall = sum(p for p in precipitation if p is not None)

    # Calculate recent rainfall (last 24 hours gets more weight)
    hours_24 = precipitation[-24:] if len(precipitation) >= 24 else precipitation
    rainfall_24h = sum(p for p in hours_24 if p is not None)

    # Calculate by day
    daily_totals = []
    for i in range(0, len(precipitation), 24):
        day_rain = sum(p for p in precipitation[i:i+24] if p is not None)
        daily_totals.append(day_rain)

    return {
        "total_rainfall_mm": round(total_rainfall, 1),
        "rainfall_24h_mm": round(rainfall_24h, 1),
        "days_analyzed": days_back,
        "daily_totals": [round(d, 1) for d in daily_totals],
        "avg_daily_mm": round(total_rainfall / days_back, 1)
    }


def display_ground_conditions(location_name, latitude, longitude, days_back=7):
    """Display current ground conditions based on recent rainfall"""
    print(f"\n{'='*60}")
    print(f"CURRENT GROUND CONDITIONS: {location_name}")
    print(f"(Based on past {days_back} days of rainfall)")
    print(f"{'='*60}\n")

    saturation = calculate_ground_saturation(latitude, longitude, days_back)

    if "error" in saturation:
        print(f"Error: {saturation['error']}")
        return

    total_rain = saturation["total_rainfall_mm"]
    rain_24h = saturation["rainfall_24h_mm"]
    daily_totals = saturation["daily_totals"]

    print(f"Rainfall Summary:")
    print(f"  Last 24 hours: {rain_24h} mm")
    print(f"  Last {days_back} days total: {total_rain} mm")
    print(f"  Daily average: {saturation['avg_daily_mm']} mm/day")

    print(f"\nDaily breakdown (most recent last):")
    for i, daily in enumerate(daily_totals):
        days_ago = len(daily_totals) - i - 1
        if days_ago == 0:
            print(f"  Today: {daily} mm")
        elif days_ago == 1:
            print(f"  Yesterday: {daily} mm")
        else:
            print(f"  {days_ago} days ago: {daily} mm")

    # Assess ground conditions
    print(f"\nGROUND CONDITION ASSESSMENT:")

    # Weight recent rain more heavily
    weighted_saturation = (rain_24h * 2) + (total_rain * 0.5)

    if weighted_saturation < 10:
        condition = "DRY"
        advice = "Perfect for hiking! Trails should be in great condition."
    elif weighted_saturation < 25:
        condition = "SLIGHTLY DAMP"
        advice = "Good for hiking. Some low spots might be muddy."
    elif weighted_saturation < 50:
        condition = "WET"
        advice = "Trails will be muddy. Waterproof boots recommended."
    elif weighted_saturation < 80:
        condition = "VERY WET / BOGGY"
        advice = "Very muddy and boggy. Expect wet feet without good waterproof gear."
    else:
        condition = "SATURATED"
        advice = "Extremely boggy, trails may be partially flooded. Not ideal for hiking."

    print(f"  Status: {condition}")
    print(f"  Advice: {advice}")

    print(f"\n{'='*60}\n")


def display_forecast(location_name, latitude, longitude, days=5):
    """Display multi-day forecast with rainfall data"""
    print(f"\n{'='*60}")
    print(f"{days}-DAY FORECAST: {location_name}")
    print(f"{'='*60}\n")

    forecast = get_daily_forecast(latitude, longitude, days)

    if "error" in forecast:
        print(f"Error: {forecast['error']}")
        return

    # Parse forecast data
    daily_forecasts = forecast.get('forecastDays', [])

    if not daily_forecasts:
        print("No forecast data available")
        return

    for day in daily_forecasts:
        date = day.get('displayDate', {})
        date_str = f"{date.get('year')}-{date.get('month'):02d}-{date.get('day'):02d}"

        # Daytime conditions
        daytime = day.get('daytimeForecast', {})
        day_condition = daytime.get('weatherCondition', {}).get('description', {}).get('text', 'Unknown')
        day_temp_max = day.get('maxTemperature', {}).get('degrees', 'N/A')
        day_rain_prob = daytime.get('precipitation', {}).get('probability', {}).get('percent', 0)
        day_rainfall = daytime.get('precipitation', {}).get('qpf', {}).get('quantity', 0)

        # Nighttime conditions
        nighttime = day.get('nighttimeForecast', {})
        night_temp_min = day.get('minTemperature', {}).get('degrees', 'N/A')
        night_rain_prob = nighttime.get('precipitation', {}).get('probability', {}).get('percent', 0)
        night_rainfall = nighttime.get('precipitation', {}).get('qpf', {}).get('quantity', 0)

        total_rainfall = day_rainfall + night_rainfall

        print(f"{date_str}:")
        print(f"  {day_condition} | {night_temp_min}°C - {day_temp_max}°C")
        print(f"  Rain: Day {day_rain_prob}%, Night {night_rain_prob}%")
        print(f"  Expected rainfall: {total_rainfall:.1f} mm")
        print()

    # Calculate total rainfall for the period
    total_period_rain = sum(
        day.get('daytimeForecast', {}).get('precipitation', {}).get('qpf', {}).get('quantity', 0) +
        day.get('nighttimeForecast', {}).get('precipitation', {}).get('qpf', {}).get('quantity', 0)
        for day in daily_forecasts
    )

    print(f"Total expected rainfall over {days} days: {total_period_rain:.1f} mm")

    # Assess ground conditions for hiking
    print(f"\nHIKING GROUND ASSESSMENT:")
    if total_period_rain < 5:
        print("  Ground condition: DRY - Perfect for hiking!")
    elif total_period_rain < 15:
        print("  Ground condition: SLIGHTLY WET - Should be fine, maybe some muddy patches")
    elif total_period_rain < 30:
        print("  Ground condition: WET - Expect muddy trails, waterproof boots recommended")
    elif total_period_rain < 50:
        print("  Ground condition: VERY WET - Very boggy, definitely need waterproof gear")
    else:
        print("  Ground condition: SATURATED - Extremely boggy, trails may be flooded")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    import sys

    # Test with Dublin coordinates
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "forecast":
            # Show future forecast
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            display_forecast("Dublin, Ireland", DUBLIN_LAT, DUBLIN_LON, days)

        elif command == "ground" or command == "hiking":
            # Show current ground conditions based on historical rainfall
            days_back = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            display_ground_conditions("Dublin, Ireland", DUBLIN_LAT, DUBLIN_LON, days_back)

        elif command == "full":
            # Show everything: current weather, ground conditions, and forecast
            display_current_weather("Dublin, Ireland", DUBLIN_LAT, DUBLIN_LON)
            display_ground_conditions("Dublin, Ireland", DUBLIN_LAT, DUBLIN_LON, 7)
            display_forecast("Dublin, Ireland", DUBLIN_LAT, DUBLIN_LON, 5)

        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python weather_checker.py              - Current weather")
            print("  python weather_checker.py forecast [days] - Future forecast")
            print("  python weather_checker.py ground [days]   - Ground conditions from past rainfall")
            print("  python weather_checker.py full            - Everything!")

    else:
        # Show current weather
        display_current_weather("Dublin, Ireland", DUBLIN_LAT, DUBLIN_LON)
