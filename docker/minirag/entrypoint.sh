#!/bin/bash
set -e

echo "Running database migration"
cd /app/models/db__schemes/minirag/
alembic upgrade head
cd /app

echo "Starting application with command: $@"

if [ -z "$1" ]; then
    echo "No command provided via Docker CMD, starting uvicorn default..."
    exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
else
    # وإلا قم بتشغيل الأمر القادم من Dockerfile
    exec "$@"
fi