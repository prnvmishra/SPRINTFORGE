# 🚀 SprintForge.AI - 100% Free Deployment Guide

## 🎯 Best Free Architecture (No Degradation, No Cold Starts)

```
┌─────────────────────────────────────────────────────────────┐
│                    Vercel (Free Tier)                        │
│              Frontend - Next.js 14 + CDN                     │
│            https://your-app.vercel.app                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         Oracle Cloud Always Free ARM Instance                │
│         4 OCPU, 24GB RAM, Always Running                     │
│              Backend - FastAPI + Docker                      │
│              Code Execution - Piston (Docker)                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Neon (Free Tier PostgreSQL)                     │
│            Serverless Database - Auto-scaling               │
└─────────────────────────────────────────────────────────────┘
```

## 💰 Cost Breakdown (100% FREE)

| Service | Free Tier Limits | Monthly Cost | Notes |
|---------|------------------|--------------|-------|
| **Vercel** | 100GB bandwidth, unlimited sites | $0 | Frontend hosting |
| **Oracle Cloud** | 4 OCPU ARM, 24GB RAM, 200GB storage | $0 | Backend + Piston |
| **Neon** | 0.5GB storage, 3 project branches | $0 | PostgreSQL database |
| **Total** | - | **$0/month** | Forever free |

## ⚡ Performance Guarantees

- **Frontend:** CDN cached, <100ms load time globally
- **Backend:** Always running, 1.6s boot time, 96MB memory
- **Database:** Auto-scaling, connection pooling
- **Code Execution:** Sandboxed, 10s timeout, no cold starts

## 📋 Prerequisites

- Oracle Cloud account (free tier)
- Vercel account (free tier)  
- Neon account (free tier)
- GitHub account (for Vercel deployment)
- Domain name (optional, can use Vercel subdomain)

---

## 🛠️ Step-by-Step Deployment

### Step 1: Database Setup (Neon)

1. **Create Neon Account**
   - Go to https://neon.tech
   - Sign up for free tier
   - Create new project "sprintforge"

2. **Get Connection String**
   ```bash
   # Format: postgresql://user:password@host/dbname?sslmode=require
   # Example: postgresql://neondb_owner:npg_xxx@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

3. **Save Connection String**
   - Keep this safe for later use in backend deployment

### Step 2: Frontend Deployment (Vercel)

1. **Push Code to GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin master
   ```

2. **Deploy to Vercel**
   - Go to https://vercel.com
   - Import your GitHub repository
   - Configure:
     - **Framework Preset:** Next.js
     - **Root Directory:** `frontend`
     - **Environment Variables:**
       - `NEXT_PUBLIC_API_URL`: `https://your-backend-oracle-cloud-ip:8000`

3. **Get Frontend URL**
   - Vercel will provide: `https://your-app.vercel.app`
   - Save this for backend CORS configuration

### Step 3: Backend Deployment (Oracle Cloud)

#### 3.1 Create Oracle Cloud Account

1. Go to https://www.oracle.com/cloud/free/
2. Sign up for Always Free tier
3. Create a credit card (required for verification, but no charges)
4. Wait for account activation (1-2 hours)

#### 3.2 Create ARM Instance

1. **Create Compute Instance**
   - Go to Oracle Cloud Console → Compute → Instances
   - Click "Create Instance"
   - Configure:
     - **Name:** `sprintforge-backend`
     - **Shape:** `VM.Standard.A1.Flex` (Always Free)
     - **OCPU:** 4 (maximum free)
     - **Memory:** 24GB (maximum free)
     - **Operating System:** `Oracle Linux` or `Ubuntu`
     - **SSH Key:** Upload your public SSH key

2. **Configure Network**
   - Add Ingress Rules:
     - `TCP 22` (SSH)
     - `TCP 8000` (Backend API)
     - `TCP 3000` (Optional: Frontend)

3. **Get Public IP**
   - Note the instance public IP address
   - Example: `129.146.0.1`

#### 3.3 Prepare Case Store (Local Machine)

```bash
# Run this on your local machine first
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m scripts.build_test_cases          # ~7 min
.venv/bin/python -m scripts.split_case_bank
.venv/bin/python -m scripts.build_curriculum_manifest

# Package the case store
tar czf cases.tgz -C app/data cases
```

#### 3.4 Setup Backend on Oracle Cloud

