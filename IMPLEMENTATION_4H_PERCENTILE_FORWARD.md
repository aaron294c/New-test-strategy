# 4-Hour Percentile Forward Mapping Implementation

## ✅ BACKEND COMPLETE

### Files Created/Modified

1. **`/backend/percentile_forward_4h.py`** (NEW)
   - Complete 4H percentile forward mapping implementation
   - Functions:
     - `fetch_4h_data()` - Fetches 1H data from yfinance and resamples to 4H
     - `calculate_rsi_ma_4h()` - RSI-MA calculation on 4H bars (same method as daily)
     - `calculate_percentile_ranks_4h()` - Rolling percentile ranks for 4H
     - `run_percentile_forward_analysis_4h()` - Main analysis function

2. **`/backend/api.py`** (MODIFIED)
   - Added `/api/percentile-forward-4h/{ticker}` endpoint
   - Returns identical structure to daily endpoint but with 4H data
   - Includes caching (24-hour cache, separate from daily)

### Key Implementation Details

#### Horizons
- **Daily**: 3d, 7d, 14d, 21d (3, 7, 14, 21 bars)
- **4-Hour**: 12h, 24h, 36h, 48h (3, 6, 9, 12 bars)

#### Data Source
- Fetches 1-hour data from yfinance (last 365 days)
- Resamples to 4-hour candles (Open=first, High=max, Low=min, Close=last, Volume=sum)
- Typical result: ~580 4H bars for 1 year lookback

#### RSI-MA Calculation (Identical to Daily)
```python
1. Calculate log returns from Close price
2. Calculate delta (diff of returns)
3. Apply RSI(14) using Wilder's smoothing
4. Apply EMA(14) to RSI
```

#### Percentile Calculation
- Lookback window: 252 4H bars (~42 days)
- Adjusted from 500 bars due to 4H data availability constraints

#### Model Suite (Same 6 Models as Daily)
1. **Empirical Conditional Expectation** - Bin-based lookup
2. **Transition Matrix (Markov Chain)** - Percentile evolution
3. **Linear Regression** - Continuous mapping
4. **Polynomial Regression** - Nonlinear relationships
5. **Quantile Regression** - Tail risk (5th, 50th, 95th percentiles)
6. **Kernel Smoothing** - Nonparametric Nadaraya-Watson
7. **Ensemble** - Average of all methods (recommended)

### API Response Structure

```json
{
  "ticker": "AAPL",
  "timeframe": "4H",
  "horizon_labels": ["12h", "24h", "36h", "48h"],
  "horizon_bars": [3, 6, 9, 12],
  "current_state": {
    "current_percentile": 83.4,
    "current_rsi_ma": 50.54
  },
  "prediction": {
    "ensemble_forecast_3d": 0.21,     // 12h
    "ensemble_forecast_7d": 0.11,     // 24h
    "ensemble_forecast_14d": 0.11,    // 36h
    "ensemble_forecast_21d": 0.11,    // 48h
    "empirical_bin_stats": {...},
    "markov_forecast_3d": 0.44,
    "linear_regression": {...},
    "polynomial_regression": {...},
    "quantile_regression_median": {...},
    "quantile_regression_05": {...},
    "quantile_regression_95": {...},
    "kernel_forecast": {...},
    "confidence_3d": {...},
    "model_bin_mappings": {...}
  },
  "bin_stats": {
    "0": {
      "bin_label": "5-15",
      "mean_return_3d": -0.13,  // 12h
      "mean_return_7d": 0.0,    // 24h
      ...
    }
  },
  "transition_matrices": {
    "3": {  // 3 bars = 12h
      "horizon_label": "12h",
      "horizon_bars": 3,
      "bins": [...],
      "matrix": [[...]],
      "sample_sizes": [...]
    },
    "6": {...},  // 24h
    "9": {...},  // 36h
    "12": {...}  // 48h
  },
  "backtest_results": [...],
  "accuracy_metrics": {
    "3d": {  // 12h
      "mae": 1.49,
      "rmse": 1.87,
      "hit_rate": 52.5,
      "sharpe": 0.07,
      "information_ratio": -0.15,
      "correlation": 0.023
    },
    ...
  },
  "timestamp": "2025-10-19T...",
  "cached": false
}
```

### Caching
- Cache files: `{TICKER}_percentile_forward_4h.json`
- Cache duration: 24 hours
- Separate from daily cache to avoid conflicts

---

## 🚧 FRONTEND TODO

### Required Changes

#### 1. Add Timeframe Toggle to `PercentileForwardMapper.tsx`

Add a toggle/tabs at the top of the component:

```tsx
const [timeframe, setTimeframe] = useState<'1D' | '4H'>('1D');

// UI Toggle
<Box sx={{ mb: 2 }}>
  <ToggleButtonGroup
    value={timeframe}
    exclusive
    onChange={(e, newTimeframe) => {
      if (newTimeframe) setTimeframe(newTimeframe);
    }}
  >
    <ToggleButton value="1D">
      Daily
    </ToggleButton>
    <ToggleButton value="4H">
      4-Hour
    </ToggleButton>
  </ToggleButtonGroup>
</Box>
```

#### 2. Update API Call Logic

```tsx
const fetchData = async () => {
  const endpoint = timeframe === '4H'
    ? `/api/percentile-forward-4h/${ticker}`
    : `/api/percentile-forward/${ticker}`;

  const response = await fetch(endpoint);
  const data = await response.json();
  setData(data);
};

useEffect(() => {
  fetchData();
}, [ticker, timeframe]);
```

