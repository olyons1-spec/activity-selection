"""
Perpetua Fitness Class Availability Checker
Checks for available classes in specified categories

Uses the Mindbody Online API (via Next.js RSC format) to fetch class schedules.
No authentication required - public API endpoint.
"""

import requests
from datetime import datetime, timedelta
import json
import re

# Mindbody Online widget endpoint for Perpetua
API_URL = "https://brandedweb-next.mindbodyonline.com/components/widgets/schedules/view/7043150014/schedule"

TARGET_CATEGORIES = [
    "InBody Analysis",
    "Oly AM",
    "PERFORMANCE RIDE",
    "Ride",
    "RIDE",
    "RIDE45",
    "RIDE60",
    "Rumble"
]

def get_classes_for_date(date):
    """Get scheduled classes for a specific date using the API"""

    # Build date range - today
    # The API seems to want the date range for a full day
    from_date = date.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(hours=1)
    to_date = from_date.replace(hour=23, minute=59, second=59, microsecond=999000)

    # Format as ISO string with timezone
    from_date_str = from_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-4] + 'Z'  # .000Z format
    to_date_str = to_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-4] + 'Z'  # .999Z format

    # Construct the exact payload format from the browser
    payload_data = json.dumps([
        "$@1",
        {
            "fromDate": from_date_str,
            "toDate": to_date_str
        }
    ], separators=(',', ':'))

    # Use requests' files parameter for multipart/form-data
    files = {
        '0': (None, payload_data, 'application/json')
    }

    headers = {
        "Accept": "text/x-component",
        "Next-Action": "a64730d69e8890e8f3a86a82ccf6ac0d82c0fb45",
        "Origin": "https://perpetua.ie",
        "Referer": "https://perpetua.ie/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.post(API_URL, headers=headers, files=files, timeout=10)

        if response.status_code == 200:
            # The response is in Next.js RSC format
            # Parse the JSON array from the response text
            text = response.text

            # Find the JSON array in the response (it's embedded in the RSC stream)
            # Look for pattern like: 1:[{...class data...}]
            match = re.search(r'1:(\[.*?\])\s*$', text, re.DOTALL | re.MULTILINE)

            if match:
                json_str = match.group(1)
                # Parse the JSON
                classes = json.loads(json_str)
                return classes
            else:
                print(f"  Could not parse RSC response")
                # Save response for debugging
                with open('perpetua_debug_response.txt', 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"  Response saved to perpetua_debug_response.txt")
                return None
        else:
            print(f"  HTTP {response.status_code}: {response.text[:200]}")
            return None

    except Exception as e:
        print(f"  Request failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_classes(classes_data):
    """Extract available classes from API response"""

    available_classes = []

    if not classes_data:
        return available_classes

    for cls in classes_data:
        class_name = cls.get('name', '')

        # Check if it's in our target categories (case-insensitive partial match)
        if any(cat.lower() in class_name.lower() for cat in TARGET_CATEGORIES):
            # Parse the datetime
            start_time = cls.get('startDateTime', '')
            if start_time:
                try:
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M')
                except:
                    time_str = start_time
            else:
                time_str = "Unknown"

            capacity = cls.get('capacity', 0)
            registered = cls.get('numberRegistered', 0)
            spots_available = capacity - registered
            bookable = cls.get('bookable', False)
            cancelled = cls.get('cancelled', False)
            location = cls.get('location', {}).get('name', 'Unknown')

            # Only include if bookable and not cancelled
            if bookable and not cancelled and spots_available > 0:
                available_classes.append({
                    'name': class_name,
                    'time': time_str,
                    'available': spots_available,
                    'total': capacity,
                    'location': location,
                    'start_datetime': start_time
                })

    # Sort by start time
    available_classes.sort(key=lambda x: x['start_datetime'])

    return available_classes

def check_perpetua_classes():
    """Check Perpetua class availability"""

    print("\n" + "="*80)
    print("PERPETUA FITNESS CLASS AVAILABILITY CHECKER")
    print("="*80)
    print(f"\nLooking for classes in these categories:")
    for cat in TARGET_CATEGORIES:
        print(f"  - {cat}")
    print()

    # The API returns all classes for the current schedule view
    # We just need to call it once
    print("Fetching class schedule...")

    data = get_classes_for_date(datetime.now())

    if not data:
        print("Failed to fetch class data")
        return []

    # Analyze all classes
    available_classes = analyze_classes(data)

    if not available_classes:
        print("\nNo available classes found in your target categories.")
        return []

    # Group by date
    classes_by_date = {}
    for cls in available_classes:
        try:
            dt = datetime.fromisoformat(cls['start_datetime'].replace('Z', '+00:00'))
            date_key = dt.strftime('%Y-%m-%d')
            if date_key not in classes_by_date:
                classes_by_date[date_key] = []
            classes_by_date[date_key].append(cls)
        except:
            pass

    # Display results
    print("\n" + "="*80)
    print("AVAILABLE CLASSES")
    print("="*80)

    for date_key in sorted(classes_by_date.keys()):
        classes = classes_by_date[date_key]
        date_obj = datetime.strptime(date_key, '%Y-%m-%d')
        print(f"\n{date_obj.strftime('%A, %B %d, %Y')}:")
        print("-" * 60)

        for cls in classes:
            print(f"  [{cls['time']}] {cls['name']}")
            print(f"      Location: {cls['location']}")
            print(f"      Availability: {cls['available']}/{cls['total']} spots")
            if cls['available'] > 0:
                print(f"      >>> BOOKABLE! <<<")

    return available_classes

if __name__ == "__main__":
    check_perpetua_classes()