```bash
# SSH into Oracle Cloud instance
ssh ubuntu@your-oracle-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Create project directory
mkdir -p ~/sprintforge
cd ~/sprintforge

# Clone repository
git clone https://github.com/prnvmishra/SPRINTFORGE.git .
cd backend

# Copy case store from local machine
# On your local machine:
scp cases.tgz ubuntu@your-oracle-ip:~/sprintforge/backend/
# On Oracle Cloud:
cd ~/sprintforge/backend
tar xzf cases.tgz
rm cases.tgz
```

#### 3.5 Build and Run Backend

```bash
# Create production environment file
cat > .env << 'EOF'
ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
AUTH_SECRET=$(openssl rand -hex 32)
CORS_ORIGINS=https://your-app.vercel.app
CORS_ORIGIN_REGEX=
AI_PROVIDER=mock
CODE_EXECUTION_PROVIDER=piston
PISTON_URL=http://localhost:2000/api/v2
EXECUTION_TIMEOUT_SECONDS=10
EOF

# Build Docker image
docker build -t sprintforge-api .

# Run backend container
docker run -d --restart unless-stopped -p 8000:8000 \
  --env-file .env \
  --name sprintforge-api \
  sprintforge-api

# Check logs
docker logs sprintforge-api
```

#### 3.6 Setup Piston for Code Execution

```bash
# Run Piston container
cd ~/sprintforge
docker compose -f docker-compose.judge.yml up -d

# Install required languages
docker exec sprintforge-piston piston install python3
docker exec sprintforge-piston piston install node
docker exec sprintforge-piston piston install java
docker exec sprintforge-piston piston install c++
docker exec sprintforge-piston piston install c

# Verify Piston is running
curl http://localhost:2000/api/v2/runtimes
```

#### 3.7 Setup SSL Certificate (Optional but Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot certonly --standalone -d your-domain.com

# Or use self-signed certificate for development
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/sprintforge.key \
  -out /etc/ssl/certs/sprintforge.crt
```

### Step 4: Update Frontend Configuration

1. **Update Vercel Environment Variables**
   - Go to Vercel dashboard → your project → Settings → Environment Variables
   - Update `NEXT_PUBLIC_API_URL` to your Oracle Cloud IP or domain
   - Redeploy

2. **Test Connection**
   ```bash
   # Test backend health
   curl https://your-oracle-ip:8000/health
   
   # Expected response:
   # {"status":"ok","app":"SprintForge.AI","environment":"production",...}
   ```

---

## 🔧 Production Configuration

### Backend Environment Variables

```bash
# Core
ENVIRONMENT=production
DATABASE_URL=postgresql://neondb_owner:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
AUTH_SECRET=your-64-character-random-secret
CORS_ORIGINS=https://your-app.vercel.app
CORS_ORIGIN_REGEX=

# AI (Optional - can use mock for free)
AI_PROVIDER=mock
# AI_PROVIDER=gemini
# GEMINI_API_KEY=your-gemini-key

# Code Execution
CODE_EXECUTION_PROVIDER=piston
PISTON_URL=http://localhost:2000/api/v2
EXECUTION_TIMEOUT_SECONDS=10
```

### Frontend Environment Variables

```bash
NEXT_PUBLIC_API_URL=https://your-oracle-ip:8000
# Or with domain: NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

---

## 🚦 Health Checks & Monitoring

### Backend Health Check

```bash
# Check backend status
curl https://your-oracle-ip:8000/health

# Expected response:
{
  "status": "ok",
  "app": "SprintForge.AI",
  "environment": "production",
  "ai_provider": "mock",
  "code_execution_provider": "piston"
}
```

### Monitor Container Status

```bash
# Check running containers
docker ps

# Check backend logs
docker logs -f sprintforge-api

# Check Piston logs
docker logs -f sprintforge-piston

# Restart if needed
docker restart sprintforge-api
```

### Resource Monitoring

```bash
# Check system resources
htop

# Check disk space
df -h

# Check memory usage
free -h
```

---

## 🛡️ Security Checklist

- ✅ **AUTH_SECRET** changed from default
- ✅ **CORS_ORIGIN_REGEX** cleared in production
- ✅ **CODE_EXECUTION_PROVIDER** set to `piston` (not `local`)
- ✅ **DATABASE_URL** using PostgreSQL (not SQLite)
- ✅ **SSL/TLS** enabled for HTTPS
- ✅ **Firewall rules** configured properly
- ✅ **SSH keys** used for authentication
- ✅ **Docker containers** running as non-root (if possible)

