#!/bin/bash
set -e

host="$DATABASE_HOST"
port="$DATABASE_PORT"

echo "Waiting for database at $host:$port..."

while ! nc -z $host $port; do
  sleep 1
done

echo "Database is up!"
exec "$@"
