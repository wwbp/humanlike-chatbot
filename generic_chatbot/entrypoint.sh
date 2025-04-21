#!/bin/bash
set -e

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Load your bots
echo "Loading bots..."
python manage.py load_bots

echo "Starting Gunicorn..."
# start X‑Ray daemon, listening on all interfaces
xray -o -n "${AWS_REGION:-us-east-1}" &
# Finally, run the command passed in the Dockerfile CMD or via `docker run`
exec "$@"
