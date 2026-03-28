#!/bin/bash
# Build script for Render.com

set -e

echo "Installing dependencies..."
pip install -r requirements/base.txt

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Build complete!"
