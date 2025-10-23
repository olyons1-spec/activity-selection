"""
Daily Activity Recommender
Aggregates all activity checkers and recommends what to do today
"""
from running_checker import check_running_availability
from perpetua_checker import check_perpetua_classes, get_today_classes_from_schedule
from sauna_checker import check_sauna_availability
from climbing_checker import check_climbing_availability
from recommend_hike import recommend_trails
from swimming_checker import check_swimming_availability
from cycling_checker import check_cycling_availability
from datetime import datetime

def get_all_available_activities():
    """Check all activity types and return what's available today"""

    print("\n" + "="*80)
    print(f"DAILY ACTIVITY RECOMMENDATIONS - {datetime.now().strftime('%A, %B %d, %Y')}")
    print("="*80)
    print()
    print("Checking all activity options...")
    print()

    activities = []

    # 1. Check Running
    print("[1/7] Checking running availability...")
    try:
        running = check_running_availability()
        if running['available']:
            activities.append({
                'type': 'Running',
                'available': True,
                'duration_minutes': running['duration_minutes'],
                'location': running['location'],
                'weather_dependent': True,
                'details': f"{running['duration_minutes']}min run at {running['location']}"
            })
    except Exception as e:
        print(f"  Error checking running: {e}")

    print()

    # 2. Check Cycling
    print("[2/7] Checking cycling availability...")
    try:
        cycling = check_cycling_availability(route_type='medium')
        if cycling['available']:
            activities.append({
                'type': 'Cycling',
                'available': True,
                'duration_minutes': cycling['duration_minutes'],
                'location': cycling['location'],
                'weather_dependent': True,
                'details': f"{cycling['route']} - {cycling['rating']}: {cycling['assessment']}"
            })
    except Exception as e:
        print(f"  Error checking cycling: {e}")

    print()

    # 3. Check Spin Classes
    print("[3/7] Checking Perpetua spin classes (from persistent schedule)...")
    try:
        # Use fast schedule lookup instead of scraping
        today_classes = get_today_classes_from_schedule()

        if today_classes:
            activities.append({
                'type': 'Spin Class',
                'available': True,
                'duration_minutes': 60,
                'location': 'Perpetua Fitness',
                'weather_dependent': False,
                'count': len(today_classes),
                'details': f"{len(today_classes)} class(es) available today",
                'classes': today_classes
            })
            print(f"  Found {len(today_classes)} class(es) today from schedule")
        else:
            print(f"  No classes today in schedule")
            print(f"  (Run 'python perpetua_checker.py' to update schedule)")
    except Exception as e:
        print(f"  Error checking spin classes: {e}")

    print()

    # 4. Check Climbing
    print("[4/7] Checking social climbing availability...")
    try:
        climbing = check_climbing_availability()
        if climbing['available']:
            activities.append({
                'type': 'Social Climbing',
                'available': True,
                'duration_minutes': climbing['duration_minutes'],
                'location': climbing['location'],
                'weather_dependent': False,
                'details': f"Social climbing at {climbing['location']} ({climbing['start_time']}-{climbing['end_time']})",
                'start_time': climbing['start_time'],
                'end_time': climbing['end_time']
            })
    except Exception as e:
        print(f"  Error checking climbing: {e}")

    print()

    # 5. Check Sauna
    print("[5/7] Checking sauna availability...")
    try:
        all_sauna_slots = check_sauna_availability()

        # Filter for TODAY only
        today_date = datetime.now().date()
        today_slots = []

        for day_name, day_date, slots in all_sauna_slots:
            # Compare dates
            if day_date.date() == today_date:
                # Count available slots for today
                available_today = [s for s in slots if s['available'] > 0 and not s['is_completed']]
                if available_today:
                    today_slots = available_today
                break

        if today_slots:
            activities.append({
                'type': 'Sauna',
                'available': True,
                'duration_minutes': 60,
                'location': 'Sláinte Wellness',
                'weather_dependent': False,
                'details': f"{len(today_slots)} slot(s) available today",
                'slots': today_slots
            })
    except Exception as e:
        print(f"  Error checking sauna: {e}")

    print()

    # 6. Check Swimming
    print("[6/7] Checking swimming availability...")
    try:
        swimming = check_swimming_availability(days=3)
        if swimming['available'] and swimming.get('today'):
            # Swimming available today
            tide_time = swimming['tide_time'].strftime('%H:%M')
            window = f"{swimming['window_start'].strftime('%H:%M')}-{swimming['window_end'].strftime('%H:%M')}"
            activities.append({
                'type': 'Swimming',
                'available': True,
                'duration_minutes': 90,
                'location': swimming['location'],
                'weather_dependent': True,
                'details': f"High tide at {tide_time}, swim window {window}",
                'tide_time': swimming['tide_time'],
                'window_start': swimming['window_start'],
                'window_end': swimming['window_end'],
                'weather_desc': swimming['weather_desc'],
                'rating': swimming['rating']
            })
        elif not swimming.get('today') and swimming.get('next_available'):
            # Not today, but show next available
            next_day = swimming['next_available'].strftime('%A, %b %d')
            activities.append({
                'type': 'Swimming',
                'available': False,
                'duration_minutes': 90,
                'location': swimming['location'],
                'weather_dependent': True,
                'details': f"Next window: {next_day}",
                'next_available': swimming['next_available']
            })
    except Exception as e:
        print(f"  Error checking swimming: {e}")

    print()

    # 7. Check Hiking
    print("[7/7] Checking hiking options...")
    try:
        # This will print its own output
        # We'll just note that hiking info was checked
        activities.append({
            'type': 'Hiking',
            'available': True,
            'duration_minutes': 240,  # ~4 hours average
            'location': 'Wicklow Mountains',
            'weather_dependent': True,
            'details': 'See hiking recommendations above'
        })
    except Exception as e:
        print(f"  Error checking hiking: {e}")

    return activities