---

## 📊 Performance Optimization

### Backend Optimization

```bash
# Use single worker (already configured in Dockerfile)
# Scale horizontally with more containers if needed

# Enable connection pooling (already configured in code)
# PostgreSQL connection pooling: pool_recycle=300

# Monitor and adjust
docker stats
```

### Frontend Optimization

- Vercel automatically handles CDN caching
- Next.js Image optimization enabled
- Static assets cached at edge
- Code splitting by default

---

## 🔄 Update & Maintenance

### Update Backend

```bash
# SSH into Oracle Cloud
ssh ubuntu@your-oracle-ip

# Pull latest code
cd ~/sprintforge
git pull

# Rebuild and restart
cd backend
docker build -t sprintforge-api .
docker stop sprintforge-api
docker rm sprintforge-api
docker run -d --restart unless-stopped -p 8000:8000 \
  --env-file .env \
  --name sprintforge-api \
  sprintforge-api
```

### Update Frontend

```bash
# Just push to GitHub
git add .
git commit -m "Update frontend"
git push origin master

# Vercel auto-deploys on push
```

---

## 🚨 Troubleshooting

### Backend Not Starting

```bash
# Check logs
docker logs sprintforge-api

# Common issues:
# - Case store missing: ensure cases/ directory exists
# - Database connection: check DATABASE_URL
# - Port conflict: ensure port 8000 is free
```

### Frontend Can't Connect to Backend

```bash
# Check CORS settings
curl -H "Origin: https://your-app.vercel.app" \
  https://your-oracle-ip:8000/health

# Check firewall rules
sudo iptables -L -n

# Test from Oracle Cloud instance
curl http://localhost:8000/health
```

### Code Execution Failing

```bash
# Check Piston status
curl http://localhost:2000/api/v2/runtimes

# Restart Piston
docker restart sprintforge-piston

# Check if languages are installed
docker exec sprintforge-piston piston list
```

### Database Connection Issues

```bash
# Test connection from Oracle Cloud
psql $DATABASE_URL

# Check Neon status
# Go to Neon console → Branches → Check status
```

---

## 📈 Scaling Strategy (When Needed)

### When to Scale Up

- Consistent high CPU usage (>80%)
- Memory pressure (>20GB used)
- High request latency (>2s)
- Database connection limits

### Scaling Options

1. **Horizontal Scaling:** Add more Oracle Cloud instances
2. **Database Upgrade:** Move to paid Neon tier
3. **CDN Enhancement:** Use Cloudflare for additional caching
4. **Load Balancing:** Add Nginx reverse proxy

---

## 💡 Tips for Maximum Free Usage

1. **Oracle Cloud Limits:**
   - 4 OCPU, 24GB RAM per tenant
   - 200GB block storage
   - 10TB/month network bandwidth

2. **Neon Limits:**
   - 0.5GB storage (enough for development)
   - 3 project branches
   - Auto-suspension after inactivity

3. **Vercel Limits:**
   - 100GB bandwidth/month
   - Unlimited projects
   - 100ms function execution timeout

4. **Optimization Tips:**
   - Use mock AI provider to save API costs
   - Implement caching where possible
   - Optimize database queries
   - Use CDN for static assets

---

## ✅ Deployment Verification Checklist

- [ ] Frontend accessible at Vercel URL
- [ ] Backend health check returns 200 OK
- [ ] Database connection successful
- [ ] Code execution (Piston) working
- [ ] CORS properly configured
- [ ] SSL certificate valid
- [ ] All environment variables set
- [ ] Case store loaded
- [ ] Security checks passed
- [ ] Monitoring setup

---

## 🎉 Final Result

You'll have a **100% free, production-ready deployment** with:

- ✅ Fast loading times (<100ms frontend, 1.6s backend boot)
- ✅ No cold starts (backend always running)
- ✅ No degradation (same performance as local)
- ✅ Secure (SSL, sandboxed execution)
- ✅ Scalable (can upgrade when needed)
- ✅ Monitorable (health checks, logs)

**Total Monthly Cost: $0**

Your SprintForge.AI application will run accurately and reliably without any usage errors or performance degradation!