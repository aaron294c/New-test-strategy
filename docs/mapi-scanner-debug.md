# MAPI Scanner Debugging Guide

## ✅ Backend is Working

Tested successfully:
```bash
curl -X POST 'https://new-test-strategy.onrender.com/api/mapi-scanner' \
  -H 'Content-Type: application/json' \
  -d '{"symbols": ["AAPL", "META"], "composite_threshold": 35, "edr_threshold": 20}'

# Returns:
{
  "success": true,
  "signals": [
    {
      "symbol": "AAPL",
      "composite_percentile": 52.8,
      "win_rate": 46.9,
      ...
    },
    {
      "symbol": "META",
      "composite_percentile": 79.2,
      "win_rate": 53.3,
      ...
    }
  ]
}
```

## 🔍 Frontend Debugging Steps

### 1. Wait for Vercel Deploy (~3-5 minutes)
Check: https://vercel.com/[your-account]/[project]/deployments
- Latest commit: `f4588df` (debugging improvements)
- Wait until status shows "Ready"

### 2. Hard Refresh Browser
- Windows/Linux: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`
- This clears cached JavaScript

### 3. Open DevTools Console
Press `F12` or right-click → Inspect → Console tab

### 4. Navigate to MAPI Scanner
1. Go to MAPI tab
2. Click "Market Scanner" toggle button
3. Watch console output

### Expected Console Logs:

#### **If Component Renders:**
```
[MAPI Scanner] Component rendering
[MAPI Scanner] Scanning with params: {symbols: [...], composite_threshold: 35, ...}
[MAPI Scanner] Scan result: {success: true, signals: [...]}
[MAPI Scanner] Scan successful: ...
```

#### **If API Error:**
```
[MAPI Scanner] Component rendering
[MAPI Scanner] Scanning with params: ...
[MAPI Scanner] Scan error: AxiosError...
```

#### **If Component Doesn't Render:**
```
(no logs at all)
```
→ Component isn't being imported or mounted

### 5. Check Network Tab
1. DevTools → Network tab
2. Filter by "mapi-scanner"
3. Click the request
4. Check:
   - Status: Should be `200 OK`
   - Response: Should have `success: true` and `signals: [...]`
   - Headers: Should have CORS headers

### 6. Common Issues

**Issue: No console logs at all**
- Solution: Check if tab switch is working
- Try: Click "Chart Analysis" then "Market Scanner" again

**Issue: "Network Error" or "Failed to fetch"**
- Solution: CORS or backend down
- Check backend health: https://new-test-strategy.onrender.com/api/health

**Issue: "Component not found" or TypeScript error**
- Solution: Vercel build failed
- Check Vercel deployment logs

**Issue: Table shows but no data**
- Check console for scan errors
- Check Network tab for API response

## 🎯 What You Should See

Once working, the scanner should display:

```
┌─────────────────────────────────────────────────────────────┐
│ MAPI Market Scanner - Entry Opportunities      [Refresh]   │
├─────────────────────────────────────────────────────────────┤
│ Extreme Low (≤20%): 0  │  Low (20-35%): 0  │  Not in Zone: 2│
└─────────────────────────────────────────────────────────────┘

┌──────────┬────────┬──────────┬──────────┬────────┬────────┐
│ Symbol   │ Price  │ Comp Raw │ Comp %ile│ EDR %  │ ESV %  │
├──────────┼────────┼──────────┼──────────┼────────┼────────┤
│ AAPL     │ $248   │ 49.82    │ 52.8%    │ 13.6%  │ 0.0%   │
│ META  🔺 │ $659   │ 51.34    │ 79.2%    │ 91.5%  │ 42.7%  │
└──────────┴────────┴──────────┴──────────┴────────┴────────┘
```

## 🚀 Quick Test Locally

If Vercel is slow, test locally:

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
# Navigate to MAPI → Market Scanner
```

This bypasses Vercel and tests immediately.

## 📝 Report Back

Please share:
1. Console logs (any messages with `[MAPI Scanner]`)
2. Network tab status for `/api/mapi-scanner`
3. Any error messages or red text in console
4. Screenshot if table appears but looks wrong

This will help me identify the exact issue!
