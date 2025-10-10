#!/bin/bash

# RSI-MA Analytics Dashboard - Quick Start Script

set -e

echo "=================================================="
echo "RSI-MA Performance Analytics Dashboard"
echo "Quick Start Script"
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

echo "✓ Python $(python3 --version) detected"
echo "✓ Node.js $(node --version) detected"

# Backend setup
echo ""
echo "Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q -r requirements.txt

# Create cache directory
mkdir -p cache

echo "✓ Backend setup complete"

# Frontend setup
echo ""
echo "Setting up frontend..."
cd ../frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
else
    echo "✓ Dependencies already installed"
fi

echo "✓ Frontend setup complete"

# Return to root
cd ..

echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "To start the application:"
echo ""
echo "1. Start Backend (Terminal 1):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python api.py"
echo ""
echo "2. Start Frontend (Terminal 2):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "Then visit: http://localhost:3000"
echo ""
echo "Or use Docker Compose:"
echo "   docker-compose up -d"
echo ""
echo "=================================================="
