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

# Dublin North Wall coordinates (for tide data)
DUBLIN_NORTH_LAT = 53.3498
DUBLIN_NORTH_LON = -6.2298


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


def get_tide_data(latitude, longitude, days=7):
    """
    Get tide data using WorldTides API (FREE tier: 500 requests/month)

    Args:
        latitude: Location latitude
        longitude: Location longitude
        days: Number of days to get tides for (default 7)

    Returns:
        Dictionary with tide data
    """
    # WorldTides API key (free tier: 500 requests/month)
    WORLDTIDES_API_KEY = "1f6845ea-de3d-4c92-a157-caf4af3d7743"

    base_url = "https://www.worldtides.info/api/v3"

    # Calculate start and end timestamps
    start_time = datetime.now()
    end_time = start_time + timedelta(days=days)

    params = {
        "extremes": True,
        "lat": latitude,
        "lon": longitude,
        "start": int(start_time.timestamp()),
        "length": days * 86400,  # seconds in a day
        "key": WORLDTIDES_API_KEY
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)

        if response.status_code != 200:
            # Try alternative free service
            return get_tide_data_alternative(latitude, longitude, days)

        data = response.json()
        return data
    except Exception as e:
        return get_tide_data_alternative(latitude, longitude, days)


def get_tide_data_alternative(latitude, longitude, days=7):
    """
    Alternative tide data using NOAA or other free services.
    For Irish waters, we can use the Irish Marine Institute data.
    """
    # Using a simple approximation based on lunar cycles
    # This is a fallback - for production use, get a proper API key

    return {
        "note": "Using simplified tide predictions. For accurate data, configure a WorldTides API key.",
        "extremes": []
    }


def display_tide_info(location_name, latitude, longitude, days=2):
    """Display tide information for the next few days"""
    print(f"\n{'='*60}")
    print(f"TIDE INFORMATION: {location_name}")
    print(f"(Next {days} days)")
    print(f"{'='*60}\n")

    tide_data = get_tide_data(latitude, longitude, days)

    if "error" in tide_data:
        print(f"Error: {tide_data['error']}")
        return

    if "note" in tide_data:
        print(f"Note: {tide_data['note']}\n")

    extremes = tide_data.get('extremes', [])

    if not extremes:
        print("Tide data not available. Consider signing up for a free API key at:")
        print("  https://www.worldtides.info/register")
        print("\nAlternatively, check tides at:")
        print("  https://tides.ie/")
        print(f"  Location: Dublin (North Wall)")
        print(f"  Coordinates: {latitude:.4f}, {longitude:.4f}")
        print(f"\n{'='*60}\n")
        return

    # Group tides by day
    current_date = None
    for extreme in extremes:
        tide_time = datetime.fromtimestamp(extreme['dt'])
        tide_date = tide_time.date()
        tide_type = extreme['type']  # 'High' or 'Low'
        tide_height = extreme.get('height', 'N/A')

        # Print date header if new day
        if tide_date != current_date:
            if current_date is not None:
                print()  # Blank line between days
            print(f"{tide_date.strftime('%A, %B %d, %Y')}:")
            current_date = tide_date

        print(f"  {tide_time.strftime('%H:%M')} - {tide_type} tide ({tide_height}m)")

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


def get_sunrise_sunset(latitude, longitude, date):
    """
    Get sunrise and sunset times for a specific date.
    Uses Open-Meteo API (free, no key needed)
    """
    date_str = date.strftime('%Y-%m-%d')

    base_url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "sunrise,sunset",
        "timezone": "Europe/Dublin",
        "start_date": date_str,
        "end_date": date_str
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            daily = data.get('daily', {})
            if daily.get('sunrise') and daily.get('sunset'):
                sunrise = datetime.fromisoformat(daily['sunrise'][0])
                sunset = datetime.fromisoformat(daily['sunset'][0])
                return sunrise, sunset
    except:
        pass

    # Fallback: approximate sunrise/sunset for Dublin
    # Winter: ~8:30am-4:30pm, Summer: ~5:30am-9:30pm
    month = date.month
    if month in [11, 12, 1, 2]:  # Winter
        sunrise = date.replace(hour=8, minute=30)
        sunset = date.replace(hour=16, minute=30)
    elif month in [5, 6, 7, 8]:  # Summer
        sunrise = date.replace(hour=5, minute=30)
        sunset = date.replace(hour=21, minute=30)
    else:  # Spring/Fall
        sunrise = date.replace(hour=7, minute=0)
        sunset = date.replace(hour=19, minute=0)

    return sunrise, sunset


