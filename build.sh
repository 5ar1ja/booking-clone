#!/usr/bin/env bash
# exit on error
set -o errexit

# Install production dependencies
pip install -r requirements/prod.txt

# Run Django management commands
cd booking_clone
python manage.py collectstatic --no-input
python manage.py migrate
