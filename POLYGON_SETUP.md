# Polygon.io Setup - Get Real Greeks & IV

## ✅ Why Polygon.io?
- **Real calculated Greeks** from market data
- **Accurate IV** - not estimated
- **Free tier** - No credit card required
- **5 API calls/minute** - Perfect for LEAPS scanning
- **Reliable** - Used by professional traders

## 🚀 Quick Setup (3 minutes)

### Step 1: Sign Up (FREE - No Credit Card)
Go to: **https://polygon.io/dashboard/signup**
- Enter email and create password
- No credit card required for free tier

### Step 2: Get API Key
1. Log in to: **https://polygon.io/dashboard**
2. Click on **"API Keys"** in sidebar
3. Copy your API key (looks like: `abc123xyz...`)

### Step 3: Set Environment Variable

**Windows (Command Prompt):**
```cmd
setx POLYGON_API_KEY your_key_here
```

**Windows (PowerShell):**
```powershell
$env:POLYGON_API_KEY="your_key_here"
# Make permanent:
[Environment]::SetEnvironmentVariable("POLYGON_API_KEY", "your_key_here", "User")
```

**Linux/Mac:**
```bash
export POLYGON_API_KEY=your_key_here
# Add to ~/.bashrc or ~/.zshrc to make permanent
```

### Step 4: Restart Backend
```bash
cd backend
python api.py
```

## ✅ Verify It's Working

Backend logs should show:
```
✓ Polygon API key found
Using Polygon.io API for accurate Greeks and IV
✓ Fetched X LEAPS options from Polygon with real Greeks
```

## 📊 What You'll Get

**Before (yfinance calculated Greeks):**
- Vega: 0.418 - 1.219 ❌ TOO HIGH
- IV: Unreliable for deep ITM
- Delta: Estimated

**After (Polygon real Greeks):**
- Vega: 0.02 - 0.15 ✅ CORRECT
- IV: Real market IV
- All Greeks: Actual calculated values

## 🎯 Free Tier Limits

**Perfect for LEAPS scanning:**
- **5 API calls per minute**
- Fetches ~20-30 LEAPS per scan
- Takes 1-2 minutes per scan (rate limiting)
- Plenty for analyzing LEAPS strategies

**If you need more:**
- Starter plan: $29/month (100 calls/min)
- Advanced plans available

## 🔧 Troubleshooting

**"Polygon API key not configured"**
- Make sure you set the environment variable
- Restart your terminal/command prompt
- Restart the backend after setting

**"Rate limit hit"**
- Normal! Free tier = 5 calls/minute
- System automatically waits and retries
- Just takes a bit longer

**"No options returned"**
- Check that market is open or recently closed
- Polygon provides delayed data on free tier
- Try during/after market hours

## 📝 Example

```bash
# Set the key (Windows)
setx POLYGON_API_KEY abc123yourkey456

# Restart backend
cd backend
python api.py

# Check logs for:
# "✓ Fetched X LEAPS options from Polygon with real Greeks"
```

## 🔒 Security

**Never commit your API key to git!**

The key is read from environment variable only.

## 💡 Tip

The system automatically falls back to yfinance if Polygon is not configured, so you can test without the API key first, then add it when ready for accurate data.
