# Setting Up Automated Perpetua Schedule Updates

This guide will help you set up automatic daily updates for your Perpetua class schedule.

## Option 1: Windows Task Scheduler (Recommended)

### Step-by-Step Instructions:

1. **Open Task Scheduler**
   - Press `Win + R`
   - Type `taskschd.msc` and press Enter
   - Or search for "Task Scheduler" in Start menu

2. **Create a New Task**
   - Click "Create Basic Task..." in the right panel
   - Name: `Perpetua Schedule Updater`
   - Description: `Updates Perpetua fitness class schedule daily`
   - Click "Next"

3. **Set Trigger**
   - Select "Daily"
   - Click "Next"
   - Set start time (recommended: **7:00 AM** - catches morning classes)
   - Recur every: 1 day
   - Click "Next"

4. **Set Action**
   - Select "Start a program"
   - Click "Next"
   - Program/script: `D:\Coding Projects\activity-selection\update_perpetua_schedule.bat`
   - Start in: `D:\Coding Projects\activity-selection`
   - Click "Next"

5. **Finish Setup**
   - Check "Open the Properties dialog when I click Finish"
   - Click "Finish"

6. **Configure Advanced Settings** (in Properties dialog)
   - Go to "General" tab:
     - ✅ Check "Run whether user is logged on or not"
     - ✅ Check "Run with highest privileges"
   - Go to "Conditions" tab:
     - ✅ Uncheck "Start the task only if the computer is on AC power"
     - ✅ Check "Wake the computer to run this task" (optional)
   - Go to "Settings" tab:
     - ✅ Check "Allow task to be run on demand"
     - ✅ Check "If the task fails, restart every: 10 minutes" (optional)
     - Attempt to restart up to: 3 times
   - Click "OK"

7. **Test It**
   - Right-click your new task
   - Select "Run"
   - Watch it execute in the background
   - Check `perpetua_schedule.json` to see it updated

### Recommended Schedule:

- **Daily at 7:00 AM** - Catches classes posted overnight
- **OR Daily at 9:00 PM** - If classes are posted in the evening

You can also set up **two runs per day** if classes get posted at different times.

---

## Option 2: Manual Run (If You Prefer Control)

Simply double-click `update_perpetua_schedule.bat` whenever you want to update the schedule.

Or run from command line:
```bash
cd "D:\Coding Projects\activity-selection"
update_perpetua_schedule.bat
```

---

## How It Works:

1. **The batch script runs 3 times** to catch more classes
2. **Each run scrapes Perpetua's website** and adds new classes to the schedule
3. **Existing classes are preserved** - never deleted
4. **Availability is updated** for classes seen again
5. **Schedule saved to**: `perpetua_schedule.json`

---

## Verifying It's Working:

### Check Last Update Time:
```bash
# View the schedule file
notepad perpetua_schedule.json

# Look for "last_updated" field at the bottom
```

### Check Today's Classes:
```bash
cd "D:\Coding Projects\activity-selection"
python daily_recommender.py
```

---

## Troubleshooting:

### Task Scheduler says "Task has not yet run"
- Make sure the trigger time hasn't passed yet today
- Try "Run" manually to test it works

### Script runs but schedule doesn't update
- Check Python is in your PATH
- Open CMD and run: `python --version`
- Make sure Playwright is installed: `pip install playwright`
- Run: `playwright install chromium`

### Script window closes immediately
- Open `update_perpetua_schedule.bat` in notepad
- Remove the `REM` before `pause` at the end
- This will keep the window open so you can see errors

---

## What Gets Updated:

- ✅ New classes are **added** to the schedule
- ✅ Existing classes get **availability updated**
- ✅ Past classes **stay in the file** (filtered out when displaying)
- ✅ Runs **3 times per execution** to catch more data
- ✅ Takes about **5-7 minutes** total per scheduled run

---

## Daily Workflow:

1. **Morning**: Task Scheduler auto-updates schedule at 7 AM
2. **Anytime**: Run `python daily_recommender.py` to see today's options (instant!)
3. **When new classes post**: Run `update_perpetua_schedule.bat` manually

---

## Files Created:

- `update_perpetua_schedule.bat` - The automation script
- `perpetua_schedule.json` - Your persistent class schedule
- This file (`SETUP_AUTOMATION.md`) - Setup instructions

---

## Need Help?

If Task Scheduler isn't working, you can also:
- Use Windows Startup folder (runs at login)
- Use third-party schedulers like System Scheduler
- Set a reminder and run the batch file manually each day
