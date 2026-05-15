#!/bin/bash

echo "======================================"
echo "    Loading Seed Data into Database   "
echo "======================================"

# Determine the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment if it exists
if [ -f "$DIR/../venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$DIR/../venv/bin/activate"
fi

cd "$DIR"

# Run the Django management command
python manage.py load_seed_data

echo "======================================"
echo "         Data Loading Complete        "
echo "======================================"
