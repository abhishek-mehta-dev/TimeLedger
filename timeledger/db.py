"""
Database module for TimeLedger - MongoDB Atlas connection and event operations.
All operations are append-only for data integrity.
"""

import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Load environment variables
load_dotenv()

# MongoDB connection
_client: Optional[MongoClient] = None
_db: Optional[Database] = None

DATABASE_NAME = "timeledger"
EVENTS_COLLECTION = "events"
HASHES_COLLECTION = "report_hashes"


class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""
    pass


def get_client() -> MongoClient:
    """Get or create MongoDB client."""
    global _client
    
    if _client is None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise DatabaseConnectionError(
                "MONGODB_URI environment variable not set. "
                "Please create a .env file with your MongoDB Atlas connection string."
            )
        
        try:
            _client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                tls=True
            )
            # Test connection
            _client.admin.command('ping')
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            raise DatabaseConnectionError(f"Failed to connect to MongoDB Atlas: {e}")
    
    return _client


def get_db() -> Database:
    """Get the timeledger database."""
    global _db
    
    if _db is None:
        client = get_client()
        _db = client[DATABASE_NAME]
    
    return _db


def get_events_collection() -> Collection:
    """Get the events collection."""
    return get_db()[EVENTS_COLLECTION]


def insert_event(
    action: str,
    date: str,
    reason: Optional[str] = None
) -> str:
    """
    Insert a new event into the database (append-only).
    
    Args:
        action: The action type (START, PAUSE, RESUME, END)
        date: The date string in YYYY-MM-DD format
        reason: Optional reason (required for PAUSE)
    
    Returns:
        The inserted document's _id as string
    """
    now = datetime.now(timezone.utc)
    
    document = {
        "date": date,
        "timestamp": now.isoformat().replace("+00:00", "Z"),
        "action": action,
        "source": "TimeLedger",
        "created_at": now
    }
    
    if reason:
        document["reason"] = reason
    
    collection = get_events_collection()
    result = collection.insert_one(document)
    
    return str(result.inserted_id)


def get_events_for_date(date: str) -> List[Dict[str, Any]]:
    """
    Retrieve all events for a specific date, ordered by timestamp.
    
    Args:
        date: The date string in YYYY-MM-DD format
    
    Returns:
        List of event documents
    """
    collection = get_events_collection()
    
    events = list(collection.find(
        {"date": date},
        {"_id": 0}  # Exclude _id for cleaner output
    ).sort("created_at", 1))
    
    return events


def get_today_events() -> List[Dict[str, Any]]:
    """Get all events for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    return get_events_for_date(today)


def store_report_hash(date: str, filename: str, sha256_hash: str) -> str:
    """
    Store the SHA256 hash of a generated report for verification.
    
    Args:
        date: The date of the report
        filename: The report filename
        sha256_hash: The SHA256 hash of the report file
    
    Returns:
        The inserted document's _id as string
    """
    collection = get_db()[HASHES_COLLECTION]
    
    document = {
        "date": date,
        "filename": filename,
        "sha256": sha256_hash,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = collection.insert_one(document)
    return str(result.inserted_id)


def test_connection() -> bool:
    """Test the database connection."""
    try:
        get_client()
        return True
    except DatabaseConnectionError:
        return False


def close_connection():
    """Close the MongoDB connection."""
    global _client, _db
    
    if _client is not None:
        _client.close()
        _client = None
        _db = None
