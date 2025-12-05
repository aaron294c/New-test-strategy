# Gamma Wall Scanner - Troubleshooting Guide

## Common Errors and Solutions

### Error: "Cannot read properties of undefined (reading 'map')"

**Location:** `GammaControlPanel.tsx:60`

**Cause:** The `GammaControlPanel` component expects an `availableSymbols` prop (string array), but was receiving `symbols` (ParsedSymbolData array) or undefined.

**Solution Applied:**
```typescript
// ❌ WRONG
<GammaControlPanel
  symbols={symbols}  // Wrong prop name and type
  isLoading={isLoading}  // Wrong prop name
  onPasteData={handlePasteData}  // Wrong prop name
/>

// ✅ CORRECT
<GammaControlPanel
  availableSymbols={symbols.map((s) => s.symbol)}  // Correct prop name and type
  loading={isLoading}  // Correct prop name
  onManualPaste={handlePasteData}  // Correct prop name
/>
```

**File:** `frontend/src/components/GammaScanner/GammaScannerTab.v3.tsx:199-206`

---

### Error: Missing Plotly Package

**Error Message:**
```
Failed to resolve import "plotly.js-basic-dist" from "src/components/GammaScanner/GammaChartCanvas.tsx"
```

**Solution:**
```bash
cd frontend
npm install plotly.js-basic-dist
```

---

### Error: Backend Import Error

**Error Message:**
```
ModuleNotFoundError: No module named 'api.gamma'; 'api' is not a package
```

**Cause:** Both `api.py` (file) and `api/` (directory) exist, causing Python import confusion.

**Solution Applied in `backend/api.py`:**
```python
# Add gamma directory directly to sys.path
from pathlib import Path
gamma_dir = Path(__file__).parent / "api" / "gamma"
if str(gamma_dir) not in sys.path:
    sys.path.insert(0, str(gamma_dir))

# Import from gamma_endpoint directly
from gamma_endpoint import router as gamma_router
app.include_router(gamma_router)
```

---

### Error: Port Already in Use

**Message:**
```
Port 3000 is in use, trying another one...
```

**Solution:** Vite automatically finds next available port (3001, 3002, etc.). No action needed.

**Manual Override:**
```bash
# In package.json, specify port
"scripts": {
  "dev": "vite --port 3001"
}
```

---

### Error: API Connection Refused

**Symptoms:**
- Error banner showing "Failed to fetch data"
- Status indicator shows "Offline" (red dot)
- Browser console shows `net::ERR_CONNECTION_REFUSED`

**Checklist:**

1. **Is backend running?**
   ```bash
   curl http://localhost:8000/api/gamma-data/example
   ```
   Expected: JSON response with level_data

2. **Check backend process:**
   ```bash
   ps aux | grep "python.*api.py"
   ```

3. **Start backend if not running:**
   ```bash
   cd backend
   python api.py
   ```

4. **Check port configuration:**
   - Frontend expects: `http://localhost:8000`
   - Backend should listen on: `:8000`

5. **CORS issues?**
   Backend `api.py` should have:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # Or specific origins
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

---

### Error: Type Errors During Build

**Message:**
```
error TS2345: Argument of type '...' is not assignable to parameter of type '...'
```

**Common Causes:**

1. **Missing settings properties:**
   ```typescript
   // Settings must include ALL required fields from GammaScannerSettings type
   const [settings, setSettings] = useState<GammaScannerSettings>({
     selectedSymbols: [],
     showSwingWalls: true,
     showLongWalls: true,
     showQuarterlyWalls: true,
     showSDBands: true,
     showGammaFlip: true,
     showLabels: true,
     showTable: true,        // ← Must include
     wallOpacity: 0.8,
     minStrength: 0,
     hideWeakWalls: false,
     applyRegimeAdjustment: true,
     dataSource: 'api',
     colorScheme: 'default',
     apiPollingInterval: 60,  // ← Must include
   });
   ```

2. **Check type definition:** `frontend/src/components/GammaScanner/types.ts`

---

### Warning: React Hook Dependency

**Message:**
```
React Hook useEffect has missing dependencies
```

**Solution:** Add dependencies to useEffect array:
```typescript
useEffect(() => {
  if (settings.dataSource === 'api') {
    fetchData();
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }
}, [settings.dataSource, fetchData]); // ← Add all dependencies
```