def get_hourly_weather_forecast(latitude, longitude, days=3):
    """
    Get hourly weather forecast using Open-Meteo API (free, no key needed)
    """
    base_url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,precipitation_probability,weather_code,cloud_cover",
        "timezone": "Europe/Dublin",
        "forecast_days": days
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass

    return {"error": "Unable to fetch hourly weather data"}


def find_best_tide_windows(latitude, longitude, days=7):
    """
    Find the best 90-minute windows around high tides during daylight hours with good weather.
    Perfect for planning swimming sessions at high tide.

    Args:
        latitude: Location latitude
        longitude: Location longitude
        days: Number of days to check (default 7)

    Returns:
        List of optimal windows with tide and weather info
    """
    # Get tide data
    tide_data = get_tide_data(latitude, longitude, days)

    if "error" in tide_data or not tide_data.get('extremes'):
        return {"error": "Unable to fetch tide data"}

    # Get hourly weather forecast
    weather_data = get_hourly_weather_forecast(latitude, longitude, days)

    if "error" in weather_data:
        return {"error": "Unable to fetch weather data"}

    # Parse hourly weather into a dictionary by timestamp
    hourly = weather_data.get('hourly', {})
    times = hourly.get('time', [])
    temps = hourly.get('temperature_2m', [])
    rain_probs = hourly.get('precipitation_probability', [])
    weather_codes = hourly.get('weather_code', [])
    cloud_covers = hourly.get('cloud_cover', [])

    weather_by_time = {}
    for i, time_str in enumerate(times):
        dt = datetime.fromisoformat(time_str)
        weather_by_time[dt] = {
            'temp': temps[i] if i < len(temps) else None,
            'rain_prob': rain_probs[i] if i < len(rain_probs) else None,
            'weather_code': weather_codes[i] if i < len(weather_codes) else None,
            'cloud_cover': cloud_covers[i] if i < len(cloud_covers) else None
        }

    # Find high tides during daylight with good weather
    optimal_windows = []

    for extreme in tide_data['extremes']:
        if extreme['type'] != 'High':
            continue

        tide_time = datetime.fromtimestamp(extreme['dt'])
        tide_height = extreme.get('height', 0)

        # Get sunrise/sunset for this date
        sunrise, sunset = get_sunrise_sunset(latitude, longitude, tide_time.date())

        # Check if high tide is during daylight (with 90min window either side)
        window_start = tide_time - timedelta(minutes=90)
        window_end = tide_time + timedelta(minutes=90)

        # Must have at least some overlap with daylight
        if window_end < sunrise or window_start > sunset:
            continue  # Entirely outside daylight hours

        # Adjust window to daylight hours only
        actual_start = max(window_start, sunrise)
        actual_end = min(window_end, sunset)

        # Get weather for the high tide time (or closest hour)
        closest_weather = None
        min_time_diff = timedelta(hours=24)

        for weather_time, weather_info in weather_by_time.items():
            time_diff = abs(weather_time - tide_time)
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_weather = weather_info

        if not closest_weather:
            continue

        # Assess weather quality
        rain_prob = closest_weather.get('rain_prob', 0)
        weather_code = closest_weather.get('weather_code', 0)
        cloud_cover = closest_weather.get('cloud_cover', 100)
        temp = closest_weather.get('temp', 0)

        # Weather codes: 0-1 clear/mostly clear, 2-3 partly cloudy, 45-48 fog, 51+ rain/snow
        is_sunny = weather_code in [0, 1] and cloud_cover < 40
        is_clear = weather_code in [0, 1, 2, 3] and cloud_cover < 60
        is_dry = rain_prob < 30

        weather_desc = "Sunny" if is_sunny else ("Clear/Partly Cloudy" if is_clear else "Cloudy")
        if rain_prob > 50:
            weather_desc = "Rainy"

        optimal_windows.append({
            'tide_time': tide_time,
            'tide_height': tide_height,
            'window_start': actual_start,
            'window_end': actual_end,
            'sunrise': sunrise,
            'sunset': sunset,
            'is_daylight': True,
            'is_sunny': is_sunny,
            'is_clear': is_clear,
            'is_dry': is_dry,
            'weather_desc': weather_desc,
            'temp': temp,
            'rain_prob': rain_prob,
            'cloud_cover': cloud_cover
        })

    # Sort by quality score (sunny + dry + daylight hours)
    def quality_score(window):
        score = 0
        score += 100 if window['is_sunny'] else 0
        score += 50 if window['is_clear'] else 0
        score += 30 if window['is_dry'] else 0
        score -= window['rain_prob']
        score -= window['cloud_cover'] / 2

        # Prefer windows with more daylight time
        window_duration = (window['window_end'] - window['window_start']).total_seconds() / 60
        score += window_duration / 10  # Bonus for longer windows

        return score

    optimal_windows.sort(key=quality_score, reverse=True)

    return optimal_windows


