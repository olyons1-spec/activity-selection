"""
Activity Logger
Simple CLI tool to log completed activities
Usage:
  python log_activity.py run                    # Log a run today
  python log_activity.py run yesterday          # Log yesterday's run
  python log_activity.py cycle                  # Log a cycle today
  python log_activity.py spin                   # Log spin class today
  python log_activity.py sauna                  # Log sauna session
  python log_activity.py climbing               # Log climbing session
  python log_activity.py swim                   # Log a swim session
  python log_activity.py hike "Trail Name"      # Log a hike
"""
import json
import sys
from datetime import datetime, timedelta

ACTIVITY_LOG_FILE = 'activity_log.json'

# Activity configurations
ACTIVITY_CONFIGS = {
    'run': {
        'duration_minutes': 45,
        'location': 'Ringsend Park'
    },
    'cycle': {
        'duration_minutes': 90,
        'location': 'Phoenix Park Circuit'
    },
    'spin': {
        'duration_minutes': 60,
        'location': 'Perpetua Fitness'
    },
    'sauna': {
        'duration_minutes': 60,
        'location': 'Sláinte Wellness'
    },
    'climbing': {
        'duration_minutes': 120,
        'location': 'Awesome Walls Finglas'
    },
    'hike': {
        'duration_minutes': 180,  # Default 3 hours
        'location': 'Wicklow Mountains'
    },
    'gym': {
        'duration_minutes': 60,
        'location': 'Gym'
    },
    'swim': {
        'duration_minutes': 90,
        'location': 'Dublin (North Wall)'
    }
}

def load_activity_log():
    """Load activity log from JSON file"""
    try:
        with open(ACTIVITY_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'activities': []}

def save_activity_log(log):
    """Save activity log to JSON file"""
    with open(ACTIVITY_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

def log_activity(activity_type, date=None, trail_name=None, notes=None):
    """
    Log an activity

    Args:
        activity_type: Type of activity (run, spin, sauna, hike, gym)
        date: Date string 'YYYY-MM-DD' or 'today'/'yesterday' (default: today)
        trail_name: For hikes, the trail name
        notes: Optional notes
    """

    # Parse date
    if date is None or date == 'today':
        activity_date = datetime.now()
    elif date == 'yesterday':
        activity_date = datetime.now() - timedelta(days=1)
    else:
        try:
            activity_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            print(f"Error: Invalid date format '{date}'. Use YYYY-MM-DD, 'today', or 'yesterday'")
            return False

    date_str = activity_date.strftime('%Y-%m-%d')

    # Validate activity type
    if activity_type not in ACTIVITY_CONFIGS:
        print(f"Error: Unknown activity type '{activity_type}'")
        print(f"Valid types: {', '.join(ACTIVITY_CONFIGS.keys())}")
        return False

    # Get activity config
    config = ACTIVITY_CONFIGS[activity_type]

    # Create activity entry
    activity = {
        'type': activity_type,
        'date': date_str,
        'duration_minutes': config['duration_minutes'],
        'location': config['location'],
        'timestamp': datetime.now().isoformat()
    }

    # Add optional fields
    if trail_name:
        activity['trail_name'] = trail_name
    if notes:
        activity['notes'] = notes

    # Load log and add activity
    log = load_activity_log()

    # Check for duplicate (same type and date)
    existing = [a for a in log['activities'] if a['type'] == activity_type and a['date'] == date_str]
    if existing:
        print(f"\nWarning: Already logged a {activity_type} on {activity_date.strftime('%A, %B %d')}:")
        print(f"  {existing[0]}")
        response = input("\nAdd another entry anyway? (y/n): ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return False

    log['activities'].append(activity)
    save_activity_log(log)

    # Confirm
    print("\n" + "="*60)
    print("ACTIVITY LOGGED")
    print("="*60)
    print(f"Type: {activity_type.title()}")
    print(f"Date: {activity_date.strftime('%A, %B %d, %Y')}")
    print(f"Location: {activity['location']}")
    if trail_name:
        print(f"Trail: {trail_name}")
    print(f"Duration: {activity['duration_minutes']} minutes")
    if notes:
        print(f"Notes: {notes}")
    print("="*60)

    # Show recent activity summary
    print(f"\nRecent {activity_type} activities:")
    recent = [a for a in log['activities'] if a['type'] == activity_type]
    recent.sort(key=lambda x: x['date'], reverse=True)
    for a in recent[:5]:
        trail_info = f" ({a['trail_name']})" if 'trail_name' in a else ""
        print(f"  - {a['date']}{trail_info}")

    return True

def show_recent_activities(days=7):
    """Show recent activities"""
    log = load_activity_log()

    if not log['activities']:
        print("No activities logged yet.")
        return

    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    recent = [a for a in log['activities'] if a['date'] >= cutoff_date]
    recent.sort(key=lambda x: x['date'], reverse=True)

    print(f"\n{'='*60}")
    print(f"RECENT ACTIVITIES (Past {days} days)")
    print(f"{'='*60}\n")

    if not recent:
        print(f"No activities in the past {days} days.")
    else:
        for activity in recent:
            date_obj = datetime.strptime(activity['date'], '%Y-%m-%d')
            trail_info = f" - {activity['trail_name']}" if 'trail_name' in activity else ""
            print(f"{date_obj.strftime('%a %b %d')}: {activity['type'].title()} ({activity['duration_minutes']}min){trail_info}")

    print(f"\n{'='*60}\n")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python log_activity.py <type> [date] [trail_name] [--notes \"note text\"]")
        print()
        print("Examples:")
        print("  python log_activity.py run")
        print("  python log_activity.py run yesterday")
        print("  python log_activity.py spin")
        print("  python log_activity.py hike \"Spinc and Glenealo Valley\"")
        print("  python log_activity.py run --notes \"Felt great!\"")
        print()
        print("  python log_activity.py recent           # Show recent activities")
        print()
        print(f"Activity types: {', '.join(ACTIVITY_CONFIGS.keys())}")
        return

    command = sys.argv[1].lower()

    # Special command: show recent
    if command == 'recent':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        show_recent_activities(days)
        return

    # Parse arguments
    activity_type = command
    date = None
    trail_name = None
    notes = None

    # Check for date argument
    if len(sys.argv) > 2 and not sys.argv[2].startswith('--'):
        date_or_trail = sys.argv[2]
        # If it's a date keyword or date format
        if date_or_trail in ['today', 'yesterday'] or '-' in date_or_trail:
            date = date_or_trail
            # Check for trail name after date
            if len(sys.argv) > 3 and not sys.argv[3].startswith('--'):
                trail_name = sys.argv[3]
        else:
            # It's a trail name
            trail_name = date_or_trail

    # Check for notes flag
    if '--notes' in sys.argv:
        notes_idx = sys.argv.index('--notes')
        if len(sys.argv) > notes_idx + 1:
            notes = sys.argv[notes_idx + 1]

    # Log the activity
    success = log_activity(activity_type, date, trail_name, notes)

    if success:
        print("\nUse 'python log_activity.py recent' to see recent activities")

if __name__ == "__main__":
    main()
