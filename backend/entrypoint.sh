#!/bin/bash
set -e

echo "Waiting for postgres..."
while ! nc -z localhost 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Running migrations..."
POSTGRES_HOST=localhost alembic upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