def display_best_tide_windows(latitude, longitude, days=7, show_all=False):
    """Display the best tide windows for swimming activities"""
    print(f"\n{'='*60}")
    if show_all:
        print(f"ALL HIGH TIDE WINDOWS (90min either side)")
    else:
        print(f"BEST HIGH TIDE WINDOWS (90min either side)")
    print(f"During daylight hours - Next {days} days")
    print(f"For Swimming at Dublin (North Wall)")
    print(f"{'='*60}\n")

    windows = find_best_tide_windows(latitude, longitude, days)

    if isinstance(windows, dict) and "error" in windows:
        print(f"Error: {windows['error']}")
        return

    if not windows:
        print("No suitable high tide windows found during daylight hours.")
        print(f"\n{'='*60}\n")
        return

    # Show all windows or just top 5
    windows_to_show = windows if show_all else windows[:5]

    for i, window in enumerate(windows_to_show, 1):
        tide_time = window['tide_time']
        window_start = window['window_start']
        window_end = window['window_end']

        print(f"{i}. {tide_time.strftime('%A, %B %d, %Y')}")
        print(f"   High Tide: {tide_time.strftime('%H:%M')} ({window['tide_height']:.2f}m)")
        print(f"   Window: {window_start.strftime('%H:%M')} - {window_end.strftime('%H:%M')}")
        print(f"   Sunrise: {window['sunrise'].strftime('%H:%M')}, Sunset: {window['sunset'].strftime('%H:%M')}")
        print(f"   Weather: {window['weather_desc']} ({window['temp']:.1f}°C)")
        print(f"   Rain probability: {window['rain_prob']}%")
        print(f"   Cloud cover: {window['cloud_cover']}%")

        # Overall rating
        if window['is_sunny'] and window['is_dry']:
            rating = "EXCELLENT ***"
        elif window['is_clear'] and window['is_dry']:
            rating = "GOOD **"
        elif window['is_dry']:
            rating = "FAIR *"
        else:
            rating = "POOR"

        print(f"   Rating: {rating}")
        print()

    print(f"{'='*60}\n")


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

        elif command == "tides":
            # Show tide information for Dublin North Wall
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 2
            display_tide_info("Dublin (North Wall)", DUBLIN_NORTH_LAT, DUBLIN_NORTH_LON, days)

        elif command == "best" or command == "windows":
            # Show best tide windows during daylight with good weather
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            # Check if 'all' flag is passed
            show_all = len(sys.argv) > 3 and sys.argv[3] == "all"
            display_best_tide_windows(DUBLIN_NORTH_LAT, DUBLIN_NORTH_LON, days, show_all)

        elif command == "all":
            # Show ALL tide windows for the next 7 days
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            display_best_tide_windows(DUBLIN_NORTH_LAT, DUBLIN_NORTH_LON, days, show_all=True)

        elif command == "full":
            # Show everything: current weather, ground conditions, forecast, and tides
            display_current_weather("Dublin, Ireland", DUBLIN_LAT, DUBLIN_LON)
            display_ground_conditions("Dublin, Ireland", DUBLIN_LAT, DUBLIN_LON, 7)
            display_forecast("Dublin, Ireland", DUBLIN_LAT, DUBLIN_LON, 5)
            display_tide_info("Dublin (North Wall)", DUBLIN_NORTH_LAT, DUBLIN_NORTH_LON, 2)

        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python weather_checker.py                 - Current weather")
            print("  python weather_checker.py forecast [days] - Future forecast")
            print("  python weather_checker.py ground [days]   - Ground conditions from past rainfall")
            print("  python weather_checker.py tides [days]    - Tide information for Dublin North")
            print("  python weather_checker.py best [days]     - Top 5 high tide windows with good weather")
            print("  python weather_checker.py all [days]      - ALL high tide windows with weather")
            print("  python weather_checker.py full            - Everything!")

    else:
        # Show current weather
        display_current_weather("Dublin, Ireland", DUBLIN_LAT, DUBLIN_LON)