**Use useCallback for functions:**
```typescript
const fetchData = useCallback(async () => {
  // ... fetch logic
}, [settings.dataSource]);
```

---

## Verification Steps

### 1. Backend Health Check
```bash
# Check example endpoint
curl http://localhost:8000/api/gamma-data/example

# Expected response structure:
{
  "level_data": ["SPX:...", "QQQ:...", "AAPL:..."],
  "last_update": "nov 07, 03:42pm",
  "market_regime": "Normal Volatility",
  "current_vix": 20.8,
  "regime_adjustment_enabled": true
}
```

### 2. Frontend Health Check
1. Open browser to http://localhost:3001
2. Navigate to "🔰 GAMMA WALL SCANNER" tab
3. Check for:
   - ✅ No error banner at top
   - ✅ Green "Live" status indicator
   - ✅ Chart canvas renders
   - ✅ Sidebar shows controls
   - ✅ Bottom panel has metrics table

### 3. Data Parser Verification
Browser console should NOT show:
- ❌ `ParseError` messages
- ❌ `Invalid field count` warnings
- ❌ `Failed to parse symbol` errors

If parser errors appear, check:
```typescript
// In browser DevTools console
localStorage.getItem('gammaScanner.lastParseErrors')
```

### 4. Chart Rendering Check
- **Candlesticks:** Green/red candles visible
- **Gamma walls:** Horizontal lines overlay chart
- **Current price:** White line with label on right
- **Gamma flip:** Orange dashed line (if enabled)
- **Interactions:** Zoom (mouse wheel), pan (drag), hover tooltips

---

## Debug Mode

### Enable Detailed Logging

Add to `GammaScannerTab.v3.tsx`:
```typescript
useEffect(() => {
  console.log('[GammaScanner] State Update:', {
    symbolCount: symbols.length,
    isLoading,
    error,
    isLive,
    lastUpdate,
  });
}, [symbols, isLoading, error, isLive, lastUpdate]);
```

### Monitor API Calls

In browser DevTools → Network tab:
- Filter by: `gamma-data`
- Check response status: 200 OK
- Inspect response body: Valid JSON
- Check timing: Should complete in < 500ms

---

## Performance Issues

### Symptom: Slow Chart Rendering

**Solutions:**

1. **Reduce data points:**
   ```typescript
   const candleData = generateCandlestickData(primarySymbol, 30); // Reduce from 60
   ```

2. **Limit gamma walls:**
   ```typescript
   if (adjustedStrength < settings.minStrength) return; // Increase minStrength
   if (settings.hideWeakWalls && adjustedStrength < 40) return;
   ```

3. **Use React.memo:**
   ```typescript
   export const GammaChartCanvasV3 = React.memo<GammaChartCanvasV3Props>(({ ... }) => {
     // Component logic
   });
   ```

4. **Debounce settings changes:**
   ```typescript
   import { debounce } from 'lodash';

   const debouncedSettingsChange = useMemo(
     () => debounce(handleSettingsChange, 300),
     []
   );
   ```

---

## Browser Console Commands

### Useful Debug Commands

```javascript
// Check current state
window.__GAMMA_SCANNER_DEBUG = true;

// Force refresh data
// (In browser console after opening Gamma Scanner tab)
document.querySelector('[data-gamma-refresh]')?.click();

// Clear localStorage
localStorage.removeItem('gammaScanner.settings');
localStorage.removeItem('gammaScanner.lastData');
location.reload();

// Check parsed symbols
console.table(
  JSON.parse(localStorage.getItem('gammaScanner.lastData') || '[]')
);
```

---

## Getting Help

If issues persist:

1. **Check console errors:**
   - Browser DevTools → Console tab
   - Look for red error messages

2. **Check backend logs:**
   ```bash
   # Backend terminal output
   # Look for:
   # ✓ Gamma Wall Scanner API registered
   # INFO: Uvicorn running on http://0.0.0.0:8000
   ```

3. **Verify file versions:**
   ```bash
   grep -r "v3.0" frontend/src/components/GammaScanner/
   ```

4. **Check documentation:**
   - `V3_TRADINGVIEW_INTEGRATION.md` - Full feature guide
   - `README.md` - Integration overview
   - `V2_DESIGN.md` - Design philosophy

---

**Last Updated:** November 7, 2025
