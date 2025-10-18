"""
Perpetua Fitness Class Availability Checker
Checks for available classes in specified categories

SETUP INSTRUCTIONS:
1. Open https://perpetua.ie/timetable in your browser
2. Open Developer Tools (F12) and go to the Network tab
3. Filter by "Fetch/XHR" requests
4. Refresh the page or click on a date
5. Look for API calls (likely to an endpoint with "schedule", "events", "classes" etc.)
6. Click on the API call and copy:
   - The full URL (API_URL below)
   - Any headers needed (especially Authorization if required)
   - The request payload if it's a POST request
7. Update the constants below with the API details

For reference, see how sauna_checker.py works with the Wunderbook API.
"""

import requests
from datetime import datetime, timedelta
import json

# TODO: Update these values after inspecting the browser's Network tab
API_URL = "https://REPLACE_WITH_ACTUAL_API_URL"
# If auth is needed, add it here (check browser Network tab):
# AUTH_TOKEN = "Bearer YOUR_TOKEN_HERE"

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

    # TODO: Update this payload based on what you see in the Network tab
    # This is just a template - the actual structure depends on their API
    payload = {
        "date": date.strftime('%Y-%m-%d'),
        # Add other required fields here
    }

    headers = {
        # TODO: Add any required headers (check Network tab)
        # "Authorization": AUTH_TOKEN,  # Uncomment if auth is needed
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        # Change to .get() if it's a GET request instead of POST
        response = requests.post(API_URL, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            # TODO: Update this based on the actual API response structure
            return data
        else:
            print(f"  HTTP {response.status_code}: {response.text[:200]}")
            return None

    except Exception as e:
        print(f"  Request failed: {e}")
        return None

def analyze_classes(data):
    """Extract available classes from API response"""

    # TODO: Update this based on the actual API response structure
    # This is a template - adjust based on how the data is structured

    available_classes = []

    if not data:
        return available_classes

    # Example structure - modify based on actual API response:
    # classes = data.get('classes', []) or data.get('events', []) or data

    # for cls in classes:
    #     class_name = cls.get('name', '') or cls.get('className', '')
    #
    #     # Check if it's in our target categories
    #     if any(cat.lower() in class_name.lower() for cat in TARGET_CATEGORIES):
    #         time_slot = cls.get('time', '') or cls.get('startTime', '')
    #         spots_available = cls.get('spotsAvailable', 0) or cls.get('available', 0)
    #         total_spots = cls.get('totalSpots', 0) or cls.get('capacity', 0)
    #
    #         if spots_available > 0:
    #             available_classes.append({
    #                 'name': class_name,
    #                 'time': time_slot,
    #                 'available': spots_available,
    #                 'total': total_spots
    #             })

    return available_classes

def check_perpetua_classes():
    """Check Perpetua class availability for upcoming days"""

    print("\n" + "="*80)
    print("PERPETUA FITNESS CLASS AVAILABILITY CHECKER")
    print("="*80)
    print(f"\nLooking for classes in these categories:")
    for cat in TARGET_CATEGORIES:
        print(f"  - {cat}")
    print()

    if "REPLACE_WITH_ACTUAL_API_URL" in API_URL:
        print("ERROR: API_URL not configured!")
        print("\nPlease follow the setup instructions at the top of this file:")
        print("1. Open https://perpetua.ie/timetable in your browser")
        print("2. Open Developer Tools (F12) -> Network tab")
        print("3. Find the API call that loads the class data")
        print("4. Update API_URL and other constants in this file")
        return

    now = datetime.now()

    # Check today and tomorrow
    days_to_check = [
        ("today", now),
        ("tomorrow", now + timedelta(days=1)),
    ]

    all_results = []

    for day_name, day_date in days_to_check:
        print(f"\nChecking {day_name} ({day_date.strftime('%A, %B %d, %Y')})...")

        data = get_classes_for_date(day_date)

        if data:
            classes = analyze_classes(data)
            all_results.append((day_name, day_date, classes))

            if classes:
                print(f"  Found {len(classes)} available class(es) in your categories")
            else:
                print(f"  No available classes found in your categories")

    # Display results
    print("\n" + "="*80)
    print("AVAILABLE CLASSES SUMMARY")
    print("="*80)

    for day_name, day_date, classes in all_results:
        print(f"\n{day_date.strftime('%A, %B %d, %Y')}:")
        print("-" * 40)

        if not classes:
            print("  No available classes")
        else:
            for cls in classes:
                print(f"  [{cls['time']}] {cls['name']}")
                print(f"      {cls['available']}/{cls['total']} spots available")
                print(f"      >>> BOOKABLE! <<<")

    return all_results

if __name__ == "__main__":
    check_perpetua_classes()

    print("\n" + "="*80)
    print("NOTE: This script template needs to be configured with the actual API details.")
    print("See the instructions at the top of this file.")
    print("="*80)
