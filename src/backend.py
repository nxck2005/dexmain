import sqlite3
import json
import random
from .database import get_db_connection, JSON_PATH

DB_ERROR_MESSAGE = (
    "Database error. Please run 'uv run src/manage_db.py rebuild' "
    "to create or rebuild the database."
)

def get_all_pokemon() -> list[dict]:
    """Fetches a list of all Pokémon from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM pokemon ORDER BY id LIMIT 1025")
        pokemon_list = [{"id": row["id"], "name": row["name"]} for row in cursor.fetchall()]
        conn.close()
        return pokemon_list
    except sqlite3.Error:
        # Fallback to JSON
        try:
            with open(JSON_PATH, "r") as f:
                all_data = json.load(f)
            return [{"id": p["id"], "name": p["name"]} for p in all_data]
        except (IOError, json.JSONDecodeError):
            return []

def get_dex_entry(name_or_id: str) -> dict:
    """
    Fetches a detailed Pokédex entry for a given Pokémon name or ID from the database.
    Falls back to JSON file if the database query fails.
    """
    if str(name_or_id) == "1773":
        return {
            "name": "Definery", "id": 1773, "types": ["dark"], "abilities": ["thief"],
            "height": random.randint(1, 100), "weight": random.randint(1, 2000),
            "stats": {
                "hp": random.randint(1, 255), "attack": random.randint(1, 255),
                "defense": random.randint(1, 255), "special-attack": random.randint(1, 255),
                "special-defense": random.randint(1, 255), "speed": random.randint(1, 255),
            },
            "flavor_text": "sonned by all",
        }

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
                                                SELECT 
                                                    p.id, p.name, p.height, p.weight, p.flavor_text, p.ascii_art,
                                                    s.hp, s.attack, s.defense, s.special_attack, s.special_defense, s.speed, 
                                                    (SELECT GROUP_CONCAT(t.name) FROM pokemon_types pt JOIN types t ON pt.type_id = t.id WHERE pt.pokemon_id = p.id) as types, 
                                                    (SELECT GROUP_CONCAT(a.name) FROM pokemon_abilities pa JOIN abilities a ON pa.ability_id = a.id WHERE pa.pokemon_id = p.id)
                                     as abilities                        FROM pokemon p
            LEFT JOIN stats s ON p.id = s.pokemon_id
            WHERE p.id = ? OR lower(p.name) = ?;
        """
        
        param = str(name_or_id).lower()
        cursor.execute(query, (param, param))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return {"error": f"Entry '{name_or_id}' not found."}

        return {
            "name": row["name"].capitalize(),
            "id": row["id"],
            "types": row["types"].split(',') if row["types"] else [],
            "abilities": row["abilities"].split(',') if row["abilities"] else [],
            "height": row["height"],
            "weight": row["weight"],
            "stats": {
                "hp": row["hp"], "attack": row["attack"], "defense": row["defense"],
                "special-attack": row["special_attack"], "special-defense": row["special_defense"],
                "speed": row["speed"],
            },
            "flavor_text": row["flavor_text"],
            "ascii_art": row["ascii_art"],
        }

    except sqlite3.Error:
        # Fallback to JSON
        try:
            with open(JSON_PATH, "r") as f:
                all_data = json.load(f)
            
            search_term = str(name_or_id).lower()
            for p in all_data:
                if str(p["id"]) == search_term or p["name"].lower() == search_term:
                    return p
            return {"error": f"Entry '{name_or_id}' not found in JSON fallback."}
        except (IOError, json.JSONDecodeError):
            return {"error": DB_ERROR_MESSAGE}