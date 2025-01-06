#!/bin/sh
# wait-for-db.sh

set -e

host="$DATABASE_HOST"
shift
cmd="$@"

until mysql -h "$host" -u "$DATABASE_USER" -p"$DATABASE_PASSWORD" -e 'SELECT 1'; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "MySQL is up - executing command"
exec $cmd