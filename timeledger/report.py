"""
Report module for TimeLedger - CSV report generation.
Generates daily reports with summary and event timeline.
"""

import os
import csv
import hashlib
from datetime import datetime
from typing import Optional

from .db import get_events_for_date, store_report_hash
from .tracker import WorkTracker


def format_duration(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    if seconds < 0:
        seconds = 0
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_time(timestamp_str: str) -> str:
    """Format ISO timestamp to local readable time."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        local_dt = dt.astimezone()
        return local_dt.strftime("%I:%M:%S %p")
    except (ValueError, AttributeError):
        return timestamp_str


def generate_report(
    date: str,
    output_dir: Optional[str] = None,
    store_hash: bool = True
) -> str:
    """
    Generate a CSV report for the specified date.
    
    Args:
        date: The date in YYYY-MM-DD format
        output_dir: Directory to save the report (defaults to current directory)
        store_hash: Whether to store the report hash in MongoDB
    
    Returns:
        The path to the generated report file
    """
    # Get events and stats
    events = get_events_for_date(date)
    tracker = WorkTracker()
    stats = tracker.get_stats_for_date(date)
    
    # Prepare output path
    if output_dir is None:
        output_dir = os.getcwd()
    
    filename = f"{date}-TimeLedger.csv"
    filepath = os.path.join(output_dir, filename)
    
    # Write CSV file
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Title
        writer.writerow(["TimeLedger Daily Report"])
        writer.writerow(["Date", date])
        writer.writerow([])
        
        # Summary Section
        writer.writerow(["=== SUMMARY ==="])
        writer.writerow(["Field", "Value"])
        writer.writerow(["Date", date])
        writer.writerow([
            "First Start", 
            format_time(stats.first_start.isoformat()) if stats.first_start else "N/A"
        ])
        writer.writerow([
            "Last End", 
            format_time(stats.last_end.isoformat()) if stats.last_end else "N/A"
        ])
        writer.writerow(["Total Span", format_duration(stats.total_span_seconds)])
        writer.writerow(["Total Break Time", format_duration(stats.break_seconds)])
        writer.writerow(["Net Work Time", format_duration(stats.work_seconds)])
        writer.writerow(["Number of Breaks", stats.break_count])
        writer.writerow([])
        
        # Break Reasons Section (if any)
        if stats.break_reasons:
            writer.writerow(["=== BREAK REASONS ==="])
            writer.writerow(["Break #", "Reason"])
            for i, reason in enumerate(stats.break_reasons, 1):
                writer.writerow([f"Break {i}", reason])
            writer.writerow([])
        
        # Event Timeline Section
        writer.writerow(["=== EVENT TIMELINE ==="])
        writer.writerow(["#", "Time (Local)", "Action", "Reason"])
        
        for i, event in enumerate(events, 1):
            writer.writerow([
                i,
                format_time(event.get("timestamp", "")),
                event.get("action", ""),
                event.get("reason", "-")
            ])
        
        writer.writerow([])
        
        # Footer
        writer.writerow([
            "Report generated at:",
            datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
        ])
    
    # Calculate and store hash
    if store_hash:
        try:
            sha256_hash = calculate_file_hash(filepath)
            store_report_hash(date, filename, sha256_hash)
        except Exception:
            pass  # Hash storage is optional, don't fail on error
    
    return filepath


def calculate_file_hash(filepath: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    
    return sha256.hexdigest()


def generate_today_report(output_dir: Optional[str] = None) -> str:
    """Generate report for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    return generate_report(today, output_dir)
