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
echo "✓ Starting development server on 0.0.0.0:3000..."
echo "✓ Dashboard will be available at: http://localhost:3000"
echo ""

# Start the frontend (vite.config.ts already has host: 0.0.0.0)
npm run dev
