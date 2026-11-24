from contextlib import contextmanager
from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "store.sqlite3"


@contextmanager
def get_connection(database_path=DATABASE_PATH):
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_schema(database_path=DATABASE_PATH):
    with get_connection(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS rarities (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                color TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS brainrots (
                id INTEGER PRIMARY KEY,
                slug TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
                stock INTEGER NOT NULL CHECK (stock >= 0),
                image_path TEXT NOT NULL,
                category_id INTEGER NOT NULL REFERENCES categories(id),
                rarity_id INTEGER NOT NULL REFERENCES rarities(id)
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                total_cents INTEGER NOT NULL,
                user_id INTEGER REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL REFERENCES orders(id),
                brainrot_id INTEGER NOT NULL REFERENCES brainrots(id),
                name TEXT NOT NULL,
                price_cents INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                image_path TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS seed_migrations (
                migration_key TEXT PRIMARY KEY
            );

            CREATE TABLE IF NOT EXISTS app_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL
            );
            """
        )
        order_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(orders)")
        }
        if "user_id" not in order_columns:
            connection.execute(
                "ALTER TABLE orders ADD COLUMN user_id INTEGER REFERENCES users(id)"
            )
