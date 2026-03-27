#!/bin/bash
# Build script for Render.com

set -e

echo "Installing dependencies..."
pip install -r requirements/base.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Applying migrations..."
python manage.py migrate

echo "Build complete!"
