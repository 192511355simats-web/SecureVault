
import os
import hashlib
import tempfile

from cryptography.exceptions import InvalidTag

from database import get_connection, initialize_database
from encryption import decrypt_file


def calculate_hash(data):
    """Calculate SHA-256 hash of file data."""

    return hashlib.sha256(data).hexdigest()


def verify_backup(backup_id):
    """Verify encrypted backup integrity."""

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM backups WHERE id = ?",
        (backup_id,)
    )

    backup = cursor.fetchone()

    if backup is None:
        connection.close()
        return "Backup record not found."

    encrypted_path = backup["encrypted_path"]
    key_version = backup["key_version"]
    original_hash = backup["file_hash"]

    try:
        if not os.path.isfile(encrypted_path):
            raise FileNotFoundError("Encrypted backup file not found.")

        # Decrypt into a temporary directory for verification
        with tempfile.TemporaryDirectory() as temp_directory:

            temporary_file = os.path.join(
                temp_directory,
                "verification_file"
            )

            decrypt_file(
                encrypted_path,
                temporary_file,
                key_version
            )

            with open(temporary_file, "rb") as file:
                recovered_data = file.read()

            recovered_hash = calculate_hash(recovered_data)

        if recovered_hash == original_hash:
            status = "Verified"
            message = "Backup integrity verified successfully."
        else:
            status = "Integrity Failed"
            message = "Backup content does not match the original."

    except InvalidTag:
        status = "Integrity Failed"
        message = "Backup authentication failed. Data may be modified."

    except Exception as error:
        status = "Integrity Failed"
        message = f"Integrity verification failed: {error}"

    # Update backup status
    cursor.execute(
        """
        UPDATE backups
        SET status = ?
        WHERE id = ?
        """,
        (status, backup_id)
    )

    connection.commit()
    connection.close()

    print("\n========== INTEGRITY REPORT ==========")
    print("Backup ID:", backup_id)
    print("File Name:", backup["file_name"])
    print("Status:", status)
    print("Result:", message)
    print("======================================\n")

    return message


def show_integrity_report():
    """Display integrity verification results."""

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, file_name, version, status
        FROM backups
        ORDER BY id DESC
        """
    )

    records = cursor.fetchall()

    connection.close()

    print("\n========== INTEGRITY REPORT ==========")

    if not records:
        print("No backup records found.")

    for record in records:
        print(
            f"ID: {record['id']} | "
            f"File: {record['file_name']} | "
            f"Version: {record['version']} | "
            f"Status: {record['status']}"
        )

    print("======================================\n")

    return records
