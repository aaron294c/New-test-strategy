# Next Task for Coding Agent

## Task Overview

**Task**: Create Comprehensive Backend Test Suite
**Priority**: HIGH
**Estimated Effort**: 4-6 hours
**Category**: Testing (Feature F035)

## Objective

Implement a comprehensive pytest test suite for the backend Python code to achieve 80%+ test coverage. The backend is the foundation of the application, and robust testing is critical for maintaining stability as new features are added.

## Why This Task First?

1. **Foundation First**: Backend is the core of the application—ensure it's solid
2. **Regression Protection**: Tests prevent breaking changes during future development
3. **Documentation**: Tests serve as executable documentation of expected behavior
4. **Confidence**: Having tests allows for safe refactoring and optimization
5. **Current Gap**: Backend has ZERO test coverage despite having pytest configured

## What to Create

### Test Files to Create

All test files should be created in `/tests/` directory:

#### 1. `tests/test_api.py`
**Purpose**: Test all FastAPI endpoints

**What to Test**:
- `GET /api/backtest/{ticker}` - Single ticker backtest
  - Valid ticker returns 200 with correct data structure
  - Invalid ticker returns 404
  - Cached results return quickly
  - Fresh calculation works
- `POST /api/backtest/batch` - Batch backtesting
  - Multiple tickers processed correctly
  - Empty ticker list handled
  - Partial failures don't crash entire batch
- `POST /api/monte-carlo/{ticker}` - Monte Carlo simulation
  - Valid parameters return simulation results
  - Invalid parameters return 400
  - Results include fan chart data and FPT
- `GET /api/performance-matrix/{ticker}/{threshold}` - Performance matrix
  - Correct 20x21 matrix returned
  - Confidence levels calculated
  - Sample sizes included
- `GET /api/optimal-exit/{ticker}/{threshold}` - Exit recommendations
  - Optimal day identified correctly
  - Efficiency rankings returned
  - Statistical significance reported
- `GET /api/health` - Health check
  - Returns 200 when service is healthy

**Mocking Strategy**:
- Mock yfinance data fetching
- Use fixture data for consistent tests
- Mock file system operations (cache reads/writes)

**Example Test Structure**:
```python
import pytest
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_backtest_endpoint_valid_ticker():
    response = client.get("/api/backtest/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert "ticker" in data
    assert "performance_matrix" in data
    assert "risk_metrics" in data
```

#### 2. `tests/test_backtester.py`
**Purpose**: Test backtesting engine logic

**What to Test**:
- RSI calculation (Feature F001)
  - Correct RSI values for known data
  - Handle edge cases (zero division, NaN)
- RSI-MA calculation (Feature F002)
  - EMA smoothing applied correctly
  - Span parameter respected
- Percentile rank calculation (Feature F003)
  - Correct percentile ranks for sample data
  - Rolling window size respected (500 periods)
  - Handle insufficient data cases
- Entry signal detection (Feature F004)
  - Crossings below 5%, 10%, 15% detected
  - Entry events recorded with correct date and percentile
- Performance tracking (Feature F006)
  - Returns calculated correctly for D1-D21
  - Cumulative and daily returns both tracked
- Performance matrix generation (Feature F007)
  - 20x21 matrix dimensions correct
  - Percentile buckets assigned properly
  - Median, P25, P75 calculated correctly

**Example Test Structure**:
```python
import pytest
import pandas as pd
import numpy as np
from enhanced_backtester import EnhancedPerformanceMatrixBacktester

def test_rsi_calculation():
    # Create sample price data
    prices = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107, 109])

    backtester = EnhancedPerformanceMatrixBacktester(tickers=["TEST"])
    rsi = backtester._calculate_rsi(prices, period=14)

    # Verify RSI is between 0 and 100
    assert (rsi >= 0).all()
    assert (rsi <= 100).all()

    # Verify RSI has expected shape
    assert len(rsi) == len(prices)
```

#### 3. `tests/test_monte_carlo.py`
**Purpose**: Test Monte Carlo simulation engine

**What to Test**:
- Geometric Brownian Motion (Feature F014)
  - Price paths generated correctly
  - Drift and volatility applied
  - Paths start from current price
- Percentile movement simulation (Feature F015)
  - Percentile paths stay in 0-100 range
  - Random walk applied correctly
- First Passage Time (Feature F016)
  - Target crossings detected
  - Days to crossing recorded
  - Probability distributions calculated
- Fan chart generation (Feature F017)
  - Confidence bands calculated (50%, 68%, 95%)
  - Percentiles extracted correctly

**Example Test Structure**:
```python
import pytest
import pandas as pd
import numpy as np
from monte_carlo_simulator import MonteCarloSimulator

def test_geometric_brownian_motion():
    simulator = MonteCarloSimulator(
        ticker="AAPL",
        current_price=150.0,
        num_simulations=100,
        max_periods=21
    )

    paths = simulator._simulate_price_paths()

    # Verify shape
    assert paths.shape == (21, 100)

    # Verify all paths start at current price
    assert np.allclose(paths[0, :], 150.0)

    # Verify no negative prices
    assert (paths > 0).all()
```

#### 4. `tests/test_statistical_analysis.py`
**Purpose**: Test statistical analysis functions

**What to Test**:
- Risk metrics calculation (Feature F010)
  - Drawdown calculated correctly
  - Recovery time measured
  - Consecutive losses counted
  - Average loss magnitude computed
- Trend significance testing (Feature F011)
  - Pearson correlation calculated
  - P-values correct
  - Mann-Whitney U test applied
- Return efficiency metric (Feature F012)
  - Efficiency = return / days held
  - Rankings correct
