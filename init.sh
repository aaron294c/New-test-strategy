#!/bin/bash

#############################################################################
# Project Initialization Script
# RSI-MA Performance Analytics Dashboard
#
# This script:
# - Installs backend dependencies (Python)
# - Installs frontend dependencies (Node.js)
# - Starts development servers
# - Performs smoke tests
# - Reports success
#
# Usage: ./init.sh
#############################################################################

set -e  # Exit on error

echo "============================================================================="
echo "RSI-MA Performance Analytics Dashboard - Initialization"
echo "============================================================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

#############################################################################
# 1. Check Prerequisites
#############################################################################

echo "Step 1: Checking prerequisites..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed${NC}"
    echo "Please install Python 3.9+ and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}ERROR: Node.js is not installed${NC}"
    echo "Please install Node.js 18+ and try again"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✓${NC} Node.js $NODE_VERSION found"

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}ERROR: npm is not installed${NC}"
    echo "Please install npm and try again"
    exit 1
fi

NPM_VERSION=$(npm --version)
echo -e "${GREEN}✓${NC} npm $NPM_VERSION found"

echo ""

#############################################################################
# 2. Backend Setup
#############################################################################

echo "Step 2: Setting up backend..."
echo ""

cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${YELLOW}⚠${NC} Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓${NC} Virtual environment activated"

# Install dependencies
echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓${NC} Backend dependencies installed"

# Verify key packages
echo "Verifying backend packages..."
python3 -c "import fastapi; import pandas; import numpy; import yfinance" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Backend packages verified"
else
    echo -e "${RED}ERROR: Failed to verify backend packages${NC}"
    exit 1
fi

cd ..

echo ""

#############################################################################
# 3. Frontend Setup
#############################################################################

echo "Step 3: Setting up frontend..."
echo ""

cd frontend

# Install dependencies
if [ -d "node_modules" ]; then
    echo -e "${YELLOW}⚠${NC} node_modules exists, skipping npm install (use 'npm install' to update)"
else
    echo "Installing frontend dependencies..."
    npm install --silent
    echo -e "${GREEN}✓${NC} Frontend dependencies installed"
fi

# Verify key packages
echo "Verifying frontend packages..."
node -e "require('react'); require('@mui/material'); require('plotly.js')" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Frontend packages verified"
else
    echo -e "${RED}ERROR: Failed to verify frontend packages${NC}"
    exit 1
fi

cd ..

echo ""

#############################################################################
# 4. Start Development Servers
#############################################################################

echo "Step 4: Starting development servers..."
echo ""

# Start backend server in background
echo "Starting backend server on http://localhost:8000..."
cd backend
source venv/bin/activate
nohup python api.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
cd ..
echo -e "${GREEN}✓${NC} Backend server started (PID: $BACKEND_PID)"

# Wait for backend to start
echo "Waiting for backend to be ready..."
sleep 3

# Check if backend is running
for i in {1..10}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Backend health check passed"
        break
    fi

    if [ $i -eq 10 ]; then
        echo -e "${RED}ERROR: Backend failed to start${NC}"
        echo "Check /tmp/backend.log for details"
        exit 1
    fi

    sleep 1
done

# Start frontend server in background
echo "Starting frontend server on http://localhost:3000..."
cd frontend
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo -e "${GREEN}✓${NC} Frontend server started (PID: $FRONTEND_PID)"

echo ""

#############################################################################
# 5. Smoke Tests
#############################################################################

echo "Step 5: Running smoke tests..."
echo ""

# Test backend API
echo "Testing backend API endpoints..."

# Health check
if curl -s http://localhost:8000/api/health | grep -q "status"; then
    echo -e "${GREEN}✓${NC} Health endpoint working"
else
    echo -e "${RED}✗${NC} Health endpoint failed"
fi

# Tickers list
if curl -s http://localhost:8000/api/tickers | grep -q "tickers"; then
    echo -e "${GREEN}✓${NC} Tickers endpoint working"
else
    echo -e "${RED}✗${NC} Tickers endpoint failed"
fi

# Wait for frontend
echo "Waiting for frontend to start..."
sleep 5

# Test frontend (simple check if port is open)
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Frontend server responding"
else
    echo -e "${YELLOW}⚠${NC} Frontend may still be starting (this is normal)"
fi

echo ""

#############################################################################
# 6. Success Message
#############################################################################

echo "============================================================================="
echo -e "${GREEN}INITIALIZATION COMPLETE!${NC}"
echo "============================================================================="
echo ""
echo "Your development environment is ready:"
echo ""
echo "  📊 Backend API:  http://localhost:8000"
echo "     - Swagger UI: http://localhost:8000/docs"
echo "     - ReDoc:      http://localhost:8000/redoc"
echo ""
echo "  🖥️  Frontend:    http://localhost:3000"
echo ""
echo "Process IDs:"
echo "  - Backend:  $BACKEND_PID"
echo "  - Frontend: $FRONTEND_PID"
echo ""
echo "Logs:"
echo "  - Backend:  /tmp/backend.log"
echo "  - Frontend: /tmp/frontend.log"
echo ""
echo "To stop servers:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Next Steps:"
echo "  1. Open http://localhost:3000 in your browser"
echo "  2. Read /project_memory/todo/next_task.md for first coding task"
echo "  3. Review /project_memory/context.md for project structure"
echo ""
echo "============================================================================="

exit 0
