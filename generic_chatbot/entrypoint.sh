#!/bin/bash
# Apply database migrations
python manage.py migrate --noinput
# Collect static files
python manage.py collectstatic --noinput
# Execute the command passed to the container
exec "$@"