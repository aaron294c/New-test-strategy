#!/bin/bash

# Quick Start - Starts both backend and frontend

echo "Starting RSI-MA Analytics Dashboard..."
echo ""

# Start backend in background
cd backend
python -m uvicorn api:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to initialize
sleep 2

# Start frontend
cd ../frontend
npx vite --port 3000

# Kill backend when frontend exits
kill $BACKEND_PID 2>/dev/null || true
