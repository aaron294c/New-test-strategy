#!/bin/bash

# Trading Framework Dashboard Startup Script
echo "=================================================="
echo "   Trading Framework Dashboard - Quick Start"
echo "=================================================="
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

# Check if we need to use the framework HTML
if [ ! -f "index-framework.html" ]; then
    echo "❌ Framework HTML file not found!"
    exit 1
fi

echo "🚀 Starting Trading Framework Dashboard..."
echo ""
echo "📊 Dashboard Features:"
echo "   ✓ Market Regime Detection (Momentum/Mean Reversion)"
echo "   ✓ Percentile-Based Entry Logic"
echo "   ✓ Risk-Adjusted Expectancy Calculator"
echo "   ✓ Composite Instrument Scoring & Rankings"
echo "   ✓ Active Position & Risk Monitoring"
echo "   ✓ Multi-Timeframe Analysis (1m to 1d)"
echo ""
echo "🌐 Dashboard will open at: http://localhost:3000"
echo "🔄 Auto-refresh: Every 5 seconds"
echo "🎨 Theme: Dark mode optimized for trading"
echo ""
echo "=================================================="
echo ""

# Start Vite with the framework configuration
VITE_HTML_FILE=index-framework.html npm run dev

# Alternative: if you want to specify the HTML file directly in vite config:
# npx vite --config vite.config.ts --open index-framework.html
