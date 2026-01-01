# Vercel Frontend Setup

## ✅ Backend is Live!

Your backend is successfully deployed at:
```
https://new-test-strategy.onrender.com
```

## 🔗 Connect Frontend to Backend

### Option 1: Vercel Dashboard (Recommended)

1. **Go to Vercel Dashboard**
   - Visit https://vercel.com/dashboard
   - Sign in to your account

2. **Select Your Project**
   - Click on your frontend project

3. **Add Environment Variable**
   - Go to **Settings** tab
   - Click **Environment Variables** in the left sidebar
   - Click **Add New**
   - Enter:
     ```
     Name: VITE_API_URL
     Value: https://new-test-strategy.onrender.com
     ```
   - OR if you're using Create React App:
     ```
     Name: REACT_APP_API_URL
     Value: https://new-test-strategy.onrender.com
     ```
   - Select: **Production, Preview, Development** (all environments)
   - Click **Save**

4. **Redeploy**
   - Go to **Deployments** tab
   - Click the three dots (•••) on the latest deployment
   - Click **Redeploy**
   - Wait for deployment to complete (~1-2 minutes)

### Option 2: Vercel CLI

```bash
# Install Vercel CLI if needed
npm i -g vercel

# Add environment variable
vercel env add VITE_API_URL production
# Paste: https://new-test-strategy.onrender.com

# Or for React
vercel env add REACT_APP_API_URL production
# Paste: https://new-test-strategy.onrender.com

# Redeploy
vercel --prod
```

### Option 3: Update Local .env and Push

1. Create or update `.env` file in your frontend directory:
   ```bash
   VITE_API_URL=https://new-test-strategy.onrender.com
   ```
   OR
   ```bash
   REACT_APP_API_URL=https://new-test-strategy.onrender.com
   ```

2. Commit and push:
   ```bash
   git add .env
   git commit -m "Add production API URL"
   git push
   ```

3. Vercel will auto-redeploy

## 🧪 Test Your Backend

Your backend has these working endpoints:

**Health Check:**
```bash
curl https://new-test-strategy.onrender.com/api/health
```

**Get Available Tickers:**
```bash
curl https://new-test-strategy.onrender.com/api/tickers
```

**Get Backtest Data:**
```bash
curl https://new-test-strategy.onrender.com/api/backtest/AAPL
```

**Get Live Signal:**
```bash
curl https://new-test-strategy.onrender.com/api/live-signal/AAPL
```

## 📝 Update Your Frontend Code

Make sure your frontend is using the environment variable:

**For Vite (React/Vue):**
```javascript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

**For Create React App:**
```javascript
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

**For Next.js:**
```javascript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

## 🔒 Security (Optional - After Testing)

Once everything works, lock down CORS to only your Vercel domain:

1. Go to Render Dashboard → Your Service
2. Environment → Add Variable:
   ```
   ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
   ```
3. Save (will auto-redeploy)

## ✅ Verification Checklist

- [ ] Backend URL confirmed: https://new-test-strategy.onrender.com
- [ ] Health endpoint returns `{"status": "healthy"}`
- [ ] Environment variable added to Vercel
- [ ] Frontend redeployed
- [ ] Frontend can fetch data from backend
- [ ] No CORS errors in browser console

## 🐛 Troubleshooting

**Issue: CORS errors**
- Solution: Backend already allows all origins (`allow_origins=["*"]`)
- Check browser console for specific error

**Issue: 404 errors**
- Solution: Make sure you're using the correct endpoint paths (they all start with `/api/`)

**Issue: Slow first request**
- Solution: Render Free tier sleeps after 15min. First request takes 30-60s
- Upgrade to Starter ($7/mo) for always-on service

## 🎯 Next Steps

1. Add environment variable to Vercel
2. Redeploy frontend
3. Test the connection
4. Enjoy your full-stack app! 🚀
