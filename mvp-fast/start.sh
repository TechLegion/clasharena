#!/bin/bash
# Production startup script

echo "Starting ClashArena MVP..."

# Navigate to backend directory
cd backend

# Run database setup (if needed)
echo "Setting up database..."
python setup_database.py

# Start the application with Gunicorn
echo "Starting server..."
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:${PORT:-8000}

