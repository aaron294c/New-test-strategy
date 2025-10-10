# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd rsi-ma-analytics-dashboard

# Run the setup script
./start.sh
```

Then open two terminals:

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python api.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Visit **http://localhost:3000** in your browser.

### Option 2: Docker (Easiest)

```bash
# Start everything with Docker Compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

Visit **http://localhost:3000** in your browser.

### Option 3: Manual Setup

#### Backend

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python api.py
```

Backend runs on **http://localhost:8000**

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on **http://localhost:3000**

## 📊 First Analysis

### Run Initial Backtest

```bash
cd backend
source venv/bin/activate
python enhanced_backtester.py
```

This will:
1. ✅ Fetch 5 years of data for 8 default tickers
2. ✅ Calculate RSI-MA indicators
3. ✅ Run D1-D21 backtests
4. ✅ Generate performance matrices
5. ✅ Export results to JSON

**Expected Runtime**: 2-5 minutes depending on your internet connection

### View Results

1. **Open Dashboard**: http://localhost:3000
2. **Select Ticker**: Choose from AAPL, MSFT, NVDA, etc.
3. **Select Threshold**: 5%, 10%, or 15%
4. **Explore Tabs**:
   - Performance Matrix: Heatmap of returns by percentile and day
   - Return Analysis: Distribution charts with confidence intervals
   - Optimal Exit: Recommended exit strategy with statistical validation

## 🎯 Key Features to Try

### 1. Performance Matrix Heatmap
- Hover over cells to see sample size, confidence, and success rate
- Darker green = higher returns
- Red = negative returns
- Yellow = neutral

### 2. Return Distribution
- Shows median return path with 68% and 95% confidence bands
- Overlay shows market benchmark for comparison
- Interactive tooltips for each day

### 3. Optimal Exit Strategy
- Recommended exit day based on return efficiency
- Target percentile range for exit
- Statistical trend analysis with p-values
- Risk metrics summary

## 🔍 Example Queries

### Via API (curl)

```bash
# Get backtest for AAPL
curl http://localhost:8000/api/backtest/AAPL

# Get performance matrix for threshold 5%
curl http://localhost:8000/api/performance-matrix/AAPL/5

# Get optimal exit strategy
curl http://localhost:8000/api/optimal-exit/AAPL/5

# Run Monte Carlo simulation
curl -X POST http://localhost:8000/api/monte-carlo/AAPL \
  -H "Content-Type: application/json" \
  -d '{"num_simulations": 1000, "max_periods": 21}'
```

### Via Python

```python
from backend.enhanced_backtester import EnhancedPerformanceMatrixBacktester

# Create backtester
backtester = EnhancedPerformanceMatrixBacktester(
    tickers=["AAPL"],
    max_horizon=21
)

# Run analysis
results = backtester.run_analysis()

# Print summary
backtester.print_summary()

# Export results
backtester.export_to_json("my_analysis.json")
```

### Via Frontend

Just use the interactive dashboard! No code required.

## 🐛 Troubleshooting

### Backend won't start

**Problem**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend won't start

**Problem**: `Cannot find module '@mui/material'`

**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### No data for ticker

**Problem**: Empty results or "Failed to fetch data"

**Solutions**:
- Check internet connection
- Try a different ticker (some may have limited data)
- Reduce lookback period in settings
- Wait a moment and try again (rate limiting)

### Port already in use

**Problem**: `Address already in use: 8000` or `3000`

**Solutions**:
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different ports
# Backend: uvicorn api:app --port 8001
# Frontend: Edit vite.config.ts and change port
```

## 📚 Next Steps

1. **Explore Documentation**: See README.md for comprehensive guide
2. **API Docs**: Visit http://localhost:8000/docs for Swagger UI
3. **Customize Parameters**: Edit backtester settings for your needs
4. **Add Tickers**: Modify DEFAULT_TICKERS in api.py
5. **Export Data**: Use dashboard export buttons for CSV/Excel

## 🎓 Learning Resources

### Understanding the Strategy

1. **RSI-MA Indicator**: 14-period RSI smoothed with 14-period EMA
2. **Percentile Ranking**: Where current RSI-MA sits in 500-period history
3. **Entry Signal**: When percentile falls below threshold (oversold)
4. **Exit Strategy**: Based on return efficiency and percentile reversion

### Reading the Heatmap

- **Green cells**: Profitable outcomes
- **Red cells**: Losing outcomes
- **Sample size**: More samples = higher confidence
- **Confidence levels**: VH > H > M > L > VL

### Interpreting Statistics

- **Win Rate**: % of trades that are profitable
- **Median Return**: Middle value (50th percentile)
- **±1σ (68%)**: One standard deviation band
- **±2σ (95%)**: Two standard deviation band
- **p-value < 0.05**: Statistically significant trend

## 💡 Pro Tips

1. **Start with 5% threshold** for conservative analysis
2. **Focus on high-confidence cells** (VH or H)
3. **Compare multiple tickers** to find best opportunities
4. **Use Monte Carlo** for forward-looking projections
5. **Export results** before running new analysis

## 🎉 You're Ready!

Your dashboard is now running. Start exploring!

**Questions?** Check the main README.md or API docs at http://localhost:8000/docs
