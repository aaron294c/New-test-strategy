# 🚀 How to View Your Dashboard

## ✅ Setup Complete!

All dependencies are installed. Now start the dashboard:

---

## 📺 **STEP 1: Start the Backend**

Open a **new terminal** and run:

```bash
cd /workspace/backend
python3 api.py
```

You should see:
```
============================================================
RSI-MA Performance Analytics API
============================================================
Cache directory: /workspace/backend/cache
Default tickers: AAPL, MSFT, NVDA, GOOGL, AMZN, META, QQQ, SPY
============================================================

INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ **Backend is ready** when you see "Uvicorn running"

**Keep this terminal open!**

---

## 🎨 **STEP 2: Start the Frontend**

Open a **second terminal** and run:

```bash
cd /workspace/frontend
npm run dev
```

You should see:
```
VITE v5.0.x ready in xxx ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

✅ **Frontend is ready** when you see the Local URL

**Keep this terminal open too!**

---

## 🌐 **STEP 3: Open in Browser**

Visit: **http://localhost:3000**

You should see the **RSI-MA Performance Analytics Dashboard**!

---

## 🎯 **What to Do Next**

1. **Select a ticker** from the dropdown (try AAPL)
2. **Select a threshold** (try 5%)
3. **Click "Refresh Data"**
4. **Wait 20-30 seconds** for the first analysis
5. **Explore the tabs**:
   - 📊 Performance Matrix
   - 📈 Return Analysis  
   - ⚡ Optimal Exit

---

## 🐛 **Troubleshooting**

### Backend won't start?
```bash
# Make sure you're in the right directory
cd /workspace/backend

# Try with full path to uvicorn
python3 -m uvicorn api:app --host 0.0.0.0 --port 8000
```

### Frontend won't start?
```bash
# Make sure dependencies are installed
cd /workspace/frontend
npm install

# Then try again
npm run dev
```

### Port already in use?
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Browser shows "Cannot connect"?
- Make sure **both** backend and frontend are running
- Check that you see "Uvicorn running" in backend terminal
- Check that you see "Local: http://localhost:3000" in frontend terminal

---

## 📊 **Alternative: Run a Backtest First**

Before using the dashboard, you can run a complete analysis:

```bash
cd /workspace/backend
python3 enhanced_backtester.py
```

This will:
- Analyze 8 tickers (AAPL, MSFT, NVDA, etc.)
- Generate D1-D21 performance matrices
- Save results to `backtest_d1_d21_results.json`
- Take about 2-5 minutes

Then the dashboard will load data **instantly** from cache!

---

## 🎉 **You're All Set!**

The dashboard is fully functional and ready to use.

**Questions?** Check:
- README.md for full documentation
- QUICKSTART.md for detailed guide
- http://localhost:8000/docs for API docs
