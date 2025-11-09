"""
Database Management Script

This script provides commands to initialize or update the application's database.
- 'create': Creates the database tables and populates them from the JSON data.
- 'rebuild': Drops all existing tables and completely rebuilds the database.
"""
import sys
from database import create_tables, populate_db_from_json, DB_PATH
import os

def rebuild_database():
    """Drops existing tables and rebuilds the database from scratch."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Existing database dropped.")
    print("Creating and populating new database...")
    create_tables()
    populate_db_from_json()
    print("Database rebuild complete.")

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run src/manage_db.py [create|rebuild]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "create":
        if os.path.exists(DB_PATH):
            print("Database already exists. Use 'rebuild' to start from scratch.")
        else:
            create_tables()
            populate_db_from_json()
    elif command == "rebuild":
        rebuild_database()
    else:
        print(f"Unknown command: {command}")
        print("Usage: uv run src/manage_db.py [create|rebuild]")
        sys.exit(1)

if __name__ == "__main__":
    main()
