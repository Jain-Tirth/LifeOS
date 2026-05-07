#!/bin/sh
set -e

echo "Starting LifeOS backend..."
echo "DEBUG: $DEBUG"
echo "DB_ENGINE: $DB_ENGINE"

# Wait for database to be ready (especially for Cloud SQL)
if [ "$DB_ENGINE" = "postgres" ]; then
    echo "Waiting for PostgreSQL to be ready..."
    max_tries=30
    try=0
    while [ $try -lt $max_tries ]; do
        if python -c "import os; from django.db import connection; connection.cursor().execute('SELECT 1')" 2>/dev/null; then
            echo "Database is ready!"
            break
        fi
        try=$((try + 1))
        echo "Database not ready, waiting... ($try/$max_tries)"
        sleep 2
    done
    
    if [ $try -eq $max_tries ]; then
        echo "Warning: Could not verify database connection after $max_tries attempts"
    fi
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if it doesn't exist (optional, for initial setup)
if [ ! -z "$SUPERUSER_NAME" ] && [ ! -z "$SUPERUSER_PASSWORD" ]; then
    echo "Setting up superuser..."
    python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$SUPERUSER_NAME').exists():
    User.objects.create_superuser('$SUPERUSER_NAME', '$SUPERUSER_NAME', '$SUPERUSER_PASSWORD')
    print("Superuser created!")
else:
    print("Superuser already exists.")
END
fi

echo "Starting Gunicorn..."
exec gunicorn lifeos.wsgi:application \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info