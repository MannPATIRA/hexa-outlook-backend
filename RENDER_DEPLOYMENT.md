# Step-by-Step Render Deployment Guide

Follow these exact steps to deploy your FastAPI backend on Render.

---

## Step 1: Push Your Code to GitHub

**If you haven't already:**

1. Make sure all your files are committed:
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   ```

2. Push to GitHub:
   ```bash
   git push origin main
   ```
   (or `git push origin master` if your main branch is called `master`)

**If your code is already on GitHub, skip to Step 2.**

---

## Step 2: Sign Up / Log In to Render

1. Go to **[render.com](https://render.com)**
2. Click **"Get Started for Free"** (or **"Sign In"** if you already have an account)
3. Sign up with:
   - **GitHub** (recommended - easiest way to connect your repo)
   - Or email/password

---

## Step 3: Create a New Web Service

1. Once logged in, you'll see the Render dashboard
2. Click the **"New +"** button (top right)
3. Select **"Web Service"** from the dropdown

---

## Step 4: Connect Your GitHub Repository

1. Render will show you a list of your GitHub repositories
2. **Find and click on `hexa-outlook-backend`** (or search for it)
3. Click **"Connect"** next to your repository

**If you don't see your repo:**
- Click **"Configure account"** to grant Render access to your GitHub repos
- Make sure you grant access to the repository

---

## Step 5: Configure Your Service

Render will auto-detect settings from your `render.yaml` file, but let's verify:

### Basic Settings:
- **Name:** `hexa-outlook-backend` (or whatever you prefer)
- **Region:** Choose closest to you (e.g., `Oregon (US West)` or `Frankfurt (EU)`)
- **Branch:** `main` (or `master` if that's your branch name)
- **Root Directory:** Leave empty (it will use the root)

### Build & Deploy Settings:
These should be auto-filled from `render.yaml`, but verify:
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `./start.sh`

**If the fields are empty, manually enter:**
- Build Command: `pip install -r requirements.txt`
- Start Command: `./start.sh`

### Advanced Settings (Optional):
- **Auto-Deploy:** `Yes` (deploys automatically on every push)
- **Plan:** `Free` (or choose a paid plan if you want)

---

## Step 6: Add Environment Variables

Scroll down to the **"Environment Variables"** section.

### Required Variables:
**None are strictly required** - your app works without them, but add these if you want the features:

1. **OPENAI_API_KEY** (Optional - for LLM email classification):
   - Click **"Add Environment Variable"**
   - Key: `OPENAI_API_KEY`
   - Value: `your_openai_api_key_here`
   - Click **"Save"**

2. **DEMO_SUPPLIER_EMAIL** (Optional - for demo auto-reply feature):
   - Click **"Add Environment Variable"**
   - Key: `DEMO_SUPPLIER_EMAIL`
   - Value: `your_demo_email@gmail.com`
   - Click **"Save"**

3. **DEMO_SUPPLIER_PASSWORD** (Optional - Gmail app password for demo):
   - Click **"Add Environment Variable"**
   - Key: `DEMO_SUPPLIER_PASSWORD`
   - Value: `your_gmail_app_password`
   - Click **"Save"**

4. **DEMO_SUPPLIER_NAME** (Optional):
   - Click **"Add Environment Variable"**
   - Key: `DEMO_SUPPLIER_NAME`
   - Value: `ABC Manufacturing (Demo)`
   - Click **"Save"**

**Note:** You can add these later if needed. The app will work without them.

---

## Step 7: Deploy!

1. Scroll to the bottom of the page
2. Click **"Create Web Service"**
3. Render will start building your app - you'll see a build log
4. Wait 2-5 minutes for the build to complete

**What's happening:**
- Render is installing Python dependencies from `requirements.txt`
- Building your application
- Starting your FastAPI server

---

## Step 8: Wait for Deployment

You'll see a live log showing:
- `Cloning repository...`
- `Installing dependencies...`
- `Building...`
- `Starting service...`
- `Your service is live at https://hexa-outlook-backend.onrender.com`

**⏱️ First deployment takes 3-5 minutes**

---

## Step 9: Test Your Deployment

Once you see **"Your service is live"**, test it:

1. **Health Check:**
   - Visit: `https://hexa-outlook-backend.onrender.com/health`
   - Should return: `{"status": "healthy", "service": "outlook-add-in-backend"}`

2. **API Docs:**
   - Visit: `https://hexa-outlook-backend.onrender.com/docs`
   - Should show Swagger UI with all your API endpoints

3. **Root Endpoint:**
   - Visit: `https://hexa-outlook-backend.onrender.com/`
   - Should show API information

---

## Step 10: Get Your API URL

Your API is now live at:
```
https://hexa-outlook-backend.onrender.com
```

**Save this URL!** You'll need it for your Outlook add-in.

You can also find it in:
- Render Dashboard → Your Service → Settings → "Service Details"
- It's shown at the top of your service page

---

## ✅ You're Done!

Your backend is now deployed and accessible from anywhere.

---

## 🔄 Future Updates

**Every time you push to GitHub:**
- Render will automatically detect the change
- It will rebuild and redeploy your app
- Takes 2-5 minutes per deployment

**To manually trigger a deploy:**
- Go to your service in Render dashboard
- Click **"Manual Deploy"** → **"Deploy latest commit"**

---

## 🚨 Troubleshooting

### Build Fails

**Error: "Module not found" or "Import error"**
- Check that all dependencies are in `requirements.txt`
- Make sure Python version is correct (3.11)

**Error: "Command not found: ./start.sh"**
- Make sure `start.sh` is in your repository
- Check that it's executable (should be fine if you committed it)

**Error: "Port already in use"**
- This shouldn't happen - Render sets PORT automatically
- Check that `start.sh` uses `$PORT` variable

### Service Won't Start

**Check the logs:**
- Go to your service in Render dashboard
- Click **"Logs"** tab
- Look for error messages

**Common issues:**
- Missing environment variables (if your code requires them)
- Import errors
- Port binding issues

### Service Spins Down (Free Tier)

**On Render's free tier:**
- Services spin down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds
- This is normal for free tier

**To prevent spin-down:**
- Upgrade to a paid plan ($7/month)
- Or use a service like UptimeRobot to ping your service every 10 minutes

---

## 📝 Next Steps

1. **Update your Outlook add-in:**
   - Change the API base URL to: `https://hexa-outlook-backend.onrender.com`
   - Test all endpoints

2. **Update CORS (if needed):**
   - Edit `app/main.py` line 36
   - Replace `allow_origins=["*"]` with your Outlook add-in domain:
     ```python
     allow_origins=["https://outlook.office.com", "https://outlook.live.com"]
     ```
   - Commit and push - Render will auto-deploy

3. **Set up monitoring (optional):**
   - Add error tracking (Sentry, etc.)
   - Set up uptime monitoring

---

## 🎉 Congratulations!

Your FastAPI backend is now live on Render!

**Your API URL:** `https://hexa-outlook-backend.onrender.com`
