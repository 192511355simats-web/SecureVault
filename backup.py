
import os
import hashlib
from datetime import datetime

from database import get_connection, initialize_database
from encryption import encrypt_file, BACKUP_FOLDER


def calculate_hash(file_path):
    """Calculate SHA-256 hash of the original file."""

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def create_backup(file_path):
    """Create an encrypted backup with automatic version management."""

    initialize_database()

    if not os.path.isfile(file_path):
        raise FileNotFoundError("Original file not found.")

    file_name = os.path.basename(file_path)

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Find the previous backup version for this filename
        cursor.execute(
            """
            SELECT MAX(version)
            FROM backups
            WHERE file_name = ?
            """,
            (file_name,)
        )

        result = cursor.fetchone()
        version = (result[0] or 0) + 1

        # Calculate original file hash
        file_hash = calculate_hash(file_path)

        # Encrypt the original file
        temporary_path, key_version = encrypt_file(file_path)

        # Create a unique encrypted backup filename
        encrypted_filename = f"{file_name}_v{version}.enc"

        encrypted_path = os.path.join(
            BACKUP_FOLDER,
            encrypted_filename
        )

        # Move temporary encrypted file to versioned location
        os.replace(temporary_path, encrypted_path)

        backup_date = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Save backup details in SQLite
        cursor.execute(
            """
            INSERT INTO backups
            (
                file_name,
                encrypted_path,
                version,
                file_hash,
                key_version,
                backup_date,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                file_name,
                encrypted_path,
                version,
                file_hash,
                key_version,
                backup_date,
                "Created"
            )
        )

        backup_id = cursor.lastrowid

        connection.commit()

        print("\n========== BACKUP CREATED ==========")
        print("Backup ID:", backup_id)
        print("File Name:", file_name)
        print("Version:", version)
        print("Encryption: AES-256-GCM")
        print("Hash Algorithm: SHA-256")
        print("Key Version:", key_version)
        print("Encrypted File:", encrypted_path)
        print("Status: Created")
        print("====================================\n")

        return backup_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def show_backup_history():
    """Display all backup versions."""

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM backups ORDER BY id DESC"
    )

    records = cursor.fetchall()

    connection.close()

    print("\n========== BACKUP HISTORY ==========")

    if not records:
        print("No backup records found.")

    for record in records:
        print(
            f"ID: {record['id']} | "
            f"File: {record['file_name']} | "
            f"Version: {record['version']} | "
            f"Status: {record['status']}"
        )

    print("====================================\n")

    return records
