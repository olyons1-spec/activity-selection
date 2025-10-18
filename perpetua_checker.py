"""
Perpetua Fitness Class Availability Checker
Checks for available classes in specified categories

Uses Playwright to scrape the Mindbody Online widget on Perpetua's website.
Runs headless - no browser window will appear.
"""

from playwright.sync_api import sync_playwright
from datetime import datetime
import json
import re
import sys

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

def get_classes_from_page():
    """Scrape class data from Perpetua website using Playwright"""

    print("  Loading Perpetua timetable...")

    with sync_playwright() as p:
        # Launch browser in headless mode (no window)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        classes_data = []

        # Set up response interception to capture the API response
        def handle_response(response):
            if 'schedule' in response.url and response.request.method == 'POST':
                try:
                    text = response.text()
                    # Parse Next.js RSC format response
                    match = re.search(r'1:(\[.*?\])\s*$', text, re.DOTALL | re.MULTILINE)
                    if match:
                        json_str = match.group(1)
                        classes = json.loads(json_str)
                        classes_data.extend(classes)
                except:
                    pass

        page.on('response', handle_response)

        try:
            # Navigate to timetable page
            page.goto('https://perpetua.ie/timetable', wait_until='domcontentloaded', timeout=60000)

            # Wait for schedule data to load (wait for API responses)
            page.wait_for_timeout(5000)

            # Try to navigate to see more days
            for i in range(7):  # Check next 7 days
                try:
                    # Look for and click the next/forward arrow button
                    # Common selectors for date navigation
                    next_selectors = [
                        'button[aria-label*="next" i]',
                        'button[aria-label*="forward" i]',
                        'button:has-text("›")',
                        'button:has-text("Next")',
                        '.calendar-next',
                        '[class*="next"]'
                    ]

                    clicked = False
                    for selector in next_selectors:
                        try:
                            next_btn = page.locator(selector).first
                            if next_btn.is_visible(timeout=1000):
                                next_btn.click()
                                page.wait_for_timeout(2000)  # Wait for new data to load
                                clicked = True
                                break
                        except:
                            continue

                    if not clicked:
                        break  # No more navigation possible

                except:
                    break

        except Exception as e:
            # Even if page load times out, we might have captured some data
            if not classes_data:
                print(f"  Error loading page: {e}")

        finally:
            browser.close()

    return classes_data if classes_data else None

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

    # Get classes from the website
    data = get_classes_from_page()

    if not data:
        print("\nFailed to fetch class data from website.")
        print("Please check your internet connection or try again later.")
        return []

    # Analyze classes
    available_classes = analyze_classes(data)

    if not available_classes:
        print("\n" + "="*80)
        print("No available classes found in your target categories.")
        print("="*80)
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
    print(f"FOUND {len(available_classes)} AVAILABLE CLASS(ES)")
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
            print(f"      >>> BOOKABLE! <<<")

    return available_classes

if __name__ == "__main__":
    check_perpetua_classes()
