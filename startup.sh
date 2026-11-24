#!/bin/bash
set -euo pipefail

export SECUREVAULT_DATA_DIR="${SECUREVAULT_DATA_DIR:-/home/site/securevault-data}"
PORT="${PORT:-8000}"

exec gunicorn --workers 1 --threads 4 --bind "0.0.0.0:${PORT}" --access-logfile - --error-logfile - app:app
