# Max Pain Calculation Fix

## Issue
Max pain was showing the same 2.04% distance for all symbols because it was using a placeholder calculation (`price * 0.98`).

## Fix Applied

### What Changed
Updated `maxPainCalculator.ts` to properly calculate max pain using **ONLY weekly options** (< 7 days DTE).

### Key Points

1. **ST Put, LT Put, Q Put - UNCHANGED**
   - These remain as gamma wall strikes (support/resistance levels)
   - Based on 14D, 30D, 90D timeframes respectively
   - No changes to risk distance logic

2. **Max Pain - COMPLETELY REWRITTEN**
   - **ONLY uses options with DTE < 7 days** (nearest Friday expiration)
   - Filters walls: `walls.filter(wall => wall.dte < MAX_DTE_THRESHOLD)`
   - Calculates pain at each strike using proper options theory
   - Returns `null` if no weekly options available

### Algorithm

```typescript
// 1. Filter to weekly options ONLY
const shortTermWalls = walls.filter(wall => wall.dte < 7);

// 2. For each test price, calculate total pain
for (const testPrice of testPrices) {
  let totalPain = 0;

  // Call pain: ITM when price > strike
  if (testPrice > strike) {
    totalPain += callOI * (testPrice - strike);
  }

  // Put pain: ITM when price < strike
  if (testPrice < strike) {
    totalPain += putOI * (strike - testPrice);
  }
}

// 3. Find strike with minimum pain
maxPain = strikeWithMinimumPain;
```

### Why Weekly Options Only?

- Weekly options (< 7 DTE) have the **highest volume** and **most influence** on near-term price action
- Dealers must hedge these aggressively as expiration approaches
- Longer-dated options (30D, 90D) are already captured in gamma walls (ST, LT, Q)
- Avoids double-counting and mixing timeframes

### Expected Results

Instead of uniform -2.04% for all symbols, you'll now see varied distances like:
- SPX: +1.2% (above max pain)
- QQQ: -3.5% (below max pain)
- AAPL: -0.8% (near max pain)

Each based on actual weekly options positioning.

## Files Modified

1. **`maxPainCalculator.ts`**
   - Added `MAX_DTE_THRESHOLD = 7` constant
   - Added filter: `walls.filter(wall => wall.dte < MAX_DTE_THRESHOLD)`
   - Applied to both `calculateMaxPain()` and `calculateMaxPainAnalysis()`

2. **`RiskDistanceTab.tsx`**
   - No logic changes to ST/LT/Q put extraction
   - Changed max pain from `symbol.gammaFlip` to `calculateMaxPain(symbol)`

## Testing

Server running at: http://localhost:3000/

Navigate to **📏 RISK DISTANCE** tab to see unique max pain values per symbol.
