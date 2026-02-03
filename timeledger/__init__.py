"""
TimeLedger - Personal Work Hours Tracker

A desktop application for tracking work and break hours with MongoDB Atlas
storage and CSV report generation.
"""

__version__ = "1.0.0"
__author__ = "TimeLedger"

from .tracker import WorkTracker, State, Action, InvalidTransitionError, TimeStats
from .db import test_connection, DatabaseConnectionError
from .report import generate_report, generate_today_report
from .ui import create_app

__all__ = [
    "WorkTracker",
    "State", 
    "Action",
    "InvalidTransitionError",
    "TimeStats",
    "test_connection",
    "DatabaseConnectionError",
    "generate_report",
    "generate_today_report",
    "create_app",
]
