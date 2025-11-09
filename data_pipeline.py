"""
A driver script to control the data pipeline for the Pokedex application.

This script provides a step-by-step process to:
1. Fetch all Pokémon data from the PokeAPI and save it to a local JSON file.
2. Populate the SQLite database from the local JSON file.

The user is prompted for confirmation before each major step.
"""

import asyncio
import json
import sqlite3
from pathlib import Path
import sys

from src.pull_data import main as fetch_api_data
from src.database import (
    create_tables,
    populate_db_from_json,
)


def confirm_step(prompt: str) -> bool:
    """Gets user confirmation for a given step, or bypasses if --yes is passed."""
    if "--yes" in sys.argv or "-y" in sys.argv:
        print(f"{prompt} [y/n]: y (auto-confirmed)")
        return True
    while True:
        response = input(f"{prompt} [y/n]: ").lower().strip()
        if response in ["y", "yes"]:
            return True
        if response in ["n", "no"]:
            return False
        print("Invalid input. Please enter 'y' or 'n'.")


def run_database_population():
    """
    Creates tables and populates the database using the data from dex.json.
    """
    print("--- Starting Database Population ---")
    create_tables()
    populate_db_from_json()
    print("--- Database Population Complete! ---")


async def main():
    """Main driver function."""
    print("--- Pokedex Data Pipeline Driver ---")

    # Phase 1: Fetch data from API
    if confirm_step("Phase 1: Do you want to fetch all data from the PokeAPI?"):
        print("Starting API data fetch. This may take a few moments...")
        await fetch_api_data()
        print("API data fetch complete. Data saved to dex.json.")
    else:
        print("Skipping API data fetch.")

    print("-" * 20)

    # Phase 2: Populate database
    if confirm_step("Phase 2: Do you want to populate the database from dex.json?"):
        run_database_population()
    else:
        print("Skipping database population.")

    print("\nData pipeline finished.")


if __name__ == "__main__":
    asyncio.run(main())
