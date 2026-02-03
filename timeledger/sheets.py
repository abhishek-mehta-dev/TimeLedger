import gspread
from google.oauth2.service_account import Credentials
import os
import json
from .tracker import WorkTracker
from datetime import datetime, timezone, timedelta

# Scopes required for Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def append_daily_summary(date: str) -> bool:
    """
    Append a daily work summary row to the configured Google Sheet.
    Returns True if successful, False otherwise.
    """
    try:
        # 1. Load configuration
        sheet_url = os.getenv('GOOGLE_SHEET_URL')
        service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        creds_path = os.path.join(os.getcwd(), 'credentials.json')
        
        if not sheet_url:
            print("Google Sheets Error: GOOGLE_SHEET_URL not set in .env")
            return False

        # 2. Authenticate
        creds = None
        if service_account_json:
            service_account_json = service_account_json.strip()
            # Check if it's raw JSON content (starts with {) or a file path
            if service_account_json.startswith('{'):
                try:
                    info = json.loads(service_account_json)
                    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
                    print("Google Sheets: Using raw JSON content from GOOGLE_SERVICE_ACCOUNT_JSON.")
                except Exception as e:
                    print(f"Google Sheets Error: Failed to parse raw JSON: {e}")
                    return False
            elif os.path.exists(service_account_json):
                try:
                    creds = Credentials.from_service_account_file(service_account_json, scopes=SCOPES)
                    print(f"Google Sheets: Using credentials from path provided in environment: {service_account_json}")
                except Exception as e:
                    print(f"Google Sheets Error: Failed to load from path {service_account_json}: {e}")
                    return False
            else:
                print(f"Google Sheets Error: GOOGLE_SERVICE_ACCOUNT_JSON provided but is neither valid JSON nor a valid file path.")
                return False
        elif os.path.exists(creds_path):
            creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
            print("Google Sheets: Using credentials from default 'credentials.json' file.")
        else:
            print("Google Sheets Error: No credentials found (check .env for GOOGLE_SERVICE_ACCOUNT_JSON or root for 'credentials.json').")
            return False
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url(sheet_url)
        worksheet = spreadsheet.get_worksheet(0) # Use the first tab

        # Header check: If worksheet is empty, add professional headers
        if not worksheet.get_all_values():
            headers = [
                "DATE", "FIRST START", "LAST END", "WORK DURATION", 
                "BREAK DURATION", "TOTAL SPAN", "PRODUCTIVITY %", "LAST SYNC (LOCAL)"
            ]
            worksheet.append_row(headers)

        # 3. Get daily stats
        tracker = WorkTracker()
        stats = tracker.get_stats_for_date(date)
        
        if not stats.work_seconds and not stats.break_seconds:
            print(f"Google Sheets Log: No activity for {date}")
            return False

        # 4. Helper for local time conversion
        def to_local_str(dt):
            if not dt: return "N/A"
            # stats.first_start is already a datetime object (often UTC-naive or aware)
            # Ensure it's treated correctly and converted to local time
            if dt.tzinfo is None:
                from datetime import timezone
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone().strftime("%I:%M:%S %p")

        # 5. Helper for duration formatting (HH:MM:SS)
        def format_dur(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            return f"{h:02d}:{m:02d}:{s:02d}"

        # 6. Prepare row data
        prod_ratio = 0.0
        if stats.total_span_seconds > 0:
            prod_ratio = (stats.work_seconds / stats.total_span_seconds) * 100

        row = [
            date,
            to_local_str(stats.first_start),
            to_local_str(stats.last_end),
            format_dur(stats.work_seconds),
            format_dur(stats.break_seconds),
            format_dur(stats.total_span_seconds),
            f"{prod_ratio:.1f}%",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Sync Time is already local
        ]

        # 7. Append row
        worksheet.append_row(row)
        print(f"Google Sheets: Sync successful for {date}")
        return True

    except Exception as e:
        print(f"Google Sheets Sync Error: {e}")
        return False