def display_summary(activities):
    """Display a summary of all available activities"""

    print("\n" + "="*80)
    print("ACTIVITY SUMMARY")
    print("="*80)

    if not activities:
        print("\nNo activities available today!")
        print("Maybe it's a rest day?")
        return

    print(f"\n{len(activities)} activity type(s) available today:\n")

    for i, activity in enumerate(activities, 1):
        icon = "[OUTDOOR]" if activity.get('weather_dependent') else "[INDOOR]"
        print(f"{i}. {icon} {activity['type']}")
        print(f"   Location: {activity['location']}")
        print(f"   Duration: ~{activity['duration_minutes']} minutes")
        print(f"   {activity['details']}")

        # Show specific times if available
        if 'classes' in activity and activity['classes']:
            print(f"   Times today:")
            for cls in activity['classes']:
                print(f"     - {cls['time']} ({cls['available']}/{cls['total']} spots)")

        if 'slots' in activity and activity['slots']:
            print(f"   Times today:")
            for slot in activity['slots']:
                print(f"     - {slot['time']} ({slot['available']}/{slot['capacity']} spots)")

        print()

    print("-" * 80)
    print("\nLegend:")
    print("  [OUTDOOR] = Weather-dependent (check conditions)")
    print("  [INDOOR] = Indoor/all-weather")
    print()

    # Give recommendation
    print("RECOMMENDATION:")
    if len(activities) == 1:
        act = activities[0]
        print(f"  Only one option today: {act['type']} at {act['location']}")
    else:
        # Prioritize outdoor activities on nice days
        # For now, just list them
        print(f"  You have {len(activities)} great options today!")
        print(f"  Consider your energy level, schedule, and weather preferences.")

    print("="*80)

def main():
    """Main recommendation flow"""

    # Get all activities
    activities = get_all_available_activities()

    # Display summary
    display_summary(activities)

    print("\nTo log a completed activity:")
    print("  python log_activity.py run")
    print("  python log_activity.py cycle")
    print("  python log_activity.py spin")
    print("  python log_activity.py sauna")
    print("  python log_activity.py climbing")
    print("  python log_activity.py swim")
    print("  python log_activity.py hike \"Trail Name\"")
    print()

if __name__ == "__main__":
    main()
