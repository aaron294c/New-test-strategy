#!/bin/bash

echo "🚀 RESTARTING DASHBOARD WITH DRAMATIC IMPROVEMENTS"
echo "=================================================="
echo ""

# Kill any existing processes
echo "Stopping any running servers..."
pkill -f "api.py" 2>/dev/null
pkill -f "vite" 2>/dev/null
pkill -f "uvicorn" 2>/dev/null
sleep 2

echo "✓ Stopped old servers"
echo ""

# Start backend
echo "Starting Backend..."
cd /workspace/backend
nohup python3 api.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "✓ Backend started (PID: $BACKEND_PID)"
echo "  View logs: tail -f /tmp/backend.log"
echo ""

# Wait for backend
sleep 3

# Start frontend
echo "Starting Frontend..."
cd /workspace/frontend
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✓ Frontend started (PID: $FRONTEND_PID)"
echo "  View logs: tail -f /tmp/frontend.log"
echo ""

sleep 5

echo "=================================================="
echo "✅ SERVERS ARE RUNNING!"
echo "=================================================="
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "🔥 WHAT YOU'LL SEE:"
echo "  • RSI Chart: 8PX SUPER THICK line"
echo "  • RSI Chart: 900PX tall (HUGE)"
echo "  • Default: Last 14 days (zoomed in)"
echo "  • Monte Carlo: MASSIVE green/red recommendation banner"
echo ""
echo "📝 Open browser to: http://localhost:5173"
echo "   Then press Ctrl+Shift+R to hard refresh"
echo ""
echo "To stop servers:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "To view logs:"
echo "  Backend:  tail -f /tmp/backend.log"
echo "  Frontend: tail -f /tmp/frontend.log"
echo "=================================================="
