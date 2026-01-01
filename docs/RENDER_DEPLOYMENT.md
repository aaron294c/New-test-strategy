# Render Deployment Guide

## Backend Deployment to Render

### Option 1: Deploy via Dashboard (Recommended)

1. **Go to Render Dashboard**
   - Visit https://dashboard.render.com/
   - Sign in with your account

2. **Create New Web Service**
   - Click "New +" button
   - Select "Web Service"

3. **Connect Repository**
   - Connect your GitHub repository
   - Or use "Deploy from Git URL" and paste your repo URL

4. **Configure Service**
   ```
   Name: rsi-ma-backend
   Region: Oregon (or closest to your users)
   Branch: main
   Runtime: Python 3

   Build Command:
   pip install -r backend/requirements.txt

   Start Command:
   cd backend && uvicorn api:app --host 0.0.0.0 --port $PORT
   ```

5. **Set Environment Variables**
   ```
   PYTHON_VERSION=3.11.0
   ALLOWED_ORIGINS=*
   ```

   **Note:** After deployment, update ALLOWED_ORIGINS to your Vercel domain:
   ```
   ALLOWED_ORIGINS=https://your-app.vercel.app
   ```

6. **Configure Health Check**
   ```
   Health Check Path: /api/health
   ```

7. **Select Plan**
   - Choose "Starter" for $7/month
   - Or "Free" (with limitations: sleeps after 15min inactivity)

8. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (usually 2-5 minutes)

### Option 2: Deploy via render.yaml (Infrastructure as Code)

1. **Blueprint Setup**
   - The `render.yaml` file is already in your project root
   - Go to https://dashboard.render.com/
   - Click "New +" → "Blueprint"
   - Connect your repository
   - Render will auto-detect the `render.yaml` file

2. **Review Configuration**
   - Verify the settings match your requirements
   - Click "Apply"

### After Deployment

1. **Get Your Backend URL**
   - After deployment completes, Render provides a URL like:
   ```
   https://rsi-ma-backend.onrender.com
   ```

2. **Test the Backend**
   ```bash
   curl https://rsi-ma-backend.onrender.com/api/health
   ```

   Expected response:
   ```json
   {
     "status": "healthy",
     "timestamp": "2026-01-01T12:00:00.000000"
   }
   ```

3. **Update Vercel Frontend**
   - Go to your Vercel project settings
   - Add environment variable:
   ```
   REACT_APP_API_URL=https://rsi-ma-backend.onrender.com
   ```
   - Or update your `.env` file:
   ```
   VITE_API_URL=https://rsi-ma-backend.onrender.com
   ```
   - Redeploy frontend

4. **Update CORS (Security)**
   - Once frontend is deployed, update backend environment variable:
   ```
   ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
   ```
   - This restricts API access to only your frontend

## Monitoring

- **Logs**: View in Render Dashboard → Your Service → Logs
- **Metrics**: Dashboard shows CPU, Memory, Request metrics
- **Alerts**: Set up alerts for downtime

## Troubleshooting

### Issue: Service won't start
- Check logs for Python dependency errors
- Verify `requirements.txt` has all dependencies
- Ensure Python version is compatible (3.11+)

### Issue: Health check failing
- Verify `/api/health` endpoint is accessible
- Check if FastAPI is binding to `0.0.0.0:$PORT`
- Confirm PORT environment variable is set

### Issue: CORS errors on frontend
- Update `ALLOWED_ORIGINS` to include your Vercel domain
- Use wildcard `*` for testing only
- Check browser console for specific CORS error

### Issue: Free tier service sleeping
- Render Free tier sleeps after 15min inactivity
- First request after sleep takes 30-60 seconds
- Upgrade to Starter ($7/mo) for always-on service
- Or use a ping service to keep it awake

## Cost Estimate

- **Free Tier**: $0/month (sleeps after 15min)
- **Starter**: $7/month (always on, 512MB RAM)
- **Standard**: $25/month (2GB RAM)

## Next Steps

1. Deploy backend to Render
2. Copy the deployment URL
3. Update frontend environment variables
4. Test the connection
5. Lock down CORS to your Vercel domain
