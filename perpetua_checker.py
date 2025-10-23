"""
Perpetua Fitness Class Availability Checker
Checks for available classes in specified categories

Uses Playwright to scrape the Mindbody Online widget on Perpetua's website.
Runs headless - no browser window will appear.
"""

from playwright.sync_api import sync_playwright
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import re
import sys
import os

TARGET_CATEGORIES = [
    "PERFORMANCE RIDE",
    "RIDE45",
    "RIDE60"
]

SCHEDULE_FILE = "perpetua_schedule.json"

def get_classes_from_page():
    """Scrape class data from Perpetua website using Playwright"""

    print("  Loading Perpetua timetable...")

    with sync_playwright() as p:
        # Launch browser in headless mode (no window)
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = browser.new_page()
        # Set a realistic user agent
        page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        classes_data = []
        last_response_time = [0]  # Track when we last got data

        # Set up response interception to capture the API response
        def handle_response(response):
            if 'schedule' in response.url and response.request.method == 'POST':
                try:
                    text = response.text()

                    # Try parsing as Next.js RSC format - array of classes
                    match = re.search(r'1:(\[.*?\])\s*$', text, re.DOTALL | re.MULTILINE)
                    if match:
                        json_str = match.group(1)
                        classes = json.loads(json_str)
                        if classes:  # Only add if not empty
                            classes_data.extend(classes)
                            import time
                            last_response_time[0] = time.time()  # Update response time
                except:
                    pass  # Silently ignore - not all responses will have class data

        page.on('response', handle_response)

        try:
            # Navigate to timetable page
            page.goto('https://perpetua.ie/timetable', wait_until='load', timeout=60000)

            # Wait for widget to load and be ready
            page.wait_for_timeout(8000)  # Longer initial wait

            # Find the Mindbody widget iframe
            print(f"  Locating Mindbody widget...")
            iframe_locator = page.frame_locator("#bw-widget-iframe-b8be0, iframe[src*='mindbody']")

            # Wait for iframe to fully load
            page.wait_for_timeout(5000)

            # Click through each day - retry until we get data or max retries
            days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            print(f"  Loading classes for each day (will retry until data loads)...")

            for day in days:
                try:
                    print(f"    Clicking {day}...", end=" ", flush=True)
                    day_btn = iframe_locator.get_by_role("button", name=day)

                    # Click 3 times with long waits - simpler and faster
                    before_count = len(classes_data)

                    for attempt in range(3):
                        day_btn.click(timeout=5000, force=True)
                        page.wait_for_timeout(7000)  # Fixed 7 second wait

                    new_classes = len(classes_data) - before_count
                    if new_classes > 0:
                        print(f"(+{new_classes} classes)")
                    else:
                        print(f"(no data)")

                except Exception as e:
                    print(f"not available")
                    continue

            # Final wait
            print(f"  Final wait for stragglers...")
            page.wait_for_timeout(5000)

            print(f"  Total classes collected: {len(classes_data)}")

        except Exception as e:
            # Even if page load times out, we might have captured some data
            if not classes_data:
                print(f"  Error loading page: {e}")

        finally:
            browser.close()

    return classes_data if classes_data else None

def load_schedule():
    """Load the persistent schedule from JSON file"""
    if not os.path.exists(SCHEDULE_FILE):
        return {
            "classes": [],
            "last_updated": None,
            "notes": "This file accumulates all Perpetua classes seen. New scrapes ADD to this data, never remove."
        }

    try:
        with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"classes": [], "last_updated": None}


def save_schedule(schedule):
    """Save the schedule to JSON file"""
    with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
        json.dump(schedule, f, indent=2, ensure_ascii=False)


def merge_classes(existing_schedule, new_classes_data):
    """
    Merge new class data with existing schedule.
    NEVER removes classes, only adds new ones or updates existing ones.
    """
    existing_classes = existing_schedule.get('classes', [])

    # Create a lookup by unique key (start_datetime + name)
    existing_by_key = {}
    for cls in existing_classes:
        key = f"{cls.get('start_datetime', '')}_{cls.get('name', '')}"
        existing_by_key[key] = cls

    # Process new classes
    for cls in new_classes_data:
        class_name = cls.get('name', '')

        # Check if it's in our target categories
        if any(cat.lower() in class_name.lower() for cat in TARGET_CATEGORIES):
            start_time = cls.get('startDateTime', '')
            key = f"{start_time}_{class_name}"

            # Parse time info
            if start_time:
                try:
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    dt_irish = dt.astimezone(ZoneInfo('Europe/Dublin'))
                    time_str = dt_irish.strftime('%H:%M')
                    date_str = dt_irish.strftime('%Y-%m-%d')
                    day_str = dt_irish.strftime('%A')
                except:
                    time_str = "Unknown"
                    date_str = start_time
                    day_str = "Unknown"
            else:
                time_str = "Unknown"
                date_str = "Unknown"
                day_str = "Unknown"

            capacity = cls.get('capacity', 0)
            registered = cls.get('numberRegistered', 0)
            spots_available = capacity - registered
            bookable = cls.get('bookable', False)
            cancelled = cls.get('cancelled', False)
            location = cls.get('location', {}).get('name', 'Unknown')

            class_entry = {
                'name': class_name,
                'time': time_str,
                'date': date_str,
                'day': day_str,
                'available': spots_available,
                'total': capacity,
                'location': location,
                'start_datetime': start_time,
                'bookable': bookable,
                'cancelled': cancelled,
                'last_seen': datetime.now().isoformat()
            }

            # Add or update the class
            if key in existing_by_key:
                # Update existing class with latest availability
                existing_by_key[key].update(class_entry)
            else:
                # Add new class
                existing_by_key[key] = class_entry

    # Convert back to list and sort
    merged_classes = list(existing_by_key.values())
    merged_classes.sort(key=lambda x: x.get('start_datetime', ''))

    return merged_classes


