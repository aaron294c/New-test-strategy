# Installation Verification Checklist

Use this checklist to verify your installation is complete and working correctly.

## ✅ Pre-Installation Checks

### System Requirements
- [ ] Python 3.9 or higher installed: `python3 --version`
- [ ] Node.js 18 or higher installed: `node --version`
- [ ] npm installed: `npm --version`
- [ ] Git installed (optional): `git --version`
- [ ] Docker installed (if using Docker): `docker --version`

### Disk Space
- [ ] At least 2GB free space available
- [ ] Internet connection for downloading data

## ✅ File Structure Verification

### Backend Files
```bash
cd backend
ls -la
```

**Should see**:
- [ ] `enhanced_backtester.py` (830 lines)
- [ ] `monte_carlo_simulator.py` (400 lines)
- [ ] `api.py` (450 lines)
- [ ] `requirements.txt`
- [ ] `Dockerfile`

### Frontend Files
```bash
cd frontend
ls -la src/
```

**Should see**:
- [ ] `src/App.tsx`
- [ ] `src/main.tsx`
- [ ] `src/components/` directory
- [ ] `src/api/` directory
- [ ] `src/types/` directory
- [ ] `package.json`
- [ ] `vite.config.ts`
- [ ] `Dockerfile`

### Root Files
```bash
ls -la
```

**Should see**:
- [ ] `README.md`
- [ ] `QUICKSTART.md`
- [ ] `PROJECT_SUMMARY.md`
- [ ] `docker-compose.yml`
- [ ] `start.sh` (executable)
- [ ] `.env.example`
- [ ] `.gitignore`

## ✅ Backend Installation

### 1. Virtual Environment
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

**Verify**:
- [ ] `(venv)` appears in terminal prompt
- [ ] `venv/` directory created

### 2. Dependencies
```bash
pip install -r requirements.txt
```

**Verify**:
- [ ] No error messages
- [ ] All packages installed successfully
- [ ] Check: `pip list | grep fastapi` shows FastAPI

### 3. Test Import
```bash
python -c "import fastapi; import pandas; import yfinance; print('✓ All imports successful')"
```

**Expected**: ✓ All imports successful

### 4. Run Backend
```bash
python api.py
```

**Verify**:
- [ ] Server starts without errors
- [ ] See: "Uvicorn running on http://0.0.0.0:8000"
- [ ] See: "RSI-MA Performance Analytics API" banner
- [ ] Visit: http://localhost:8000/docs (Swagger UI loads)
- [ ] Press Ctrl+C to stop

## ✅ Frontend Installation

### 1. Dependencies
```bash
cd frontend
npm install
```

**Verify**:
- [ ] `node_modules/` directory created
- [ ] `package-lock.json` created
- [ ] No errors in console

### 2. Build Check
```bash
npm run build
```

**Verify**:
- [ ] Build completes successfully
- [ ] `dist/` directory created
- [ ] No TypeScript errors

### 3. Run Frontend
```bash
npm run dev
```

**Verify**:
- [ ] Vite server starts
- [ ] See: "Local: http://localhost:3000"
- [ ] Visit: http://localhost:3000 (app loads)
- [ ] Press Ctrl+C to stop

## ✅ Integration Testing

### 1. Start Both Services

**Terminal 1 - Backend**:
```bash
cd backend
source venv/bin/activate
python api.py
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

### 2. Test Dashboard
- [ ] Visit http://localhost:3000
- [ ] Dashboard loads without errors
- [ ] Select ticker from dropdown (e.g., AAPL)
- [ ] Select threshold (e.g., 5%)
- [ ] Click "Refresh Data" button

**Expected**:
- [ ] Loading spinner appears
- [ ] Data loads (may take 20-30 seconds)
- [ ] Performance Matrix tab shows heatmap
- [ ] Return Analysis tab shows charts
- [ ] Optimal Exit tab shows recommendations

### 3. Test API Directly

**With backend running**, open new terminal:

```bash
# Health check
curl http://localhost:8000/api/health

