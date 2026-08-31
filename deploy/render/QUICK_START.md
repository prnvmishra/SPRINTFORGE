# 🚀 Render Quick Start - No Credit Card Required

## ⚡ 10-Minute Render Deployment

### Prerequisites
- GitHub account
- Render account (free, no credit card)
- SprintForge code on GitHub

---

## 🚀 Step-by-Step Deployment

### Step 1: Build Case Store (7 minutes)

```bash
cd backend
python -m scripts.build_test_cases
python -m scripts.split_case_bank
python -m scripts.build_curriculum_manifest
```

### Step 2: Push to GitHub (1 minute)

```bash
git add .
git commit -m "Add case store for Render deployment"
git push origin master
```

### Step 3: Create Render Account (1 minute)

1. **Go to:** https://render.com
2. **Sign up** with GitHub
3. **No credit card required**

### Step 4: Deploy with Blueprint (2 minutes)

1. **Copy render-neon.yaml** to your project root
2. **In Render Dashboard:**
   - Click "New +"
   - Select "Blueprint"
   - Connect your GitHub repository
   - Select `render-neon.yaml`
   - Click "Apply"

### Step 5: Update Vercel (1 minute)

1. **Get Render URL** from dashboard (e.g., `https://sprintforge-api.onrender.com`)
2. **Update Vercel:**
   - Go to Vercel → Settings → Environment Variables
   - Update `NEXT_PUBLIC_API_URL` to Render URL
   - Redeploy

### Step 6: Test (1 minute)

```bash
curl https://your-render-url.onrender.com/health
```

---

## 📋 Important Notes

### **Database Configuration**
- Using your existing Neon database (no 90-day limit)
- DATABASE_URL already configured in render-neon.yaml

### **Memory Optimization**
- Render free tier has limited RAM
- SprintForge is optimized (96MB boot memory)
- Should work within limits

### **Build Time**
- Case store already built locally
- Render will use committed files
- Build time: ~5 minutes

---

## 🎯 Expected Result

**Backend URL:** `https://sprintforge-api.onrender.com`

**Health Check:** `https://sprintforge-api.onrender.com/health`

**Frontend:** `https://your-app.vercel.app` (connected to Render)

**Monthly Cost:** $0 (within free tier)

**Reliability:** Good (with 50-second cold starts on free tier)

---

## ⚠️ Limitations

- **Cold starts:** 50-second delay after inactivity
- **Database:** Neon (unlimited time, unlike Render's 90-day PostgreSQL)
- **Memory:** Free tier limited but SprintForge optimized

---

## 🚨 Troubleshooting

### Build Fails - Case Store Missing

```bash
# Make sure case store is committed
cd backend
git add app/data/cases/
git commit -m "Add case store"
git push origin master
```

### Cold Start Issues

**Solution:** Keep service warm by hitting it periodically
```bash
# Every 10 minutes
curl https://your-render-url.onrender.com/health
```

### Memory Issues

**Solution:** Reduce dependencies or upgrade to paid tier

---

## 💡 Pro Tips

1. **Use Neon database** - No time limit
2. **Keep case store in Git** - Faster builds
3. **Monitor usage** - Stay within 750 hours/month
4. **Consider upgrade** - For hackathon demo (avoid cold starts)

---

## ✅ Summary

**Render + Neon = Perfect No-Credit-Card Solution**

- ✅ No credit card required
- ✅ Docker support
- ✅ Unlimited database (Neon)
- ✅ Auto SSL
- ✅ Git deployment
- ✅ $0/month

**Perfect for your hackathon!** 🏆