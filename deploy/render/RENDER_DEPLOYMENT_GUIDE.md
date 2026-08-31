# 🚀 SprintForge.AI - Render Deployment Guide (No Credit Card Required)

## 🎯 Why Render?

- ✅ **No credit card required** for free tier
- ✅ **Docker support** - Perfect for SprintForge
- ✅ **Free PostgreSQL included** - 90 days free
- ✅ **Auto SSL certificates** - HTTPS included
- ✅ **Git-based deployment** - Connect GitHub repo
- ✅ **Auto-scaling** - Scales when needed

---

## 📋 Prerequisites

- GitHub account
- Render account (free)
- SprintForge code on GitHub

---

## 🚀 Step-by-Step Deployment

### Step 1: Create Render Account (2 minutes)

1. **Go to:** https://render.com
2. **Sign up** with GitHub (recommended)
3. **Verify** email address
4. **No credit card required** for free tier

### Step 2: Push Code to GitHub (1 minute)

```bash
# Add all files
git add .
git commit -m "Ready for Render deployment"
git push origin master
```

### Step 3: Deploy to Render (5 minutes)

#### Option A: Using render.yaml (Recommended)

1. **Create `render.yaml` file** in project root (already created)
2. **In Render Dashboard:**
   - Click "New +"
   - Select "Blueprint"
   - Connect your GitHub repository
   - Select the `render.yaml` file
   - Click "Apply"

#### Option B: Manual Setup

1. **Create Web Service:**
   - Click "New +"
   - Select "Web Service"
   - Connect GitHub repository
   - Configure:
     - **Name:** sprintforge-api
     - **Root Directory:** backend
     - **Runtime:** Docker
     - **Dockerfile Path:** Dockerfile
     - **Plan:** Free

2. **Create Database:**
   - Click "New +"
   - Select "PostgreSQL"
   - Configure:
     - **Name:** sprintforge-db
     - **Database:** sprintforge
     - **User:** sprintforge
     - **Plan:** Free (90 days)

3. **Connect Database to Web Service:**
   - Go to sprintforge-api service
   - Environment Variables → Add from Database
   - Select sprintforge-db → DATABASE_URL

### Step 4: Configure Environment Variables

In your Render web service, add these environment variables:

```bash
ENVIRONMENT=production
DATABASE_URL=auto-generated from database
AUTH_SECRET=auto-generated
CORS_ORIGINS=https://your-app.vercel.app
AI_PROVIDER=mock
CODE_EXECUTION_PROVIDER=piston
PISTON_URL=https://emkc.org/api/v2/piston
EXECUTION_TIMEOUT_SECONDS=10
```

### Step 5: Build Case Store (10 minutes)

Since Render builds from Git, you need to include the case store:

```bash
# On your local machine
cd backend
python -m scripts.build_test_cases
python -m scripts.split_case_bank
python -m scripts.build_curriculum_manifest

# Commit the case store
git add app/data/cases/
git commit -m "Add case store for production"
git push origin master
```

### Step 6: Update Vercel Frontend (1 minute)

1. **Get Render URL:** After deployment, Render gives you a URL like:
   `https://sprintforge-api.onrender.com`

2. **Update Vercel:**
   - Go to Vercel → Settings → Environment Variables
   - Update `NEXT_PUBLIC_API_URL` to your Render URL
   - Redeploy Vercel

### Step 7: Test Deployment (2 minutes)

```bash
# Test backend health
curl https://your-render-url.onrender.com/health

# Expected response:
# {"status":"ok","app":"SprintForge.AI","environment":"production",...}

# Test frontend
# Open https://your-app.vercel.app
```

---

## 📊 Render Free Tier Limits

| Resource | Free Tier Limit | SprintForge Needs |
|----------|----------------|-------------------|
| Web Service Hours | 750 hours/month | ~730 hours/month ✅ |
| PostgreSQL | 90 days free | 90 days ✅ |
| RAM | 512MB - 2GB | Might be tight ⚠️ |
| CPU | Shared | Sufficient ✅ |
| Build Time | 15 minutes | 7 minutes ✅ |

---

## ⚠️ Render Limitations for SprintForge

### **Potential Issues:**

1. **Memory Limit:** Render free tier has limited RAM (512MB-2GB)
   - SprintForge needs ~96MB boot memory
   - Should work, but might be tight

2. **Build Time:** 15-minute limit
   - Case store build takes 7 minutes
   - Should be within limits

3. **PostgreSQL Free Duration:** 90 days only
   - After 90 days, need to pay or migrate
   - Solution: Use Neon (external free database)

### **Solutions:**

**Use External Neon Database:**
```bash
# Keep using your existing Neon database
# In Render, don't create PostgreSQL
# Set DATABASE_URL to your Neon connection string
```

---

## 🔧 Alternative: Use External Database

### **Modified render.yaml with Neon:**

```yaml
services:
  - type: web
    name: sprintforge-api
    env: docker
    dockerfilePath: ./backend/Dockerfile
    dockerContext: ./backend
    plan: free
    region: oregon
    
    envVars:
      - key: DATABASE_URL
        value: postgresql://neondb_owner:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
      - key: ENVIRONMENT
        value: production
      - key: AUTH_SECRET
        generateValue: true
      - key: CORS_ORIGINS
        value: https://your-app.vercel.app
      - key: AI_PROVIDER
        value: mock
      - key: CODE_EXECUTION_PROVIDER
        value: piston
      - key: PISTON_URL
        value: https://emkc.org/api/v2/piston
```

---

## 🚨 Troubleshooting

### Build Fails - Memory Issues

```bash
# Reduce memory usage in Dockerfile
# Add this to backend/Dockerfile:
ENV PYTHONUNBUFFERED=1
```

### Database Connection Issues

```bash
# Test connection from local machine
psql $DATABASE_URL

# Check Render logs for database errors
```

### 50-second Cold Starts

Render free tier has cold starts:
- **Solution:** Keep the service warm by hitting it periodically
- **Or upgrade to paid tier** for always-on

---

## 💡 Performance Tips

1. **Use Neon database** - Avoid 90-day PostgreSQL limit
2. **Minimize case store** - Only include essential cases
3. **Use mock AI** - Save processing time
4. **Monitor usage** - Keep within 750 hours/month

---

## 🎯 Final Recommendation

**Render is your best option because:**

1. **No credit card required** ✅
2. **Docker support** ✅
3. **Git-based deployment** ✅
4. **Auto SSL** ✅
5. **Works with Neon database** ✅

**Estimated monthly cost: $0** (within free tier)

---

## 📞 Next Steps

1. **Create Render account:** https://render.com
2. **Push code to GitHub**
3. **Deploy using render.yaml**
4. **Test deployment**
5. **Update Vercel frontend**

**This should work perfectly for your hackathon!** 🚀