#!/bin/sh
# wait-for-db.sh

host="$DATABASE_HOST"
user="$DATABASE_USER"
password="$DATABASE_PASSWORD"

until mysql -h "$host" -u "$user" -p"$password" -e 'SELECT 1' > /dev/null 2>&1; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 1
done

python manage.py load_bots

>&2 echo "MySQL is up - executing command: $@"
exec "$@"