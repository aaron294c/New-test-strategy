# MarketData.app Setup - Get Real Greeks & IV (FREE!)

## ✅ Why MarketData.app?
- **Real calculated Greeks** included in FREE tier
- **Accurate Vega** - Expected 0.02-0.15 for deep ITM LEAPS
- **Accurate IV** from market data
- **100 API calls/day** - Perfect for LEAPS scanning
- **No credit card required**

## 🚀 Quick Setup (3 minutes)

### Step 1: Sign Up (FREE - No Credit Card)
1. Go to: **https://www.marketdata.app/dashboard/signup**
2. Enter email and create password
3. Verify your email
4. No credit card required for free tier

### Step 2: Get API Token
1. Log in to: **https://www.marketdata.app/dashboard**
2. Click on **"API Keys"** in the sidebar
3. Copy your API token (looks like: `abc123xyz...`)

### Step 3: Set Environment Variable

**Windows (Command Prompt):**
```cmd
setx MARKETDATA_API_KEY your_token_here
```

**Windows (PowerShell):**
```powershell
$env:MARKETDATA_API_KEY="your_token_here"
# Make permanent:
[Environment]::SetEnvironmentVariable("MARKETDATA_API_KEY", "your_token_here", "User")
```

**Linux/Mac:**
```bash
export MARKETDATA_API_KEY=your_token_here
# Add to ~/.bashrc or ~/.zshrc to make permanent
echo 'export MARKETDATA_API_KEY=your_token_here' >> ~/.bashrc
```

### Step 4: Restart Backend
**IMPORTANT:** Close and restart your terminal/command prompt, then restart the backend:

```bash
cd backend
python api.py
```

## ✅ Verify It's Working

Backend logs should show:
```
✓ MarketData API key found
Using MarketData.app API for accurate Greeks and IV
✓ Fetched X LEAPS options from MarketData with real Greeks
```

## 📊 What You'll Get

**Before (yfinance calculated Greeks):**
- Vega: 0.418 - 1.219 ❌ **TOO HIGH** (unreliable for deep ITM)
- IV: Inflated from low volume
- Delta: Estimated from Black-Scholes

**After (MarketData real Greeks):**
- Vega: 0.02 - 0.15 ✅ **CORRECT** (matches expected for deep ITM)
- IV: Real market IV
- All Greeks: Actual calculated values from options market

## 🎯 Free Tier Limits

**Perfect for LEAPS scanning:**
- **100 API calls per day**
- Fetches ~20-30 LEAPS per scan
- System automatically manages rate limits
- More than enough for daily LEAPS analysis

**If you need more:**
- Starter plan: $9.99/month (250 calls/min)
- Professional plan: $29.99/month (unlimited calls)

## 🔧 Troubleshooting

**"MarketData API key not configured"**
- Make sure you set the environment variable correctly
- **IMPORTANT:** Restart your terminal/command prompt after setting the variable
- Restart the backend (`python api.py`)
- Verify with: `echo %MARKETDATA_API_KEY%` (Windows CMD) or `echo $MARKETDATA_API_KEY` (PowerShell/Linux/Mac)

**"MarketData API failed" or "No options returned"**
- Check that your API key is valid (log in to dashboard)
- Free tier has 100 calls/day - check if you've hit the limit
- Try again after market hours for better data availability
- System automatically falls back to yfinance if MarketData fails

**"Rate limit hit"**
- Normal! Free tier = 100 calls/day
- System automatically waits and retries
- You'll see a warning in logs: "MarketData rate limit, waiting..."
- Scan will continue but take a bit longer

## 📝 Example Setup

```bash
# Windows - Set the key
setx MARKETDATA_API_KEY abc123yourkey456

# Close and reopen your terminal/command prompt

# Restart backend
cd backend
python api.py

# Check logs for:
# "✓ Fetched X LEAPS options from MarketData with real Greeks"
```

## 🔒 Security

**Never commit your API key to git!**

The key is read from environment variable only. It's already in `.gitignore`:
```
.env
*.key
```

## 💡 Automatic Fallback

The system automatically falls back to yfinance if:
- MarketData API key is not configured
- API request fails
- Rate limit is exceeded
- No options data returned

This ensures the app always works, even without the API key configured. However, **for accurate vega and Greeks, you MUST use MarketData.app API**.

## 🎓 Understanding the Data

**Vega Values:**
- Deep ITM LEAPS (delta 0.85-0.98): **Vega 0.02-0.15** ✅
- ATM LEAPS (delta ~0.50): **Vega 0.20-0.40**
- OTM LEAPS (delta <0.40): **Vega 0.10-0.30**

**Why Deep ITM has low vega:**
- Deep ITM options trade like stock (high delta, low gamma)
- Volatility changes have minimal impact on pricing
- Most value is intrinsic, not extrinsic
- Low vega = less sensitivity to IV changes

## 📚 Additional Resources

- MarketData Docs: https://www.marketdata.app/docs/
- API Reference: https://www.marketdata.app/docs/api/
- Dashboard: https://www.marketdata.app/dashboard

---

**Ready to get accurate Greeks?** Sign up for free at https://www.marketdata.app/ and set your API key!
