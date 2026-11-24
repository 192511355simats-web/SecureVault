
import os
import hashlib
from datetime import datetime

from database import get_connection, initialize_database
from encryption import decrypt_file
from storage import RESTORE_FOLDER


def record_audit(file_name, version, action, status):
    """Save recovery activity in the audit database."""

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    operation_date = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute(
        """
        INSERT INTO audit_logs
        (file_name, version, action, operation_date, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            file_name,
            version,
            action,
            operation_date,
            status
        )
    )

    connection.commit()
    connection.close()


def restore_backup(backup_id):
    """Restore a selected encrypted backup."""

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM backups WHERE id = ?",
        (backup_id,)
    )

    backup = cursor.fetchone()
    connection.close()

    if backup is None:
        return "Backup record not found."

    file_name = backup["file_name"]
    encrypted_path = backup["encrypted_path"]
    version = backup["version"]
    key_version = backup["key_version"]
    original_hash = backup["file_hash"]

    output_name = f"{os.path.splitext(file_name)[0]}_v{version}{os.path.splitext(file_name)[1]}"

    output_path = os.path.join(
        RESTORE_FOLDER,
        output_name
    )

    try:
        if not os.path.isfile(encrypted_path):
            raise FileNotFoundError("Encrypted backup not found.")

        # Decrypt selected backup
        decrypt_file(
            encrypted_path,
            output_path,
            key_version
        )

        # Verify restored content using SHA-256
        sha256 = hashlib.sha256()

        with open(output_path, "rb") as restored_file:
            for chunk in iter(
                lambda: restored_file.read(4096),
                b""
            ):
                sha256.update(chunk)

        restored_hash = sha256.hexdigest()

        if restored_hash != original_hash:
            os.remove(output_path)
            raise ValueError("Restored file integrity check failed.")

        record_audit(
            file_name,
            version,
            "Selective Restore",
            "Success"
        )

        print("\n========== RESTORE COMPLETED ==========")
        print("File:", file_name)
        print("Version:", version)
        print("Restored Location:", output_path)
        print("Status: Success")
        print("=======================================\n")

        return f"Backup restored successfully: {output_path}"

    except Exception as error:

        record_audit(
            file_name,
            version,
            "Selective Restore",
            "Failed"
        )

        return f"Restore failed: {error}"


def show_available_backups():
    """Display available backups for restoration."""

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM backups ORDER BY id DESC"
    )

    records = cursor.fetchall()

    connection.close()

    print("\n========== AVAILABLE BACKUPS ==========")

    if not records:
        print("No backups available.")

    for record in records:
        print(
            f"ID: {record['id']} | "
            f"File: {record['file_name']} | "
            f"Version: {record['version']} | "
            f"Status: {record['status']}"
        )

    print("========================================\n")

    return records


def show_recovery_audit():
    """Display recovery audit history."""

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM audit_logs ORDER BY id DESC"
    )

    records = cursor.fetchall()

    connection.close()

    print("\n========== RECOVERY AUDIT ==========")

    if not records:
        print("No recovery activities found.")

    for record in records:
        print(
            f"File: {record['file_name']} | "
            f"Version: {record['version']} | "
            f"Action: {record['action']} | "
            f"Date: {record['operation_date']} | "
            f"Status: {record['status']}"
        )

    print("====================================\n")

    return records
