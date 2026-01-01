# RSI-MA Performance Analytics Dashboard - AI Agent Guide

## Project Architecture

**Type**: Full-stack trading analytics dashboard (Python FastAPI backend + React TypeScript frontend)
**Purpose**: RSI-MA percentile ranking strategy backtesting, Monte Carlo simulations, and live trading signals

### Directory Structure
- `backend/` - FastAPI REST API, backtesting engines, signal generators (Python 3.9+)
- `frontend/` - React + TypeScript + Vite SPA with Material-UI components
- `strategy/` - Core indicator calculations (RSI-MA methodology)
- `tests/` - Test framework and validation scripts
- `docs/` - Feature documentation and technical specs

## Critical Technical Patterns

### RSI-MA Indicator Calculation
The core strategy uses **TradingView's "Mean Price" indicator** with RSI on directional price:

```python
# backend/enhanced_backtester.py:243-280
def calculate_rsi_ma_indicator(self, data: pd.DataFrame) -> pd.Series:
    """RSI(14) calculated on Mean Price weighted by bar direction"""
    mean_price = self.calculate_mean_price(data)  # TradingView Mean Price formula
    # Returns RSI(mean_price) NOT RSI(close)
```

**DO NOT** use `RSI(close)` - this project requires `RSI(mean_price)` for TradingView alignment.

### Data Flow Architecture

1. **Historical Analysis** (`enhanced_backtester.py`)
   - Fetches 5yr data via yfinance with Yahoo symbol resolution
   - Calculates RSI-MA → percentile ranks (500-day rolling window)
   - Generates D1-D21 forward return matrices (20 percentile ranges × 21 days)
   - Caches results in `backend/cache/{ticker}_results.json`

2. **Multi-Timeframe Analysis** (`multi_timeframe_analyzer.py`)
   - Compares Daily vs 4H timeframe percentiles
   - Detects divergence signals (e.g., Daily >> 4H = overextended)
   - Uses aligned windows: 252 daily bars = 410 4H bars (~1 trading year)

3. **Live Signals** (`live_signal_generator.py`)
   - Real-time entry/exit recommendations
   - Confidence scoring based on historical win rates
   - Exit pressure calculation using volatility metrics + percentile velocity

4. **API Layer** (`backend/api.py`)
   - Lazy-loads precomputed results from cache (24hr TTL)
   - GZip compression for large JSON responses
   - CORS configured for Codespaces/local dev with wildcard support

### Frontend API Integration

```typescript
// frontend/src/api/client.ts
const API_BASE_URL = import.meta.env.VITE_API_URL ?? '';  // Defaults to same-origin
// Dev: Vite proxy /api → http://localhost:8000 (see vite.config.ts)
// Prod: Deploy frontend+backend under same domain
```

All API calls are typed with TypeScript interfaces in `frontend/src/types/index.ts`.

## Development Workflows

### Quick Start Commands
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python api.py  # Runs uvicorn on :8000

# Frontend
cd frontend
npm install
npm run dev  # Vite dev server on :3000

# Full Stack (Docker)
docker-compose up  # backend:8000, frontend:3000
```

### Running Backtests
```python
# From backend/ directory
python enhanced_backtester.py  # Generates backtest_d1_d21_results.json

# Or via API
POST /api/backtest/batch
{
  "tickers": ["AAPL", "MSFT", "NVDA"],
  "lookback_period": 500,
  "max_horizon": 21
}
```

### Key Testing Scripts
- `backend/test_gold_silver_analysis.py` - Verify GLD/SLV analysis
- Various `backend/test_*.py` - RSI calculation validation against TradingView

## Project-Specific Conventions

### File Organization (CRITICAL)
- **NEVER save working files to root** - use subdirectories:
  - `/docs` for markdown documentation
  - `/tests` for test files
  - `/backend/cache` for generated results
  - See [CLAUDE.md](CLAUDE.md) for full rules

### Symbol Resolution
```python
# backend/ticker_utils.py (imported everywhere)
resolve_yahoo_symbol(ticker)  # Handles BRK.B→BRK-B, missing suffixes
```
Always use this before yfinance calls.

### Percentile Calculation
500-day rolling window for percentile ranks (approx 2 years trading data):
```python
percentiles = df['rsi_ma'].rolling(500, min_periods=50).rank(pct=True) * 100
```

### Entry Thresholds
Three standard thresholds: **5%, 10%, 15%** percentile
- 5% = aggressive (rare oversold)
- 10% = balanced (historical sweet spot)  
- 15% = conservative (more frequent signals)

### Return Calculation
**Cumulative returns** from entry through D1-D21 (NOT day-to-day):
```python
cumulative_returns[i] = (future_prices[i] / entry_price) - 1
```

## External Dependencies & Integration

### Market Data
- **yfinance** for Yahoo Finance data (with curl_cffi fallback for Cloudflare)
- Fallback to sample data generator if Yahoo blocked
- 0.5s rate limiting between tickers

### Pre-computed Statistics
Static data in `backend/stock_statistics.py`:
```python
from stock_statistics import NVDA_4H_DATA, NVDA_DAILY_DATA, STOCK_METADATA
# Pre-analyzed results for 15+ tickers (NVDA, MSFT, GOOGL, AAPL, GLD, SLV, etc.)
```
Used for instant loading without re-running backtests.

### SPARC Development Environment
This project uses Claude-Flow with 54+ specialized agents (see [CLAUDE.md](CLAUDE.md)):
```bash
npx claude-flow sparc tdd "feature description"  # Full TDD workflow
npx claude-flow sparc batch "task" # Parallel agent execution
```
**Use Claude Code's Task tool for agent spawning**, NOT just MCP coordination.

## Key Files to Reference

- [backend/enhanced_backtester.py](backend/enhanced_backtester.py) - Core backtesting engine (1067 lines)
- [backend/api.py](backend/api.py) - FastAPI endpoints (1900 lines)
- [backend/advanced_trade_manager.py](backend/advanced_trade_manager.py) - Exit pressure & volatility analysis
- [frontend/src/api/client.ts](frontend/src/api/client.ts) - Typed API client
- [frontend/src/components/](frontend/src/components/) - React visualization components
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Complete feature overview
- [CLAUDE.md](CLAUDE.md) - Agent orchestration rules

## Common Pitfalls

1. **Wrong RSI calculation** - Must use Mean Price, not Close
2. **Symbol resolution** - Always use `resolve_yahoo_symbol()` before yfinance
3. **Percentile window mismatch** - Daily=252 bars, 4H=410 bars for alignment
4. **File placement** - Don't save markdown/tests to root (see CLAUDE.md)
5. **Cache invalidation** - Backend caches results for 24hrs (force_refresh param available)

## Success Metrics

- Backtest generates 420 data points per threshold (20 ranges × 21 days)
- API response times <2s for cached results, <30s for fresh backtests
- Frontend handles 8+ ticker comparison without lag
- Monte Carlo simulations complete in <10s (1000 paths)
