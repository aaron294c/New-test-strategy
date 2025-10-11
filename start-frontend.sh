#!/bin/bash

# Start Frontend Script
set -e

echo "=================================================="
echo "Starting RSI-MA Analytics Frontend"
echo "=================================================="

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

echo ""
echo "✓ Frontend environment ready"
echo "✓ Starting development server..."
echo "✓ Dashboard will be available at: http://localhost:5173"
echo ""

# Start the frontend
npm run dev
