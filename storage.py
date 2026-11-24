"""Locations for SecureVault's persistent runtime data."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(
    os.environ.get(
        "SECUREVAULT_DATA_DIR",
        "/home/site/securevault-data" if os.environ.get("WEBSITE_SITE_NAME") else BASE_DIR,
    )
)

DATABASE_PATH = os.path.join(DATA_DIR, "backup_system.db")
UPLOAD_FOLDER = os.path.join(DATA_DIR, "uploads")
KEY_FOLDER = os.path.join(DATA_DIR, "keys")
BACKUP_FOLDER = os.path.join(DATA_DIR, "backups")
RESTORE_FOLDER = os.path.join(DATA_DIR, "restored")

for directory in (DATA_DIR, UPLOAD_FOLDER, KEY_FOLDER, BACKUP_FOLDER, RESTORE_FOLDER):
    os.makedirs(directory, mode=0o700, exist_ok=True)