def analyze_classes(classes_data):
    """Extract available classes from API response"""

    available_classes = []

    if not classes_data:
        return available_classes

    for cls in classes_data:
        class_name = cls.get('name', '')

        # Check if it's in our target categories (case-insensitive partial match)
        if any(cat.lower() in class_name.lower() for cat in TARGET_CATEGORIES):
            # Parse the datetime and convert to Irish time
            start_time = cls.get('startDateTime', '')
            if start_time:
                try:
                    # Parse as UTC and convert to Europe/Dublin timezone
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    dt_irish = dt.astimezone(ZoneInfo('Europe/Dublin'))
                    time_str = dt_irish.strftime('%H:%M')
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

def check_perpetua_classes(use_persistent=True):
    """
    Check Perpetua class availability

    Args:
        use_persistent: If True, merges with persistent schedule file
    """

    print("\n" + "="*80)
    print("PERPETUA FITNESS CLASS AVAILABILITY CHECKER")
    if use_persistent:
        print("(Using persistent schedule - accumulates all classes seen)")
    print("="*80)
    print(f"\nLooking for classes in these categories:")
    for cat in TARGET_CATEGORIES:
        print(f"  - {cat}")
    print()

    # Load existing schedule
    if use_persistent:
        schedule = load_schedule()
        print(f"  Loaded persistent schedule: {len(schedule.get('classes', []))} classes on file")
    else:
        schedule = {"classes": [], "last_updated": None}

    # Get classes from the website
    data = get_classes_from_page()

    if not data:
        print("\nFailed to fetch class data from website.")
        if use_persistent and schedule.get('classes'):
            print("Using existing schedule data from file...")
        else:
            print("Please check your internet connection or try again later.")
            return []
    else:
        print(f"  Total classes found this scrape: {len(data)}")

        # Show all unique class types found (for debugging)
        if data:
            all_types = set(cls.get('name', '') for cls in data)
            print(f"  Class types in data: {', '.join(sorted(all_types))}")

        # Merge with persistent schedule
        if use_persistent:
            merged_classes = merge_classes(schedule, data)
            schedule['classes'] = merged_classes
            schedule['last_updated'] = datetime.now().isoformat()
            save_schedule(schedule)
            print(f"  Merged schedule now has: {len(merged_classes)} total classes")
            print(f"  Saved to: {SCHEDULE_FILE}")

    # Get all classes from schedule (filter for upcoming only)
    all_classes = schedule.get('classes', [])

    # Filter for upcoming classes only (not in the past)
    now = datetime.now(ZoneInfo('Europe/Dublin'))
    upcoming_classes = []
    for cls in all_classes:
        try:
            dt = datetime.fromisoformat(cls['start_datetime'].replace('Z', '+00:00'))
            dt_irish = dt.astimezone(ZoneInfo('Europe/Dublin'))
            if dt_irish > now:
                # Check if bookable and not cancelled and has spots
                if cls.get('bookable', False) and not cls.get('cancelled', False) and cls.get('available', 0) > 0:
                    upcoming_classes.append(cls)
        except:
            pass

    if not upcoming_classes:
        print("\n" + "="*80)
        print("No upcoming RIDE/Performance classes with availability.")
        print("="*80)
        return []

    # Group by date
    classes_by_date = {}
    for cls in upcoming_classes:
        date_key = cls.get('date', 'Unknown')
        if date_key not in classes_by_date:
            classes_by_date[date_key] = []
        classes_by_date[date_key].append(cls)

    # Display results
    print("\n" + "="*80)
    print(f"UPCOMING CLASSES WITH AVAILABILITY: {len(upcoming_classes)}")
    if use_persistent:
        print(f"(From persistent schedule with {len(all_classes)} total classes)")
    print("="*80)

    for date_key in sorted(classes_by_date.keys()):
        classes = classes_by_date[date_key]
        try:
            date_obj = datetime.strptime(date_key, '%Y-%m-%d')
            print(f"\n{date_obj.strftime('%A, %B %d, %Y')}:")
        except:
            print(f"\n{date_key}:")
        print("-" * 60)

        for cls in classes:
            print(f"  [{cls.get('time', 'Unknown')}] {cls.get('name', 'Unknown')}")
            print(f"      Location: {cls.get('location', 'Unknown')}")
            print(f"      Availability: {cls.get('available', 0)}/{cls.get('total', 0)} spots")
            if cls.get('bookable', False):
                print(f"      >>> BOOKABLE! <<<")

    # Return in old format for compatibility
    return upcoming_classes

def get_today_classes_from_schedule():
    """
    Quick function to get today's classes from persistent schedule WITHOUT scraping.
    Use this for fast daily checks. Run full check_perpetua_classes() periodically to update.
    """
    schedule = load_schedule()
    all_classes = schedule.get('classes', [])

    # Filter for today only
    now = datetime.now(ZoneInfo('Europe/Dublin'))
    today_str = now.strftime('%Y-%m-%d')
    today_classes = []

    for cls in all_classes:
        if cls.get('date') == today_str:
            # Check if bookable and not cancelled and has spots and is upcoming
            try:
                dt = datetime.fromisoformat(cls['start_datetime'].replace('Z', '+00:00'))
                dt_irish = dt.astimezone(ZoneInfo('Europe/Dublin'))
                if dt_irish > now and cls.get('bookable', False) and not cls.get('cancelled', False) and cls.get('available', 0) > 0:
                    today_classes.append(cls)
            except:
                pass

    return today_classes


if __name__ == "__main__":
    check_perpetua_classes()
