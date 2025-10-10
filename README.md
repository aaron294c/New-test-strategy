# RSI-MA Performance Analytics Dashboard

A comprehensive web-based analytics dashboard for visualizing and analyzing the performance characteristics of an RSI-MA percentile ranking trading strategy. Combines historical backtesting (D1-D21) with forward-looking Monte Carlo simulations.

## 🎯 Project Overview

This dashboard provides traders with actionable insights for:
- **Entry Timing**: When RSI-MA percentile falls below configurable thresholds (5%, 10%, 15%)
- **Exit Strategy Optimization**: Data-driven recommendations based on return efficiency analysis
- **Risk Assessment**: Comprehensive risk metrics including drawdowns, recovery times, and loss streaks
- **Forward-Looking Analysis**: Monte Carlo simulations for probability distributions

## 🚀 Quick Start

### Prerequisites

- **Backend**: Python 3.9+
- **Frontend**: Node.js 18+ and npm/yarn
- **Data**: Internet connection for fetching market data via yfinance

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
python api.py

# Or use uvicorn directly
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Running Full Analysis

```bash
# From the backend directory, run the backtester
cd backend
python enhanced_backtester.py
```

This will:
1. Fetch 5 years of historical data for default tickers
2. Calculate RSI-MA indicators and percentile rankings
3. Run backtests for D1-D21 holding periods
4. Generate performance matrices, risk metrics, and optimal exit strategies
5. Export results to `backtest_d1_d21_results.json`

## 📊 Core Features

### 1. Extended Backtesting (D1-D21)

**Previous Version**: D1-D7 analysis  
**Current Version**: D1-D21 comprehensive analysis

```python
backtester = EnhancedPerformanceMatrixBacktester(
    tickers=["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "QQQ", "SPY"],
    lookback_period=500,
    rsi_length=14,
    ma_length=14,
    max_horizon=21  # Extended to D21
)
```

**Key Improvements**:
- Track cumulative returns from entry through D1-D21
- Calculate individual daily returns (day-to-day changes)
- Monitor RSI-MA percentile movement throughout holding period
- Comprehensive risk metrics: drawdowns, recovery times, consecutive losses

### 2. Monte Carlo Simulation Engine

Forward-looking probability analysis based on First Passage Time methodology:

```python
from monte_carlo_simulator import MonteCarloSimulator

simulator = MonteCarloSimulator(
    ticker="AAPL",
    current_rsi_ma_percentile=15.5,
    current_price=175.50,
    historical_percentile_data=percentile_series,
    historical_price_data=price_series,
    num_simulations=1000,
    max_periods=21
)

# Run simulations
results = simulator.run_simulations()
fpt_results = simulator.calculate_first_passage_times([25, 50, 75, 90])
fan_chart = simulator.generate_fan_chart_data()
```

**Features**:
- Percentile movement projections with confidence bands
- First passage time calculations (time to reach target percentiles)
- Exit timing probability distributions
- Risk scenario analysis

### 3. Interactive Dashboard Components

#### Performance Matrix Heatmap
- **20 percentile ranges** × **21 days** = 420 data points per threshold
- Color-coded by return: Red (negative) → Yellow (neutral) → Green (positive)
- Hover tooltips show: sample size, confidence level, success rate, P25-P75 range
- Confidence indicators: VH (20+), H (10-19), M (5-9), L (3-4), VL (1-2) samples

#### Return Distribution Charts
- Median return paths with 68% (±1σ) and 95% (±2σ) confidence intervals
- Benchmark comparison overlay
- Interactive tooltips for detailed statistics
- Day-by-day progression visualization

#### Optimal Exit Strategy Panel
- **Return Efficiency Analysis**: Return % per day held
- **Recommended Exit Day**: Based on peak efficiency
- **Target Percentile Range**: Where to exit for optimal returns
- **Statistical Validation**: Trend significance testing with p-values
- **Risk Summary**: Drawdowns, recovery rates, consecutive losses

## 🏗️ Architecture

### Backend (Python/FastAPI)

```
backend/
├── enhanced_backtester.py    # D1-D21 backtesting engine
├── monte_carlo_simulator.py  # Forward-looking simulations
├── api.py                     # FastAPI REST endpoints
├── requirements.txt           # Python dependencies
└── cache/                     # Cached backtest results
```

**Key Endpoints**:
- `GET /api/backtest/{ticker}` - Get backtest results
- `POST /api/backtest/batch` - Run batch analysis
- `POST /api/monte-carlo/{ticker}` - Run Monte Carlo simulation
- `GET /api/performance-matrix/{ticker}/{threshold}` - Get performance matrix
- `GET /api/optimal-exit/{ticker}/{threshold}` - Get exit recommendations
- `POST /api/compare` - Compare multiple tickers

