# Nadaraya-Watson Lower Band Distance Feature

## Overview

The **Nadaraya-Watson Lower Band** is the 6th risk metric in the Risk Distance analysis system. It measures how close the current price is to the Nadaraya-Watson Envelope's lower band, providing an additional support level based on kernel regression with ATR-based volatility bands.

## Formula

The Nadaraya-Watson Envelope uses a Gaussian kernel regression estimator:

```
weight[i] = exp(-(i²) / (2 * h²))
nw_estimate = Σ(price[i] * weight[i]) / Σ(weight[i])
lower_band = nw_estimate - (ATR(atr_period) * atr_mult)
```

### Distance Metrics

1. **lower_band_breached** (boolean): `True` if `current_price < lower_band`, else `False`
2. **pct_from_lower_band** (float): Percentage difference computed as:
   ```
   pct_from_lower_band = 100 * (price - lower_band) / lower_band
   ```

### Examples
- `price = 102`, `lower_band = 100` → `pct_from_lower_band = +2.0%`
- `price = 98`, `lower_band = 100` → `pct_from_lower_band = -2.0%`
- `price = 95`, `lower_band = 100` → `pct_from_lower_band = -5.0%`, `lower_band_breached = True`

## Parameters

| Parameter | Default | Min | Max | Description |
|-----------|---------|-----|-----|-------------|
| `length` | 200 | 20 | 500 | Window size for kernel regression |
| `bandwidth` | 8.0 | 0.1 | - | Kernel bandwidth parameter (h) - controls smoothness |
| `atr_period` | 50 | 10 | - | Period for ATR calculation |
| `atr_mult` | 2.0 | 0.1 | - | ATR multiplier for envelope width |

## Visual Proximity Filtering

To prevent extreme support levels from breaking the visual scale of the horizontal levels bar, the Lower Extension and NW Band markers use **conditional rendering based on proximity to price**.

### Behavior

**Always Shown:**
- ST Put, LT Put, Q Put, Max Pain (core PUT levels)

**Conditionally Shown (based on proximity):**
- Lower Extension (MBAD Blue Line)
- NW Lower Band (Nadaraya-Watson)

### Proximity Rules

1. Calculate `pct_dist` for the level
2. If `use_absolute_distance = true` (default), compute `abs_pct = abs(pct_dist)`
3. If `abs_pct <= threshold_pct` (default: 20%):
   - **Show** the marker on the horizontal bar
   - Display its percentage next to the marker
4. Else:
   - **Hide** the marker from the horizontal bar
   - **Keep** the row in the detailed metrics table
   - Show a subtle indicator: "Lower Extension not shown (> 20% from price)"

### Configuration

```typescript
interface ProximityConfig {
  lowerExtThresholdPct: number;    // Default: 20%
  nwBandThresholdPct: number;      // Default: 20%
  useAbsoluteDistance: boolean;    // Default: true
}
```

### Examples

| Current Price | Lower Band | % Distance | Visual Result |
|---------------|------------|------------|---------------|
| $100 | $118 | +18.0% | ✅ Shown on bar (18 ≤ 20) |
| $100 | $125 | +25.0% | ❌ Hidden from bar, shown in table (25 > 20) |
| $100 | $10 | -90.0% | ❌ Hidden from bar, shown in table |
| $102 | $100 | +2.0% | ✅ Shown on bar |
| $496.82 | $499.83 | -0.6% | ✅ Shown on bar |

## Edge Cases

### Division by Zero Protection
- If `lower_band ≈ 0` (< 1e-8), returns `pct_from_lower_band = None`
- Uses epsilon `eps = 1e-8` to avoid division by zero

### Insufficient Data
- Requires `min_bars = max(length, atr_period) + 1` data points
- Returns `is_valid = False` if insufficient data
- Shows "N/A - Insufficient Data" in UI

### Missing Data
- If `price = null` or `lower_band = null`, propagates `None` values
- Visual indicator shows warning in table row

## Integration

### Backend API

**Endpoint:** `GET /api/nadaraya-watson/metrics/{ticker}`

