"""
App module for TimeLedger - Main application logic and orchestration.
Provides high-level functions for running the application.
"""

import os
import sys

from .ui import create_app
from .db import test_connection, close_connection


def check_environment() -> bool:
    """
    Check if the environment is properly configured.
    
    Returns:
        True if environment is ready, False otherwise
    """
    env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    env_exists = os.path.exists('.env') or os.path.exists(env_file)
    
    if not env_exists:
        print("⚠️  No .env file found!")
        print("   Please create a .env file with:")
        print("   MONGODB_URI=your_mongodb_atlas_connection_string")
        print()
        return False
    
    return True


def run() -> int:
    """
    Run the TimeLedger application.
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    print("Starting TimeLedger...")
    print("=" * 40)
    
    # Check environment
    check_environment()
    
    try:
        # Create and run the application
        root = create_app()
        print("✓ Application window created")
        print("✓ Ready to track your work hours!")
        print("=" * 40)
        print()
        
        # Start the main event loop
        root.mainloop()
        
        return 0
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        return 0
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        return 1
    finally:
        close_connection()
        print("\nTimeLedger closed. Have a great day!")


def main():
    """Main entry point."""
    sys.exit(run())


if __name__ == "__main__":
    main()