#### 3. Update Horizon Labels Dynamically

Replace hardcoded "3d", "7d", "14d", "21d" with dynamic labels from API:

```tsx
const horizonLabels = data?.horizon_labels || ['3d', '7d', '14d', '21d'];

// Use in UI
{horizonLabels.map((label, idx) => (
  <TableCell key={label}>{label}</TableCell>
))}
```

#### 4. Add Timeframe Indicator

Add a small label/chip showing current timeframe:

```tsx
<Chip
  label={`Data timeframe: ${timeframe} • Forecast horizons: ${horizonLabels.join(' / ')}`}
  size="small"
  sx={{ mb: 2 }}
/>
```

#### 5. Update TypeScript Interfaces

```tsx
interface PercentileForwardData {
  ticker: string;
  timeframe: '1D' | '4H';
  horizon_labels: string[];
  horizon_bars?: number[];
  current_state: {
    current_percentile: number;
    current_rsi_ma: number;
  };
  prediction: {...};
  bin_stats: {...};
  transition_matrices: {...};
  backtest_results: [...];
  accuracy_metrics: {...};
  timestamp: string;
  cached: boolean;
}
```

### Files to Modify

1. **`/frontend/src/components/PercentileForwardMapper.tsx`**
   - Add timeframe toggle
   - Update API endpoint logic
   - Make horizon labels dynamic
   - Add timeframe indicator

2. **`/frontend/src/types/index.ts`** (if it exists)
   - Update interfaces to include `timeframe` and `horizon_labels`

3. **`/frontend/src/api/client.ts`** (if centralized API calls)
   - Add `fetchPercentileForward4h()` function

### UI/UX Considerations

- Keep the same tab structure: Key Insights, Empirical Bin Mapping, Transition Matrices, Model Comparison
- Visual style should be identical between Daily and 4H
- Color palette unchanged
- Tooltip behavior consistent
- When switching timeframes, show loading state

### Testing Checklist

- [ ] Toggle switches between Daily and 4H successfully
- [ ] API calls go to correct endpoint (`/api/percentile-forward` vs `/api/percentile-forward-4h`)
- [ ] Horizon labels update correctly (3d/7d/14d/21d vs 12h/24h/36h/48h)
- [ ] All tabs render correctly for both timeframes
- [ ] Charts update with new data
- [ ] Cached data loads quickly
- [ ] Error handling works for both endpoints
- [ ] Side-by-side visual comparison (Daily vs 4H) shows no styling differences

---

## Example Usage

### Backend Test

```bash
python backend/percentile_forward_4h.py
```

### API Test

```bash
curl http://localhost:8000/api/percentile-forward-4h/AAPL
```

### Frontend Component (Pseudocode)

```tsx
function PercentileForwardMapper({ ticker }: Props) {
  const [timeframe, setTimeframe] = useState<'1D' | '4H'>('1D');
  const [data, setData] = useState<PercentileForwardData | null>(null);

  useEffect(() => {
    const endpoint = timeframe === '4H'
      ? `/api/percentile-forward-4h/${ticker}`
      : `/api/percentile-forward/${ticker}`;

    fetch(endpoint)
      .then(res => res.json())
      .then(setData);
  }, [ticker, timeframe]);

  return (
    <>
      <TimeframeToggle value={timeframe} onChange={setTimeframe} />
      <Chip label={`${timeframe} • ${data?.horizon_labels.join(' / ')}`} />
      <Tabs>
        <Tab label="Key Insights">
          <CurrentPercentile value={data?.current_state.current_percentile} />
          <Forecasts horizons={data?.horizon_labels} predictions={data?.prediction} />
        </Tab>
        <Tab label="Empirical Bin Mapping">
          <BinStatsTable binStats={data?.bin_stats} horizons={data?.horizon_labels} />
        </Tab>
        <Tab label="Transition Matrices">
          <TransitionHeatmap matrices={data?.transition_matrices} />
        </Tab>
        <Tab label="Model Comparison">
          <ModelComparisonChart models={data?.prediction} horizons={data?.horizon_labels} />
        </Tab>
      </Tabs>
    </>
  );
}
```

---

## Performance Notes

- 4H data fetching: ~2-3 seconds (first run)
- Cached response: < 100ms
- Dataset size: ~300-400 observations (vs 800+ for daily)
- Models fit faster due to smaller dataset
- Backtest may have fewer iterations due to limited data

---

## Limitations & Known Issues

1. **Data Availability**: yfinance 1H data limited to ~730 days max
   - Reduced lookback window from 500 to 252 bars to accommodate this
   - Affects backtest sample size

2. **Horizon Naming**: Internal code still uses `forecast_3d`, `forecast_7d`, etc.
   - These map to bars, not days
   - Frontend should use `horizon_labels` for display

3. **Resampling**: 4H candles created from 1H data
   - Not native 4H from exchange
   - Minor timing differences possible

---

## Next Steps

1. ✅ Backend implementation complete
2. ✅ API endpoint working
3. ✅ Caching implemented
4. 🚧 Frontend timeframe toggle (TODO)
5. 🚧 Frontend API integration (TODO)
6. 🚧 Dynamic horizon labels (TODO)
7. 🚧 Visual QA (TODO)
8. 🚧 Documentation update (TODO)

---

## Questions?

- Backend logic: See `/backend/percentile_forward_4h.py`
- API endpoint: See `/backend/api.py` line 987-1073
- Daily implementation (reference): See `/backend/percentile_forward_mapping.py`
