
import sqlite3
from storage import DATABASE_PATH

DATABASE_NAME = DATABASE_PATH


def get_connection():
    """Create and return a database connection."""

    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """Create all required database tables."""

    connection = get_connection()
    cursor = connection.cursor()

    # Backup information and version management
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            encrypted_path TEXT NOT NULL,
            version INTEGER NOT NULL,
            file_hash TEXT NOT NULL,
            key_version INTEGER NOT NULL,
            backup_date TEXT NOT NULL,
            status TEXT DEFAULT 'Created'
        )
    """)

    # Backup scheduling
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            schedule_type TEXT NOT NULL,
            next_run TEXT NOT NULL,
            status TEXT DEFAULT 'Active'
        )
    """)

    # Encryption key management
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS encryption_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_version INTEGER NOT NULL,
            key_path TEXT NOT NULL,
            created_date TEXT NOT NULL,
            status TEXT DEFAULT 'Active'
        )
    """)

    # Recovery audit records
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            version INTEGER NOT NULL,
            action TEXT NOT NULL,
            operation_date TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")
