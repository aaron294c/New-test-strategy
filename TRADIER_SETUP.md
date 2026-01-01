# Tradier API Setup - Get Real Greeks & IV

## Why Tradier?
- ✅ **Real calculated Greeks** (not estimated from Black-Scholes)
- ✅ **Accurate IV** from actual market data
- ✅ **Free sandbox account** for developers
- ✅ **No more vega/IV calculation issues**

## Quick Setup (5 minutes)

### Step 1: Create Free Sandbox Account
1. Go to: https://developer.tradier.com/user/sign_up
2. Fill in email and create password
3. Verify your email

### Step 2: Get Your Sandbox API Token
1. Log in to: https://developer.tradier.com/user/settings
2. Look for **Sandbox Account** section
3. Copy your **Access Token** (starts with something like `ABC123xyz...`)

### Step 3: Configure Environment Variable

**Windows (Command Prompt):**
```cmd
set TRADIER_API_KEY=Bearer YOUR_TOKEN_HERE
```

**Windows (PowerShell):**
```powershell
$env:TRADIER_API_KEY="Bearer YOUR_TOKEN_HERE"
```

**Linux/Mac:**
```bash
export TRADIER_API_KEY="Bearer YOUR_TOKEN_HERE"
```

**Make it permanent (Windows):**
```cmd
setx TRADIER_API_KEY "Bearer YOUR_TOKEN_HERE"
```

### Step 4: Install requests library
```bash
cd backend
pip install requests
```

### Step 5: Restart Backend
```bash
cd backend
python api.py
```

## Verify It's Working

You should see in the backend logs:
```
✓ Fetched X LEAPS options from Tradier with real Greeks
```

The UI will now show:
- ✅ Correct vega values (0.02-0.15 for deep ITM)
- ✅ Accurate IV from market data
- ✅ Real calculated Greeks from Tradier

## Fallback Behavior

If Tradier is not configured, the system automatically falls back to yfinance with calculated Greeks (less accurate).

## Rate Limits

**Sandbox (Free):**
- 120 requests per minute
- 20,000 requests per day
- Delayed data (15-20 minutes)

**Production (Paid):**
- Higher limits
- Real-time data
- $0/month for basic, $75/month for pro

For this LEAPS scanner, sandbox is perfect since we're analyzing longer-term options.

## Troubleshooting

**"Tradier API not configured"**
- Make sure you set the environment variable correctly
- Remember to include "Bearer " before your token
- Restart your terminal/command prompt after setting the variable

**"401 Unauthorized"**
- Check that your token is correct
- Make sure you copied it from the Sandbox section, not Brokerage

**"No options data returned"**
- Sandbox uses delayed data, so some expirations might be missing
- Try during market hours for better data availability

## Example Token Format

```
TRADIER_API_KEY=Bearer AbCdEf123456YourActualTokenHere789
```

**Important:** Never commit your API token to git!