- Confidence intervals (Feature F013)
  - 68% CI = median ± 1σ
  - 95% CI = median ± 2σ

**Example Test Structure**:
```python
import pytest
import numpy as np
from enhanced_backtester import calculate_risk_metrics

def test_drawdown_calculation():
    returns = np.array([1.0, 1.05, 1.03, 0.98, 0.95, 1.00, 1.02])

    metrics = calculate_risk_metrics(returns)

    assert metrics["max_drawdown"] < 0  # Drawdown is negative
    assert metrics["recovery_rate"] >= 0
    assert metrics["recovery_rate"] <= 1
```

### Test Configuration Files

#### `tests/conftest.py`
**Purpose**: Shared pytest fixtures and configuration

**What to Include**:
```python
import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def sample_price_data():
    """Generate sample OHLC price data for testing"""
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    return pd.DataFrame({
        'Open': np.random.uniform(100, 110, 100),
        'High': np.random.uniform(110, 120, 100),
        'Low': np.random.uniform(90, 100, 100),
        'Close': np.random.uniform(100, 110, 100),
        'Volume': np.random.randint(1e6, 10e6, 100)
    }, index=dates)

@pytest.fixture
def mock_yfinance(monkeypatch):
    """Mock yfinance data fetching"""
    def mock_download(*args, **kwargs):
        return sample_price_data()

    monkeypatch.setattr("yfinance.download", mock_download)
```

#### `tests/pytest.ini`
**Purpose**: Pytest configuration

**What to Include**:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --cov=backend
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
```

## Success Criteria

### Quantitative Metrics
- ✅ 80%+ code coverage on backend codebase
- ✅ All API endpoints have at least 3 test cases
- ✅ Core algorithms (RSI, percentile, returns) have unit tests
- ✅ Statistical functions have validation tests
- ✅ All tests pass with `pytest`

### Qualitative Metrics
- ✅ Tests are readable and well-documented
- ✅ Edge cases and error conditions tested
- ✅ Tests run in under 10 seconds total
- ✅ No flaky tests (tests pass consistently)
- ✅ External dependencies (yfinance) properly mocked

## Testing Strategy

### 1. Unit Tests (70% of tests)
- Test individual functions in isolation
- Mock external dependencies
- Focus on core logic correctness

### 2. Integration Tests (20% of tests)
- Test API endpoints end-to-end
- Use TestClient for FastAPI
- Verify data flows correctly

### 3. Edge Case Tests (10% of tests)
- Empty data
- Invalid inputs
- Boundary conditions
- Error scenarios

## Commands to Run

### Install Test Dependencies
```bash
cd backend
pip install pytest pytest-cov pytest-mock
```

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=backend --cov-report=term-missing

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_backtester.py::test_rsi_calculation

# Run in verbose mode
pytest -v

# Run with coverage HTML report
pytest --cov=backend --cov-report=html
# Open htmlcov/index.html to view report
```

### Continuous Testing
```bash
# Watch mode (re-run on file changes)
pytest-watch
```

## Files to Read Before Starting

1. `/backend/api.py` - Understand API structure
2. `/backend/enhanced_backtester.py` - Core backtesting logic
3. `/backend/monte_carlo_simulator.py` - Simulation logic
4. `/project_memory/spec.md` - Feature specifications
5. `/project_memory/context.md` - Project structure

## Feature Update Instructions

After implementing tests, update `/project_memory/feature_list.json`:

1. Open the file
2. Find feature F035 (Backend Test Suite)
3. Change `"passes": false` to `"passes": true`
4. Update the `last_updated` field to current date

**DO NOT** mark other features as passing unless they have test coverage.

## Tips and Best Practices

### Mocking External Dependencies
```python
# Mock yfinance
@pytest.fixture
def mock_yfinance_data(monkeypatch):
    def mock_download(*args, **kwargs):
        return pd.DataFrame({'Close': [100, 101, 102, 103]})
    monkeypatch.setattr("yfinance.download", mock_download)
```

### Testing FastAPI Endpoints
```python
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
```

### Testing Async Functions
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected_value
```

### Parametrized Tests
```python
@pytest.mark.parametrize("ticker,expected", [
    ("AAPL", True),
    ("INVALID", False),
    ("", False)
])
def test_ticker_validation(ticker, expected):
    assert validate_ticker(ticker) == expected
```

## Common Pitfalls to Avoid

1. ❌ **Don't test external libraries** (e.g., testing pandas works)
2. ❌ **Don't write slow tests** (mock IO operations)
3. ❌ **Don't write flaky tests** (avoid time-dependent assertions)
4. ❌ **Don't test implementation details** (test behavior, not internal state)
5. ❌ **Don't skip edge cases** (empty inputs, None values, negative numbers)

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [FastAPI testing guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Best practices for Python testing](https://docs.pytest.org/en/latest/goodpractices.html)

## After Completion

Once backend tests are complete:

1. ✅ Run full test suite and verify 80%+ coverage
2. ✅ Update `feature_list.json` (mark F035 as passing)
3. ✅ Update `claude-progress.txt` with completion notes
4. ✅ Commit tests with descriptive message: "Add comprehensive backend test suite (F035)"
5. ✅ Move to next task: Frontend test suite (F036) - see instructions in `feature_list.json`

## Questions or Issues?

- Review `/project_memory/context.md` for project structure
- Check `/backend/api.py` for API implementation details
- Examine existing test files in other projects for examples
- Consult pytest documentation for advanced techniques

---

**Remember**: Tests are code too! Write them clearly, document them well, and keep them maintainable.
