
import os
import secrets
import hashlib
from datetime import datetime

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from database import get_connection, initialize_database
from encryption import generate_key, load_key
from storage import KEY_FOLDER


def rotate_encryption_keys():
    """Rotate the encryption key for all existing backups."""

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM backups ORDER BY id")
    backups = cursor.fetchall()

    if not backups:
        connection.close()
        return "No backups available for key rotation."

    # Generate a new AES-256 key
    new_key, new_version = generate_key()

    rotated_count = 0
    failed_count = 0

    for backup in backups:

        encrypted_path = backup["encrypted_path"]
        old_version = backup["key_version"]
        original_hash = backup["file_hash"]

        temporary_path = encrypted_path + ".tmp"

        try:
            if not os.path.isfile(encrypted_path):
                raise FileNotFoundError("Encrypted backup not found.")

            # Read existing encrypted backup
            with open(encrypted_path, "rb") as file:
                encrypted_data = file.read()

            if len(encrypted_data) < 28:
                raise ValueError("Encrypted backup is incomplete.")

            old_nonce = encrypted_data[:12]
            old_ciphertext = encrypted_data[12:]

            # Decrypt using the old key
            old_key = load_key(old_version)
            old_aes = AESGCM(old_key)

            original_data = old_aes.decrypt(
                old_nonce,
                old_ciphertext,
                None
            )

            # Verify original file content
            recovered_hash = hashlib.sha256(
                original_data
            ).hexdigest()

            if recovered_hash != original_hash:
                raise ValueError("Original file hash verification failed.")

            # Encrypt using the new key
            new_nonce = secrets.token_bytes(12)
            new_aes = AESGCM(new_key)

            new_ciphertext = new_aes.encrypt(
                new_nonce,
                original_data,
                None
            )

            # Write new encrypted data to temporary file
            with open(temporary_path, "wb") as file:
                file.write(new_nonce + new_ciphertext)
                file.flush()
                os.fsync(file.fileno())

            # Replace old encrypted file
            os.replace(temporary_path, encrypted_path)

            # Update backup key version
            cursor.execute(
                """
                UPDATE backups
                SET key_version = ?
                WHERE id = ?
                """,
                (new_version, backup["id"])
            )

            rotated_count += 1

        except Exception as error:
            failed_count += 1
            print(
                f"Key rotation failed for backup "
                f"{backup['id']}: {error}"
            )

            if os.path.exists(temporary_path):
                os.remove(temporary_path)

    # Save new key information
    key_path = os.path.join(KEY_FOLDER, f"key_v{new_version}.bin")

    cursor.execute(
        """
        INSERT INTO encryption_keys
        (key_version, key_path, created_date, status)
        VALUES (?, ?, ?, ?)
        """,
        (
            new_version,
            key_path,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Active"
        )
    )

    # Mark previously active database keys as retired
    cursor.execute(
        """
        UPDATE encryption_keys
        SET status = 'Retired'
        WHERE key_version != ?
        AND status = 'Active'
        """,
        (new_version,)
    )

    connection.commit()
    connection.close()

    print("\n========== KEY ROTATION REPORT ==========")
    print("New Key Version:", new_version)
    print("Successfully Rotated:", rotated_count)
    print("Failed Backups:", failed_count)
    print("=========================================\n")

    return (
        f"Key rotation completed. "
        f"Successful: {rotated_count}, Failed: {failed_count}, "
        f"New key version: {new_version}"
    )
