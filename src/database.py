import sqlite3
import json
import os

DB_PATH = os.path.join("data", "pokedex.db")
JSON_PATH = os.path.join("data", "dex.json")

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Creates all the necessary tables in the database based on the schema."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Pokémon Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pokemon (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        height INTEGER,
        weight INTEGER,
        flavor_text TEXT,
        ascii_art TEXT
    );
    """)

    # App Data Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pokemon_app_data (
        pokemon_id INTEGER PRIMARY KEY,
        is_favorite INTEGER DEFAULT 0,
        search_count INTEGER DEFAULT 0,
        FOREIGN KEY (pokemon_id) REFERENCES pokemon (id)
    );
    """)

    # Types Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)

    # Pokémon-Types Linking Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pokemon_types (
        pokemon_id INTEGER,
        type_id INTEGER,
        PRIMARY KEY (pokemon_id, type_id),
        FOREIGN KEY (pokemon_id) REFERENCES pokemon (id),
        FOREIGN KEY (type_id) REFERENCES types (id)
    );
    """)

    # Abilities Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS abilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)

    # Pokémon-Abilities Linking Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pokemon_abilities (
        pokemon_id INTEGER,
        ability_id INTEGER,
        PRIMARY KEY (pokemon_id, ability_id),
        FOREIGN KEY (pokemon_id) REFERENCES pokemon (id),
        FOREIGN KEY (ability_id) REFERENCES abilities (id)
    );
    """)

    # Stats Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stats (
        pokemon_id INTEGER PRIMARY KEY,
        hp INTEGER,
        attack INTEGER,
        defense INTEGER,
        special_attack INTEGER,
        special_defense INTEGER,
        speed INTEGER,
        FOREIGN KEY (pokemon_id) REFERENCES pokemon (id)
    );
    """)

    # Evolutions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evolutions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_pokemon_id INTEGER,
        to_pokemon_id INTEGER,
        trigger TEXT,
        details TEXT,
        FOREIGN KEY (from_pokemon_id) REFERENCES pokemon (id),
        FOREIGN KEY (to_pokemon_id) REFERENCES pokemon (id)
    );
    """)

    # Moves Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS moves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        type_id INTEGER,
        power INTEGER,
        pp INTEGER,
        accuracy INTEGER,
        effect TEXT,
        FOREIGN KEY (type_id) REFERENCES types (id)
    );
    """)

    # Pokémon-Moves Linking Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pokemon_moves (
        pokemon_id INTEGER,
        move_id INTEGER,
        learn_method TEXT,
        level_learned INTEGER,
        PRIMARY KEY (pokemon_id, move_id, learn_method),
        FOREIGN KEY (pokemon_id) REFERENCES pokemon (id),
        FOREIGN KEY (move_id) REFERENCES moves (id)
    );
    """)

    conn.commit()
    conn.close()

def populate_db_from_json():
    """Populates the database from the dex.json file."""
    if not os.path.exists(JSON_PATH):
        print(f"Error: {JSON_PATH} not found. Cannot populate database.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    with open(JSON_PATH, "r") as f:
        all_pokemon_data = json.load(f)

    # Caches to avoid querying the DB repeatedly for IDs
    type_id_cache = {}
    ability_id_cache = {}

    # Pre-fill caches with existing data to be safe
    cursor.execute("SELECT id, name FROM types")
    for row in cursor.fetchall():
        type_id_cache[row['name']] = row['id']

    cursor.execute("SELECT id, name FROM abilities")
    for row in cursor.fetchall():
        ability_id_cache[row['name']] = row['id']

    try:
        cursor.execute("BEGIN")

        for pokemon in all_pokemon_data:
            # 1. Insert into pokemon table
            cursor.execute(
                "INSERT OR IGNORE INTO pokemon (id, name, height, weight, flavor_text, ascii_art) VALUES (?, ?, ?, ?, ?, ?)",
                (pokemon['id'], pokemon['name'], pokemon['height'], pokemon['weight'], pokemon.get('flavor_text', ''), pokemon.get('ascii_art', ''))
            )

            # 2. Insert into pokemon_app_data
            cursor.execute(
                "INSERT OR IGNORE INTO pokemon_app_data (pokemon_id) VALUES (?)",
                (pokemon['id'],)
            )

            # 3. Insert into stats
            stats = pokemon['stats']
            cursor.execute(
                """
                INSERT OR IGNORE INTO stats (pokemon_id, hp, attack, defense, special_attack, special_defense, speed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (pokemon['id'], stats.get('hp', 0), stats.get('attack', 0), stats.get('defense', 0),
                 stats.get('special-attack', 0), stats.get('special-defense', 0), stats.get('speed', 0))
            )

            # 4. Handle Types
            for type_name in pokemon['types']:
                if type_name not in type_id_cache:
                    cursor.execute("INSERT INTO types (name) VALUES (?)", (type_name,))
                    type_id_cache[type_name] = cursor.lastrowid
                type_id = type_id_cache[type_name]
                cursor.execute("INSERT OR IGNORE INTO pokemon_types (pokemon_id, type_id) VALUES (?, ?)", (pokemon['id'], type_id))

            # 5. Handle Abilities
            for ability_name in pokemon['abilities']:
                if ability_name not in ability_id_cache:
                    cursor.execute("INSERT INTO abilities (name) VALUES (?)", (ability_name,))
                    ability_id_cache[ability_name] = cursor.lastrowid
                ability_id = ability_id_cache[ability_name]
                cursor.execute("INSERT OR IGNORE INTO pokemon_abilities (pokemon_id, ability_id) VALUES (?, ?)", (pokemon['id'], ability_id))

        cursor.execute("COMMIT")
        print("Database populated successfully.")

    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"An error occurred: {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    print("Initializing database...")
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    create_tables()
    populate_database()
    print("Database initialization complete.")
