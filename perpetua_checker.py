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
                    pass  # Silently ignore parsing errors

        page.on('response', handle_response)

        try:
            # Navigate to timetable page
            page.goto('https://perpetua.ie/timetable', wait_until='domcontentloaded', timeout=60000)

            # Accept cookies
            try:
                cookie_btn = page.locator('button:has-text("Allow cookies")').first
                if cookie_btn.is_visible(timeout=2000):
                    cookie_btn.click()
                    page.wait_for_timeout(1000)
            except:
                pass

            # Dismiss promotional popup if it appears
            try:
                page.wait_for_timeout(3000)  # Wait for popup to appear
                no_thanks_btn = page.locator('text="NO, THANKS"').first
                if no_thanks_btn.is_visible(timeout=2000):
                    print(f"  Dismissing promotional popup...")
                    no_thanks_btn.click()
                    page.wait_for_timeout(1000)
            except:
                pass

            # Wait for the Mindbody widget iframe to load
            print(f"  Waiting for calendar widget to load...")
            page.wait_for_timeout(8000)

            # Find and access the Mindbody iframe
            try:
                iframe_elem = page.wait_for_selector('iframe[src*="mindbody"]', timeout=10000)
                frame = iframe_elem.content_frame()

                if frame:
                    print(f"  Loading full week schedule...")
                    frame.wait_for_timeout(5000)  # Wait longer for initial load

                    # Try clicking "Full Calendar" button to see all classes
                    try:
                        clicked = frame.evaluate('''() => {
                            const allButtons = Array.from(document.querySelectorAll('button'));
                            const calBtn = allButtons.find(btn => btn.textContent.trim() === 'Full Calendar');
                            if (calBtn) {
                                calBtn.click();
                                return true;
                            }
                            return false;
                        }''')

                        if clicked:
                            print(f"  Switched to Full Calendar view")
                            frame.wait_for_timeout(8000)  # Wait longer for calendar view to load all data

                            # Try navigating forward through weeks to load more data
                            for week_num in range(2):  # Load 2 more weeks
                                nav_clicked = frame.evaluate('''() => {
                                    const allButtons = Array.from(document.querySelectorAll('button'));
                                    const nextBtn = allButtons.find(btn => {
                                        const text = btn.textContent.trim();
                                        const ariaLabel = btn.getAttribute('aria-label') || '';
                                        return text === '›' || text === '>' ||
                                               ariaLabel.toLowerCase().includes('next') ||
                                               ariaLabel.toLowerCase().includes('forward');
                                    });

                                    if (nextBtn && !nextBtn.disabled) {
                                        nextBtn.click();
                                        return true;
                                    }
                                    return false;
                                }''')

                                if nav_clicked:
                                    print(f"    Loading week {week_num + 2}...")
                                    frame.wait_for_timeout(4000)
                                else:
                                    break

                    except Exception as e:
                        print(f"  Calendar navigation error: {e}")

                    print(f"  Total classes collected: {len(classes_data)}")

                else:
                    print(f"  Could not access iframe, collecting today's data only...")
                    page.wait_for_timeout(5000)

            except Exception as e:
                print(f"  Could not find widget iframe, collecting today's data only...")
                page.wait_for_timeout(5000)

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

    print(f"  Total classes found: {len(data)}")

    # Show all unique class types found (for debugging)
    if data:
        all_types = set(cls.get('name', '') for cls in data)
        print(f"  Class types in data: {', '.join(sorted(all_types))}")

    # Analyze classes
    available_classes = analyze_classes(data)

    if not available_classes:
        print("\n" + "="*80)
        print("No RIDE/Performance classes found in the target categories.")
        print("(These classes may only be scheduled on certain weekdays)")
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
