"""
Perpetua Schedule Auto-Updater
Runs the checker multiple times to build up the schedule
"""
from perpetua_checker import check_perpetua_classes
from datetime import datetime
import time

def update_schedule(num_runs=3):
    """Run the Perpetua checker multiple times to accumulate classes"""

    print("=" * 80)
    print("PERPETUA SCHEDULE AUTO-UPDATER")
    print("=" * 80)
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Will run {num_runs} times to catch more classes")
    print("=" * 80)
    print()

    for i in range(1, num_runs + 1):
        print(f"\n{'='*80}")
        print(f"RUN {i} of {num_runs}")
        print(f"{'='*80}\n")

        try:
            check_perpetua_classes(use_persistent=True)
        except Exception as e:
            print(f"Error during run {i}: {e}")
            print("Continuing to next run...")

        # Small delay between runs (except after last run)
        if i < num_runs:
            print(f"\nWaiting 5 seconds before next run...")
            time.sleep(5)

    print("\n" + "=" * 80)
    print("UPDATE COMPLETE")
    print("=" * 80)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Schedule saved to: perpetua_schedule.json")
    print("=" * 80)
    print()

if __name__ == "__main__":
    import sys

    # Allow specifying number of runs as command line argument
    num_runs = 3
    if len(sys.argv) > 1:
        try:
            num_runs = int(sys.argv[1])
        except ValueError:
            print("Usage: python auto_update_schedule.py [num_runs]")
            print("Example: python auto_update_schedule.py 5")
            sys.exit(1)

    update_schedule(num_runs)
