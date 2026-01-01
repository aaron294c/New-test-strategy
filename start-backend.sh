#!/bin/bash

# Start Backend Script
set -e

echo "=================================================="
echo "Starting RSI-MA Analytics Backend"
echo "=================================================="

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Create cache directory if it doesn't exist
mkdir -p cache

echo ""
echo "✓ Backend environment ready"
echo "✓ Starting API server on http://localhost:8000"
echo "✓ API Documentation: http://localhost:8000/docs"
echo ""

# Start the backend (FastAPI via uvicorn)
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:-1}"

if [ "$RELOAD" = "1" ]; then
  uvicorn api:app --host "$HOST" --port "$PORT" --reload
else
  uvicorn api:app --host "$HOST" --port "$PORT"
fi
