"""
Sauna Availability Checker - Working API Version
Uses direct API calls with proper authentication and parameters
"""

import requests
from datetime import datetime, timedelta
import json

TENANT_ID = 459
API_URL = "https://api.wunderbook.com/api/services/app/MobileEventSchedule/ListScheduledEventsNEW"

# You'll need to get this token from your browser when logged in
# This token expires, so you'd need to update it periodically
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9uYW1laWRlbnRpZmllciI6IjEyMTM3MiIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL25hbWUiOiJvc2Nhci5seW9uc0BjYXBwZmluaXR5LmNvbSIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL2VtYWlsYWRkcmVzcyI6Im9zY2FyLmx5b25zQGNhcHBmaW5pdHkuY29tIiwiQXNwTmV0LklkZW50aXR5LlNlY3VyaXR5U3RhbXAiOiJIQ1RRSzZFMjdLVFBGQkVSV1FVSVo1WFBLTUNHU0hOUyIsInN1YiI6IjEyMTM3MiIsImp0aSI6IjEyMGZlMDI4LTI5MGQtNGMwYi1iMGU4LWMwZDVkMTA3NWNkMyIsImlhdCI6MTc1ODE5NDMyOCwidG9rZW5fdmFsaWRpdHlfa2V5IjoiNTYxMDZlZjAtYWQyMi00MTcwLWJjNjAtMDU2MDBmMDgwNmE1IiwidXNlcl9pZGVudGlmaWVyIjoiMTIxMzcyIiwidG9rZW5fdHlwZSI6IjAiLCJuYmYiOjE3NTgxOTQzMjgsImV4cCI6MTc4OTczMDMyOCwiaXNzIjoiV3VuZGVyYm9vayIsImF1ZCI6Ild1bmRlcmJvb2sifQ.ekNUwhinEEAu_K2pUXLqsGiiw2kyx-BvQyMqUq55r9E"

def get_events_for_date(date):
    """Get scheduled events for a specific date using the API"""

    # Format date as required by the API
    schedule_date = date.strftime('%Y-%m-%dT00:00:00')
    schedule_dt_str = date.strftime('%Y-%m-%dT18:30:00.000Z')

    # Build the exact payload structure from the captured request
    payload = {
        "isListView": True,
        "scheduleDate": schedule_date,
        "scheduleDtStr": schedule_dt_str,
        "TenantId": TENANT_ID,
        "timezoneOffsetInMinutes": 60,  # Adjust for your timezone
        "userEmailAddress": ""
    }

    headers = {
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "*/*"
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('result', [])
            else:
                print(f"  API returned success=false: {data.get('error')}")
                return None
        else:
            print(f"  HTTP {response.status_code}: {response.text[:200]}")
            return None

    except Exception as e:
        print(f"  Request failed: {e}")
        return None

def analyze_all_slots(events, date):
    """Analyze events and extract ALL time slot availability"""

    if not events:
        return []

    all_slots = []

    for event in events:
        start_time = event.get('startDateTime', '')

        if start_time:
            # Parse the time
            try:
                event_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

                total_bookings = event.get('totalBookings', 0)
                attendance_limit = event.get('attendanceLimit', 12)
                available = attendance_limit - total_bookings

                all_slots.append({
                    'time': event_time.strftime('%H:%M'),
                    'start': start_time,
                    'end': event.get('endDateTime', ''),
                    'booked': total_bookings,
                    'capacity': attendance_limit,
                    'available': available,
                    'is_completed': event.get('isEventCompleted', False)
                })
            except:
                pass

    return all_slots

def check_sauna_availability():
    """Check sauna availability for upcoming days"""

    now = datetime.now()
    current_hour = now.hour

    # Determine which days to check
    days_to_check = []

    if current_hour < 21:  # Before 9pm
        days_to_check = [
            ("today", now),
            ("tomorrow", now + timedelta(days=1)),
            ("day_after", now + timedelta(days=2))
        ]
        print(f"Current time: {now.strftime('%I:%M %p')}")
        print("Before 9pm - checking today, tomorrow, and day after tomorrow")
    else:  # 9pm or later
        days_to_check = [
            ("tomorrow", now + timedelta(days=1)),
            ("day_after", now + timedelta(days=2))
        ]
        print(f"Current time: {now.strftime('%I:%M %p')}")
        print("After 9pm - checking tomorrow and day after tomorrow")

    print("\n" + "="*80)
    print("SLAINTE SAUNA EVENING AVAILABILITY CHECKER")
    print("="*80)

    all_results = []

    for day_name, day_date in days_to_check:
        print(f"\nChecking {day_name} ({day_date.strftime('%A, %B %d, %Y')})...")

        events = get_events_for_date(day_date)

        if events:
            all_slots = analyze_all_slots(events, day_date)
            all_results.append((day_name, day_date, all_slots))

            if all_slots:
                print(f"  Found {len(all_slots)} time slot(s)")
            else:
                print(f"  No slots found")
        else:
            print(f"  Failed to fetch data")

    # Display results
    print("\n" + "="*80)
    print("FULL DAY AVAILABILITY SUMMARY")
    print("="*80)

    for day_name, day_date, slots in all_results:
        print(f"\n{day_date.strftime('%A, %B %d, %Y')}:")
        print("-" * 40)

        if not slots:
            print("  No evening slots available")
        else:
            for slot in slots:
                status = "COMPLETED" if slot['is_completed'] else f"{slot['available']}/{slot['capacity']} spots available"
                availability_icon = "X" if slot['is_completed'] or slot['available'] == 0 else "OK"

                print(f"  [{availability_icon}] {slot['time']} - {status}")
                if slot['available'] > 0 and not slot['is_completed']:
                    print(f"      >>> BOOKABLE! <<<")

    return all_results

if __name__ == "__main__":
    results = check_sauna_availability()

    print("\n" + "="*80)
    print("NOTE: Auth token expires periodically.")
    print("If this stops working, update AUTH_TOKEN at the top of this file")
    print("with a fresh token from your browser's DevTools.")
    print("="*80)
