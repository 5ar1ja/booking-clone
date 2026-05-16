#!/bin/sh
set -e

REDIS_HOST="${REDIS_HOST:-redis}"

# echo "Waiting for Redis..."
# until redis-cli -h "$REDIS_HOST" ping | grep -q "PONG"; do
#     echo "  Redis not ready, retrying in 1s..."
#     sleep 1
# done
# echo "Redis is up!"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Compiling translations..."
python manage.py compilemessages || true

echo "Starting: $*"
exec "$@"
