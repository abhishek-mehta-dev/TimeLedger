#!/usr/bin/env python3
"""
TimeLedger - Personal Work Hours Tracker

A desktop application for tracking work and break hours with MongoDB Atlas
storage and CSV report generation.

Usage:
    python main.py

Requirements:
    - Python 3.12+
    - MongoDB Atlas account with connection URI in .env file
    - Dependencies: pymongo, python-dotenv

Author: TimeLedger
License: MIT
"""

import os
import sys

# Ensure we're running from the correct directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from timeledger.app import run


if __name__ == "__main__":
    sys.exit(run())
