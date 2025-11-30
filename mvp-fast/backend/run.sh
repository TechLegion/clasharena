#!/bin/bash

# Run the ClashArena MVP application

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Load environment variables
if [ -f "../.env" ]; then
    export $(cat ../.env | xargs)
fi

# Run the application
python main.py