### Frontend (React/TypeScript)

```
frontend/
├── src/
│   ├── components/
│   │   ├── PerformanceMatrixHeatmap.tsx  # Heatmap visualization
│   │   ├── ReturnDistributionChart.tsx   # Distribution plots
│   │   └── OptimalExitPanel.tsx          # Exit strategy display
│   ├── api/
│   │   └── client.ts                      # API client
│   ├── types/
│   │   └── index.ts                       # TypeScript definitions
│   ├── App.tsx                            # Main application
│   └── main.tsx                           # Entry point
├── package.json
└── vite.config.ts
```

**Technology Stack**:
- **React 18** with TypeScript
- **Material-UI (MUI)** for UI components
- **Plotly.js** for interactive charts
- **TanStack Query** for data fetching
- **Zustand** for state management
- **Vite** for build tooling

## 📈 Strategy Details

### Core Indicator Calculation

```python
# 1. Calculate 14-period RSI
daily_returns = prices.pct_change()
delta = daily_returns.diff()
gains = delta.where(delta > 0, 0)
losses = -delta.where(delta < 0, 0)
avg_gains = gains.ewm(alpha=1/14, adjust=False).mean()
avg_losses = losses.ewm(alpha=1/14, adjust=False).mean()
rsi = 100 - (100 / (1 + avg_gains / avg_losses))

# 2. Apply 14-period EMA to RSI
rsi_ma = rsi.ewm(span=14, adjust=False).mean()

# 3. Calculate rolling 500-period percentile rank
percentile_rank = rolling_percentile_rank(rsi_ma, window=500)
```

### Entry Signals

Trades are triggered when RSI-MA percentile falls below threshold:
- **Conservative**: ≤ 5th percentile (extreme oversold)
- **Moderate**: ≤ 10th percentile
- **Aggressive**: ≤ 15th percentile

### Performance Tracking

For each entry event, track:
1. **Cumulative Returns**: Log returns from entry to each day (D1-D21)
2. **Daily Returns**: Day-to-day log return changes
3. **Percentile Movement**: How RSI-MA percentile evolves
4. **Risk Metrics**: Drawdowns from peak, recovery timing

## 📊 Sample Output

### Console Output

```
================================================================================
ENHANCED PERFORMANCE MATRIX BACKTESTER - D1-D21
================================================================================
Analyzing 8 tickers: AAPL, MSFT, NVDA, GOOGL, AMZN, META, QQQ, SPY
Entry thresholds: 5%, 10%, 15%
Holding period: D1 through D21
================================================================================

============================================================
Analyzing AAPL...
============================================================
Successfully fetched 1258 data points for AAPL

Processing threshold 5.0%...
  Found 45 entry events

Processing threshold 10.0%...
  Found 92 entry events

Processing threshold 15.0%...
  Found 138 entry events
```

### Performance Matrix (Sample)

```
Entry ≤5% - Complete D1-7 Matrix (45 events)
Percentile   │      D1      │      D2      │      D3      │ ... │      D21     │
─────────────┼──────────────┼──────────────┼──────────────┼─────┼──────────────┤
 0- 5%       │ +0.25% (12M) │ +0.48% (11M) │ +0.72% (10M) │ ... │ +2.15% (8M)  │
 5-10%       │ +0.30% (15H) │ +0.55% (14H) │ +0.85% (13H) │ ... │ +2.45% (11H) │
10-15%       │ +0.28% (18H) │ +0.51% (17H) │ +0.78% (16H) │ ... │ +2.30% (14H) │
...
95-100%      │ +0.10% (3L)  │ +0.15% (3L)  │ +0.20% (2L)  │ ... │ +0.50% (2L)  │
─────────────┼──────────────┼──────────────┼──────────────┼─────┼──────────────┤
Win Rate %   │     65.5%    │     68.2%    │     71.1%    │ ... │     75.5%    │
```

### Optimal Exit Strategy

```
📈 OPTIMAL EXIT STRATEGY:
  • Best Efficiency: D7 (+0.425%/day, +2.98% total)
  • Exit Target: When RSI-MA reaches 50-55% on D7
  • Historical Performance: +2.95% return, 72% success rate
  • Sample Confidence: 35 trades (H confidence)
  
  Efficiency Rankings:
  ⭐ D7: +0.425%/day (+2.98% total)
  2. D6: +0.418%/day (+2.51% total)
  3. D8: +0.395%/day (+3.16% total)
```

## 🔬 Statistical Analysis

### Trend Significance Testing

```python
# Pearson correlation for trend
correlation, p_value = pearsonr(days, median_returns)

# Mann-Whitney U test for early vs late returns
statistic, mw_p_value = mannwhitneyu(late_returns, early_returns, alternative='greater')
```

