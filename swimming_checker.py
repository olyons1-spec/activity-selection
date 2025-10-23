"""
Swimming Availability Checker
Checks tide windows and weather conditions for swimming at Dublin (North Wall)
"""
from datetime import datetime, timedelta
from weather_checker import find_best_tide_windows, DUBLIN_NORTH_LAT, DUBLIN_NORTH_LON


def check_swimming_availability(days=3):
    """
    Check if there are good swimming windows available today or in the next few days.

    Args:
        days: Number of days to check ahead (default 3)

    Returns:
        Dictionary with swimming availability info
    """
    # Get tide windows
    windows = find_best_tide_windows(DUBLIN_NORTH_LAT, DUBLIN_NORTH_LON, days)

    if isinstance(windows, dict) and "error" in windows:
        return {
            'available': False,
            'error': windows['error']
        }

    if not windows:
        return {
            'available': False,
            'reason': 'No suitable high tide windows during daylight hours'
        }

    # Filter for today
    today = datetime.now().date()
    today_windows = [w for w in windows if w['tide_time'].date() == today]

    # Get upcoming windows (next 3 days)
    upcoming_windows = [w for w in windows[:5] if w['tide_time'].date() >= today]

    if today_windows:
        best_today = today_windows[0]
        return {
            'available': True,
            'today': True,
            'tide_time': best_today['tide_time'],
            'window_start': best_today['window_start'],
            'window_end': best_today['window_end'],
            'tide_height': best_today['tide_height'],
            'weather_desc': best_today['weather_desc'],
            'temp': best_today['temp'],
            'rain_prob': best_today['rain_prob'],
            'cloud_cover': best_today['cloud_cover'],
            'is_sunny': best_today['is_sunny'],
            'is_dry': best_today['is_dry'],
            'rating': get_rating(best_today),
            'location': 'Dublin (North Wall)',
            'duration_minutes': 90,
            'all_today_windows': today_windows,
            'upcoming_windows': upcoming_windows
        }
    else:
        # No windows today, but show next available
        next_window = upcoming_windows[0] if upcoming_windows else None
        if next_window:
            return {
                'available': False,
                'today': False,
                'next_available': next_window['tide_time'],
                'next_window_start': next_window['window_start'],
                'next_window_end': next_window['window_end'],
                'next_weather': next_window['weather_desc'],
                'next_temp': next_window['temp'],
                'next_rating': get_rating(next_window),
                'location': 'Dublin (North Wall)',
                'upcoming_windows': upcoming_windows
            }
        else:
            return {
                'available': False,
                'reason': 'No suitable windows in the next few days'
            }


def get_rating(window):
    """Get text rating for a window"""
    if window['is_sunny'] and window['is_dry']:
        return "EXCELLENT"
    elif window['is_clear'] and window['is_dry']:
        return "GOOD"
    elif window['is_dry']:
        return "FAIR"
    else:
        return "POOR"


def display_swimming_availability():
    """Display swimming availability in a nice format"""
    print("\n" + "="*60)
    print("SWIMMING AVAILABILITY - Dublin (North Wall)")
    print("="*60 + "\n")

    result = check_swimming_availability(days=7)

    if 'error' in result:
        print(f"Error: {result['error']}")
        return result

    if result['available'] and result['today']:
        print("[YES] Swimming available TODAY!\n")

        print(f"High Tide: {result['tide_time'].strftime('%H:%M')} ({result['tide_height']:.2f}m)")
        print(f"Best Window: {result['window_start'].strftime('%H:%M')} - {result['window_end'].strftime('%H:%M')}")
        print(f"Weather: {result['weather_desc']} ({result['temp']:.1f}°C)")
        print(f"Rain Probability: {result['rain_prob']}%")
        print(f"Cloud Cover: {result['cloud_cover']}%")
        print(f"Rating: {result['rating']}")

        if len(result['all_today_windows']) > 1:
            print(f"\nNote: {len(result['all_today_windows'])} tide windows available today")

        # Show next few days
        if result['upcoming_windows']:
            print(f"\nUpcoming windows (next 5):")
            for i, window in enumerate(result['upcoming_windows'][:5], 1):
                day = window['tide_time'].strftime('%A, %b %d')
                time = window['tide_time'].strftime('%H:%M')
                rating = get_rating(window)
                print(f"  {i}. {day} at {time} - {window['weather_desc']} ({rating})")

    else:
        print("[NO] No swimming windows available today\n")

        if 'next_available' in result:
            print(f"Next available window:")
            print(f"  Date: {result['next_available'].strftime('%A, %B %d, %Y')}")
            print(f"  Time: {result['next_window_start'].strftime('%H:%M')} - {result['next_window_end'].strftime('%H:%M')}")
            print(f"  Weather: {result['next_weather']} ({result['next_temp']:.1f}°C)")
            print(f"  Rating: {result['next_rating']}")

            # Show more upcoming
            if result.get('upcoming_windows'):
                print(f"\nAll upcoming windows:")
                for i, window in enumerate(result['upcoming_windows'][:5], 1):
                    day = window['tide_time'].strftime('%A, %b %d')
                    time = window['tide_time'].strftime('%H:%M')
                    rating = get_rating(window)
                    print(f"  {i}. {day} at {time} - {window['weather_desc']} ({rating})")
        else:
            print(f"Reason: {result.get('reason', 'Unknown')}")

    print("\n" + "="*60 + "\n")
    return result


if __name__ == "__main__":
    display_swimming_availability()