**Query Parameters:**
```
length: int = 200
bandwidth: float = 8.0
atr_period: int = 50
atr_mult: float = 2.0
```

**Response:**
```json
{
  "symbol": "MSFT",
  "nw_estimate": 516.89,
  "lower_band": 499.83,
  "upper_band": 533.96,
  "lower_band_breached": true,
  "pct_from_lower_band": -0.6,
  "atr": 8.53,
  "current_price": 496.82,
  "is_valid": true,
  "last_update": "nov 09, 10:09am"
}
```

### Frontend Integration

The NW lower band is integrated into the Risk Distance system:

1. **Types** (`types.ts`):
   - Added `nw_lower_band` to `RiskDistanceInput`
   - Added distance fields to `RiskDistanceOutput`

2. **Calculator** (`calculator.ts`):
   - Calculates `pct_dist_nw_lower_band` using same formula as other levels
   - Included in `findClosestSupport()` logic

3. **Risk Distance Tab** (`RiskDistanceTab.tsx`):
   - Fetches NW data in parallel with other metrics
   - Merges into unified risk distance output

4. **Symbol Card** (`SymbolCard.tsx`):
   - Displays 6th metric row: "NW Band" in cyan (#00BCD4)
   - Shows level value, % distance, and below/above indicator

5. **Position Strip** (`PositionStrip.tsx`):
   - Conditionally renders NW marker based on proximity threshold
   - Shows hidden indicator when level is too far from price
   - Applies same scaling logic as other levels

## Testing

### Unit Tests

All tests are in `/backend/tests/test_nadaraya_watson.py`:

```bash
cd /workspaces/New-test-strategy/backend
python3 -m pytest tests/test_nadaraya_watson.py -v
```

**Test Coverage:**
- ✅ Price above lower band (positive %, breach = False)
- ✅ Price below lower band (negative %, breach = True)
- ✅ Price at lower band (% ≈ 0, breach = False)
- ✅ Division by zero handling
- ✅ Warm-up period with insufficient data
- ✅ Exact example case (lower_band = 100, price = 95)
- ✅ High/low data for proper ATR calculation
- ✅ Percentage calculation (positive and negative)
- ✅ Empty prices array
- ✅ Bandwidth sensitivity
- ✅ Return types validation

### Visual Proximity Tests

| Test Case | Expected Result |
|-----------|----------------|
| lower_ext at +10% | Appears on bar; table row exists |
| lower_ext at -18% | Appears on bar; table row exists |
| lower_ext at +75% | Does NOT appear on bar; table row shows +75%; indicator shows "hidden" |
| lower_ext at +6000% | Does NOT appear on bar; other levels remain scaled correctly |
| Toggle threshold to 30% | Updates immediately (no refresh needed) |
| Screen reader | Reads lower_ext table row even when hidden from bar |

## Accessibility

- **ARIA Labels**: Hidden levels indicator has `role="status"` and `aria-live="polite"`
- **Screen Reader**: Can access lower_ext entry in table even when hidden from bar
- **Keyboard Navigation**: All interactive elements are keyboard accessible
- **Tooltips**: Provide additional context on hover

## Performance

- **Parallel Fetching**: NW data fetched in parallel with other metrics
- **Caching**: yfinance data cached by backtester
- **Warm-up**: Requires 200+ bars for accurate calculation
- **Computation Time**: O(length) for kernel regression

## Future Enhancements

1. **Per-Instrument Override**: Allow different thresholds for different symbols
2. **User Preferences**: Remember user's custom threshold settings
3. **Auto-Adjust**: Dynamically adjust threshold based on market volatility
4. **Multiple Bands**: Add upper band distance calculations
5. **Alerts**: Notify when price crosses NW bands

## References

- Pine Script Implementation: `/workspaces/New-test-strategy/MBAD.md`
- Backend Calculator: `/backend/api/nadaraya_watson.py`
- Frontend Types: `/frontend/src/components/RiskDistance/types.ts`
- Unit Tests: `/backend/tests/test_nadaraya_watson.py`
