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

echo "Creating superuser (if not exists)..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
email = '${DJANGO_SUPERUSER_EMAIL:-admin@example.com}'
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        email=email,
        first_name='${DJANGO_SUPERUSER_FIRST_NAME:-Admin}',
        last_name='${DJANGO_SUPERUSER_LAST_NAME:-User}',
        password='${DJANGO_SUPERUSER_PASSWORD:-admin123}',
    )
    print('Superuser created:', email)
else:
    print('Superuser already exists:', email)
"

echo "Starting: $*"
exec "$@"
