# Activity Selection - Sauna Availability Checker

Quick Python script to check real-time availability for Slainte Saunas in Dublin.

## What it does

Queries the Wunderbook API directly to check sauna availability for the next few days. No browser needed - just pure API calls.

## Features

- Checks today, tomorrow, and day after (before 9pm) or tomorrow and day after (after 9pm)
- Shows all time slots with availability
- Displays capacity and booking status
- Highlights bookable slots

## Usage

```bash
python sauna_checker.py
```

## Requirements

```bash
pip install requests
```

## Setup

The script uses an auth token that you'll need to get from your browser:

1. Log into [Slainte Saunas booking page](https://flutterwbdev.azurewebsites.net/#/tenantDetails?tenantName=slainte_saunas)
2. Open DevTools (F12) → Network tab
3. Click on a date to trigger an API call
4. Find the POST request to `ListScheduledEventsNEW`
5. Copy the Authorization Bearer token from the request headers
6. Update `AUTH_TOKEN` in `sauna_checker.py`

## Example Output

```
Current time: 11:47 PM
After 9pm - checking tomorrow and day after tomorrow

================================================================================
SLAINTE SAUNA AVAILABILITY CHECKER - ALL TIMES
================================================================================

Checking tomorrow (Saturday, October 18, 2025)...
  Found 6 time slot(s)

Saturday, October 18, 2025:
----------------------------------------
  [OK] 10:00 - 10/12 spots available
      >>> BOOKABLE! <<<
  [OK] 11:00 - 10/12 spots available
      >>> BOOKABLE! <<<
  [OK] 12:00 - 9/12 spots available
      >>> BOOKABLE! <<<
```

## Notes

- Auth token expires periodically and needs to be refreshed
- Built for personal use with Slainte Saunas booking system
- Can be adapted for other Wunderbook-powered booking systems

## How it was built

This started as a Playwright browser automation project but evolved into a direct API integration after inspecting network traffic and reverse-engineering the booking API.
