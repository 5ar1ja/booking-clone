#!/bin/bash
set -e
set -o pipefail

# ----------------------------------
# CONFIGURATION
# ----------------------------------

ENV_FILE="booking_clone/settings/.env"
VENV_DIR=".venv"
APP_DIR="booking_clone"
DJANGO_MANAGE="python $APP_DIR/manage.py"
SERVER_PORT=8000

SUPERUSER_EMAIL="admin@example.com"
SUPERUSER_PASSWORD="admin123"
SUPERUSER_FIRST_NAME="Admin"
SUPERUSER_LAST_NAME="User"

# ----------------------------------
# FUNCTIONS
# ----------------------------------

echo_step() {
    echo
    echo "==== $1 ===="
}

check_env_vars() {
    echo_step "Checking environment variables"

    if [ ! -f "$ENV_FILE" ]; then
        echo "Error: $ENV_FILE not found. Copy .env.example and fill in values."
        exit 1
    fi

    set -a
    # shellcheck source=/dev/null
    source "$ENV_FILE"
    set +a

    REQUIRED_VARS=("BOOKING_SECRET_KEY" "BOOKING_ENV_ID")
    MISSING_VARS=()

    for VAR in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!VAR}" ]; then
            MISSING_VARS+=("$VAR")
        fi
    done

    if [ ${#MISSING_VARS[@]} -ne 0 ]; then
        echo "Error: Missing required environment variables:"
        for VAR in "${MISSING_VARS[@]}"; do
            echo "  - $VAR"
        done
        exit 1
    fi

    echo "All required environment variables are set."
}

create_virtualenv() {
    echo_step "Setting up virtual environment"

    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        echo "Virtualenv created at $VENV_DIR"
    fi
    
    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
    
    pip install --upgrade pip -q
    pip install -r requirements/dev.txt -q
}

run_migrations() {
    echo_step "Running database migrations"
    
    $DJANGO_MANAGE migrate
}

compile_translations() {
    echo_step "Compiling translation files"
    
    $DJANGO_MANAGE compilemessages 2>/dev/null || echo "No translation files found, skipping"
}

create_superuser() {
    echo_step "Creating superuser (if not exists)"

    PYTHONPATH="$APP_DIR" DJANGO_SETTINGS_MODULE="settings.env.dev" python - <<END
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email="$SUPERUSER_EMAIL").exists():
    User.objects.create_superuser(
        email="$SUPERUSER_EMAIL",
        first_name="$SUPERUSER_FIRST_NAME",
        last_name="$SUPERUSER_LAST_NAME",
        password="$SUPERUSER_PASSWORD",
    )
    print("Superuser created")
else:
    print("Superuser already exists")
END
}

start_server() {
    echo_step "Starting Django development server"
    echo "  API:       http://127.0.0.1:$SERVER_PORT/api/"
    echo "  Swagger:   http://127.0.0.1:$SERVER_PORT/api/docs/"
    echo "  ReDoc:     http://127.0.0.1:$SERVER_PORT/api/redoc/"
    echo "  Admin:     http://127.0.0.1:$SERVER_PORT/admin/"
    echo "  Login:     $SUPERUSER_EMAIL / $SUPERUSER_PASSWORD"
    echo
    $DJANGO_MANAGE runserver 0.0.0.0:$SERVER_PORT
}

# ----------------------------------
# SCRIPT EXECUTION
# ----------------------------------

check_env_vars
create_virtualenv
run_migrations
compile_translations
create_superuser
start_server
