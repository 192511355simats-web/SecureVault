
import os
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from storage import BACKUP_FOLDER, KEY_FOLDER


def generate_key():
    """Generate and securely store a 256-bit AES key."""

    existing_versions = []

    for filename in os.listdir(KEY_FOLDER):
        if filename.startswith("key_v") and filename.endswith(".bin"):
            try:
                version = int(filename[5:-4])
                existing_versions.append(version)
            except ValueError:
                continue

    new_version = max(existing_versions, default=0) + 1

    key = AESGCM.generate_key(bit_length=256)

    key_path = os.path.join(
        KEY_FOLDER,
        f"key_v{new_version}.bin"
    )

    with open(key_path, "wb") as key_file:
        key_file.write(key)

    return key, new_version


def get_latest_key():
    """Get the latest encryption key."""

    versions = []

    for filename in os.listdir(KEY_FOLDER):
        if filename.startswith("key_v") and filename.endswith(".bin"):
            try:
                versions.append(int(filename[5:-4]))
            except ValueError:
                continue

    if not versions:
        return generate_key()

    latest_version = max(versions)

    return load_key(latest_version), latest_version


def load_key(version):
    """Load an encryption key using its version."""

    key_path = os.path.join(
        KEY_FOLDER,
        f"key_v{version}.bin"
    )

    if not os.path.isfile(key_path):
        raise FileNotFoundError(
            f"Encryption key version {version} not found."
        )

    with open(key_path, "rb") as key_file:
        key = key_file.read()

    if len(key) != 32:
        raise ValueError("Invalid AES-256 key length.")

    return key


def encrypt_file(file_path):
    """Encrypt a file using AES-256-GCM."""

    if not os.path.isfile(file_path):
        raise FileNotFoundError("File not found.")

    key, key_version = get_latest_key()

    with open(file_path, "rb") as file:
        original_data = file.read()

    aesgcm = AESGCM(key)

    nonce = secrets.token_bytes(12)

    encrypted_data = aesgcm.encrypt(
        nonce,
        original_data,
        None
    )

    filename = os.path.basename(file_path)

    encrypted_path = os.path.join(
        BACKUP_FOLDER,
        filename + ".enc"
    )

    with open(encrypted_path, "wb") as encrypted_file:
        encrypted_file.write(nonce + encrypted_data)

    return encrypted_path, key_version


def decrypt_file(encrypted_path, output_path, key_version):
    """Decrypt an encrypted backup using its original key."""

    if not os.path.isfile(encrypted_path):
        raise FileNotFoundError("Encrypted backup not found.")

    with open(encrypted_path, "rb") as encrypted_file:
        encrypted_data = encrypted_file.read()

    if len(encrypted_data) < 28:
        raise ValueError("Encrypted file is incomplete or corrupted.")

    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]

    key = load_key(key_version)

    aesgcm = AESGCM(key)

    original_data = aesgcm.decrypt(
        nonce,
        ciphertext,
        None
    )

    output_directory = os.path.dirname(output_path)

    if output_directory:
        os.makedirs(output_directory, exist_ok=True)

    with open(output_path, "wb") as output_file:
        output_file.write(original_data)

    return output_path