# Get backtest for AAPL
curl http://localhost:8000/api/backtest/AAPL
```

**Expected**:
- [ ] Health check returns: `{"status": "healthy", ...}`
- [ ] Backtest returns JSON data with ticker info

## ✅ Docker Installation (Optional)

### 1. Build Images
```bash
docker-compose build
```

**Verify**:
- [ ] Backend image builds successfully
- [ ] Frontend image builds successfully
- [ ] No build errors

### 2. Start Containers
```bash
docker-compose up -d
```

**Verify**:
- [ ] Both containers start
- [ ] Check: `docker-compose ps` shows 2 running containers
- [ ] Visit: http://localhost:3000 (app loads)

### 3. Check Logs
```bash
docker-compose logs -f
```

**Verify**:
- [ ] No error messages in logs
- [ ] Backend shows API startup
- [ ] Frontend shows nginx running

### 4. Stop Containers
```bash
docker-compose down
```

## ✅ Feature Testing

### Performance Matrix
- [ ] Heatmap displays with colors
- [ ] Hover shows tooltips
- [ ] All 21 days visible (D1-D21)
- [ ] Confidence legend shows at bottom

### Return Distribution
- [ ] Chart shows median line
- [ ] Confidence bands (68%, 95%) visible
- [ ] Benchmark line displayed (if available)
- [ ] Hover shows values

### Optimal Exit Panel
- [ ] Recommended exit day shown
- [ ] Efficiency rankings table populated
- [ ] Trend analysis displayed
- [ ] Risk metrics shown

## ✅ Performance Testing

### Backend Performance
```bash
cd backend
time python -c "from enhanced_backtester import *; b = EnhancedPerformanceMatrixBacktester(['AAPL']); b.run_analysis()"
```

**Expected**:
- [ ] Completes in <60 seconds
- [ ] No memory errors
- [ ] Results printed to console

### Frontend Performance
- [ ] Initial load: <2 seconds
- [ ] Chart render: <500ms
- [ ] Tab switching: <200ms
- [ ] Ticker change: <30 seconds (if uncached)

## 🐛 Common Issues & Solutions

### Backend Issues

**Issue**: `ModuleNotFoundError`
- [ ] Solution: Activate venv and reinstall requirements
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Issue**: Port 8000 already in use
- [ ] Solution: Kill existing process
```bash
lsof -ti:8000 | xargs kill -9
```

**Issue**: yfinance timeout
- [ ] Solution: Check internet connection, try again

### Frontend Issues

**Issue**: `Cannot find module`
- [ ] Solution: Reinstall dependencies
```bash
rm -rf node_modules package-lock.json
npm install
```

**Issue**: Port 3000 already in use
- [ ] Solution: Kill existing process or change port in vite.config.ts

**Issue**: Blank page
- [ ] Solution: Check browser console for errors
- [ ] Verify backend is running
- [ ] Check CORS settings

### Docker Issues

**Issue**: Build fails
- [ ] Solution: Check Dockerfile syntax
- [ ] Ensure Docker daemon is running
```bash
docker info
```

**Issue**: Container exits immediately
- [ ] Solution: Check logs
```bash
docker-compose logs backend
docker-compose logs frontend
```

## ✅ Final Verification

### Smoke Test
Run this complete test sequence:

1. **Start backend**: `cd backend && source venv/bin/activate && python api.py &`
2. **Start frontend**: `cd frontend && npm run dev &`
3. **Wait 10 seconds**
4. **Visit**: http://localhost:3000
5. **Select**: AAPL, 5% threshold
6. **Click**: Refresh Data
7. **Wait**: 30 seconds
8. **Verify**: All three tabs show data
9. **Success**: ✅ Installation verified!

### Cleanup
```bash
# Stop all processes
pkill -f "python api.py"
pkill -f "npm run dev"

# Or use Ctrl+C in each terminal
```

## 📊 Verification Summary

Total checks: ~50+  
Required for basic functionality: ~30  
Optional (Docker, advanced): ~20  

**When all basic checks pass**:
✅ Your installation is complete and ready for use!

## 📚 Next Steps

After verification:
1. Read QUICKSTART.md for usage guide
2. Run first analysis: `python backend/enhanced_backtester.py`
3. Explore the dashboard at http://localhost:3000
4. Check API docs at http://localhost:8000/docs
5. Read README.md for detailed documentation

## 🎉 Congratulations!

You've successfully installed and verified the RSI-MA Performance Analytics Dashboard!

**Need help?** Check:
- README.md for comprehensive guide
- QUICKSTART.md for common tasks
- http://localhost:8000/docs for API reference
