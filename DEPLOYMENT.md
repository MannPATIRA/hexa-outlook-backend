# Deployment Guide

This guide covers the easiest ways to deploy your FastAPI backend.

## 🚀 Recommended: Railway (Easiest)

**Railway** is the easiest option with automatic deployments from GitHub.

### Steps:

1. **Sign up at [railway.app](https://railway.app)** (free tier available)

2. **Create a new project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `hexa-outlook-backend` repository

3. **Railway will auto-detect Python:**
   - It will automatically detect your `requirements.txt` and `Procfile`
   - The `Procfile` tells Railway how to start your app
   - No additional configuration needed!

4. **Set environment variables:**
   - Go to your project → Variables tab
   - Add these (if needed):
     ```
     OPENAI_API_KEY=your_key_here
     DEMO_SUPPLIER_EMAIL=your_email@example.com
     DEMO_SUPPLIER_PASSWORD=your_app_password
     DEMO_SUPPLIER_NAME=Your Supplier Name
     ```

5. **Deploy:**
   - Railway automatically deploys on every push to your main branch
   - Your API will be live at: `https://your-app-name.up.railway.app`

6. **Get your URL:**
   - Railway provides a public URL automatically
   - You can also add a custom domain

**Cost:** Free tier includes $5/month credit (usually enough for small apps)

---

## 🆓 Alternative: Render (Free Tier)

**Render** offers a free tier with automatic deployments.

### Steps:

1. **Sign up at [render.com](https://render.com)** (free tier available)

2. **Create a new Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select `hexa-outlook-backend`

3. **Configure the service:**
   - **Name:** `hexa-outlook-backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - The `render.yaml` file is already configured for you!

4. **Set environment variables:**
   - Scroll down to "Environment Variables"
   - Add:
     ```
     OPENAI_API_KEY=your_key_here
     DEMO_SUPPLIER_EMAIL=your_email@example.com
     DEMO_SUPPLIER_PASSWORD=your_app_password
     DEMO_SUPPLIER_NAME=Your Supplier Name
     ```

5. **Deploy:**
   - Click "Create Web Service"
   - Render will build and deploy automatically
   - Your API will be live at: `https://hexa-outlook-backend.onrender.com`

**Note:** Free tier services spin down after 15 minutes of inactivity (first request after spin-down takes ~30 seconds)

**Cost:** Free tier available, paid plans start at $7/month

---

## ⚡ Alternative: Vercel

**Vercel** works but requires more configuration for FastAPI.

### Steps:

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Deploy:**
   ```bash
   vercel
   ```

3. **Set environment variables:**
   - Go to your project on [vercel.com](https://vercel.com)
   - Settings → Environment Variables
   - Add your variables

4. **Note:** Vercel is serverless, so long-running tasks might timeout. Railway/Render are better for this use case.

**Cost:** Free tier available, but better for frontend/API routes

---

## 🔧 Environment Variables

Set these in your deployment platform:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Optional | For LLM email classification features |
| `DEMO_SUPPLIER_EMAIL` | Optional | Gmail for demo auto-reply feature |
| `DEMO_SUPPLIER_PASSWORD` | Optional | Gmail app password for demo feature |
| `DEMO_SUPPLIER_NAME` | Optional | Name for demo supplier |

**Note:** The app works without any environment variables - they're only needed for specific features.

---

## ✅ Post-Deployment Checklist

1. **Test your API:**
   - Visit `https://your-app-url/health` - should return `{"status": "healthy"}`
   - Visit `https://your-app-url/docs` - should show Swagger UI

2. **Update CORS (if needed):**
   - Edit `app/main.py` line 36
   - Replace `allow_origins=["*"]` with your Outlook add-in domain:
     ```python
     allow_origins=["https://outlook.office.com", "https://outlook.live.com"]
     ```

3. **Update your Outlook add-in:**
   - Change API base URL to your deployed URL
   - Test all endpoints

---

## 🎯 Quick Comparison

| Platform | Ease | Free Tier | Auto Deploy | Best For |
|----------|------|-----------|-------------|----------|
| **Railway** | ⭐⭐⭐⭐⭐ | ✅ $5/month credit | ✅ | **Recommended** |
| **Render** | ⭐⭐⭐⭐ | ✅ (spins down) | ✅ | Good alternative |
| **Vercel** | ⭐⭐⭐ | ✅ | ✅ | Frontend/API routes |
| Fly.io | ⭐⭐⭐ | ✅ | ✅ | More complex setup |

---

## 🚨 Troubleshooting

### Port Issues
- Railway/Render set `PORT` environment variable automatically
- Your app should use `$PORT` or `0.0.0.0` (already configured)

### Import Errors
- Make sure `requirements.txt` includes all dependencies
- Check that Python version matches (3.11 recommended)

### Environment Variables Not Working
- Make sure variables are set in the platform dashboard
- Restart the service after adding variables

### CORS Errors
- Update `allow_origins` in `app/main.py` with your frontend domain

---

## 📝 Next Steps

1. Choose a platform (Railway recommended)
2. Deploy following the steps above
3. Test your endpoints
4. Update your Outlook add-in with the new API URL
5. Celebrate! 🎉
