@echo off
REM Perpetua Schedule Auto-Updater
REM Runs the Perpetua checker 3 times to build up the schedule

cd /d "D:\Coding Projects\activity-selection"

REM Run the Python auto-updater (runs checker 3 times)
python auto_update_schedule.py 3

REM Optional: Keep window open to see results (uncomment for manual testing)
REM pause
