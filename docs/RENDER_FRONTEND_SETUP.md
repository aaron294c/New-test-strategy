# Deploy Frontend to Render

## Quick Setup (5 minutes)

### Step 1: Create New Static Site

1. **Go to Render Dashboard**
   - Visit https://dashboard.render.com/

2. **Click "New +"** (top right)
   - Select **"Static Site"**

### Step 2: Connect Repository

1. **Connect GitHub repository:**
   - Repository: `aaron294c/New-test-strategy`
   - Branch: `main`

2. **Configure Build Settings:**
   ```
   Name: rsi-ma-frontend

   Build Command:
   cd frontend && npm install && npm run build

   Publish Directory:
   frontend/dist
   ```

### Step 3: Add Environment Variable

**Click "Advanced"** and add:

```
Key: VITE_API_URL
Value: https://new-test-strategy.onrender.com
```

### Step 4: Create Static Site

- **Click "Create Static Site"**
- Wait 2-3 minutes for build
- Get your frontend URL!

## Your Complete Architecture

```
Frontend (Render Static Site)
https://rsi-ma-frontend.onrender.com
    ↓
Backend (Render Web Service)
https://new-test-strategy.onrender.com
```

## ✅ Verification

Once deployed:

1. **Frontend URL:** `https://rsi-ma-frontend.onrender.com`
2. **Test it:** Open in browser
3. **Check API calls:** Open DevTools → Network → Should see calls to backend
4. **No CORS errors!** Both are on Render

## 🎉 Benefits of Render for Both

- ✅ No deployment limits (unlike Vercel free tier)
- ✅ Same platform = simpler management
- ✅ No CORS configuration needed
- ✅ Free tier available for both
- ✅ Auto-deploy on git push

## Next Steps

1. Complete the setup above
2. Get your frontend URL
3. Test your app! 🚀