**Interpretation**:
- **p < 0.01**: Very strong trend (high confidence)
- **p < 0.05**: Statistically significant trend
- **p < 0.10**: Moderate evidence of trend
- **p ≥ 0.10**: Weak/no significant trend

### Risk Metrics

```python
RiskMetrics(
    median_drawdown=-2.5%,           # Median peak-to-trough decline
    p90_drawdown=-5.8%,              # 90th percentile worst drawdown
    median_recovery_days=3.0,         # Days to recover from drawdown
    recovery_rate=0.85,               # 85% of trades recover
    max_consecutive_losses=4,         # Longest losing streak
    avg_loss_magnitude=-1.2%          # Average loss when losing
)
```

## 🎨 Visualization Examples

### Color Schemes

```javascript
// Return heatmap colors
positive: ['#e8f5e9', '#81c784', '#4caf50', '#2e7d32']  // Light to dark green
negative: ['#ffebee', '#e57373', '#f44336', '#c62828']  // Light to dark red
neutral: '#fff9c4'  // Yellow for ~0%

// Percentile colors
veryLow:  '#1b5e20'   // Dark green (0-15%)
low:      '#4caf50'   // Green (15-35%)
neutral:  '#ffeb3b'   // Yellow (35-65%)
high:     '#ff9800'   // Orange (65-85%)
veryHigh: '#d32f2f'   // Red (85-100%)
```

## 🚀 Advanced Usage

### Custom Analysis

```python
# Run custom analysis with different parameters
backtester = EnhancedPerformanceMatrixBacktester(
    tickers=["YOUR_TICKER"],
    lookback_period=300,      # Shorter lookback
    rsi_length=10,            # Faster RSI
    ma_length=10,             # Faster MA
    max_horizon=14            # Shorter holding period
)

results = backtester.run_analysis()
backtester.export_to_json("custom_results.json")
```

### API Integration

```typescript
// Fetch backtest data
const response = await backtestApi.getBacktestResults('AAPL', true);

// Run Monte Carlo simulation
const mcResults = await monteCarloApi.runSimulation('AAPL', {
  num_simulations: 5000,
  max_periods: 21,
  target_percentiles: [25, 50, 75, 90]
});

// Compare multiple tickers
const comparison = await comparisonApi.compareTickers({
  tickers: ['AAPL', 'MSFT', 'NVDA'],
  threshold: 5
});
```

## 📝 API Documentation

### Backend API

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Response Formats

All API responses follow this structure:

```json
{
  "ticker": "AAPL",
  "source": "cache",
  "data": { ... },
  "timestamp": "2025-10-10T12:00:00Z"
}
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build individually
docker build -t rsi-ma-backend ./backend
docker build -t rsi-ma-frontend ./frontend

docker run -p 8000:8000 rsi-ma-backend
docker run -p 3000:3000 rsi-ma-frontend
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📦 Export & Reporting

### JSON Export

```python
# Export backtest results
backtester.export_to_json("results.json")

# Export Monte Carlo results
simulator.export_results("monte_carlo_AAPL.json")
```

### CSV Export (from frontend)

Use the export buttons in the dashboard to download:
- Performance matrix as CSV
- Return distributions as Excel
- Charts as PNG/SVG

## 🤝 Contributing

This is a comprehensive analytical tool. Potential improvements:
1. Additional technical indicators (MACD, Bollinger Bands)
2. Real-time data streaming via WebSocket
3. Portfolio-level analysis across multiple tickers
4. Machine learning for exit timing prediction
5. Options pricing integration

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **TradingView**: Inspiration for First Passage Time indicator
- **yfinance**: Market data API
- **FastAPI**: High-performance Python web framework
- **React/MUI**: Modern UI components

## 📞 Support

For issues or questions:
1. Check the `/docs` endpoint for API documentation
2. Review console output for detailed error messages
3. Verify data availability for your chosen tickers

## 🔮 Future Enhancements (Phase 2-4)

### Phase 2: Enhanced Analytics
- ✅ Monte Carlo simulation engine
- ✅ First Passage Time calculations
- ✅ Optimal exit strategy module
- ⏳ Multi-ticker comparison

### Phase 3: Advanced Features
- ⏳ Real-time percentile tracking
- ⏳ Custom indicator parameters
- ⏳ Enhanced export/reporting
- ⏳ Mobile responsiveness

### Phase 4: Production Polish
- ⏳ Performance optimization (caching, lazy loading)
- ⏳ User authentication
- ⏳ Saved analyses/watchlists
- ⏳ Advanced customization

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-10  
**Status**: Phase 1 Complete ✅
