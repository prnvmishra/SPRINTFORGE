# 🚀 SprintForge.AI - Azure for Students Deployment Guide

## 🎯 Why Azure for Students?

- ✅ **$100 free credit annually** (renewed)
- ✅ **No credit card required** for students
- ✅ **Full Docker support** for complex backends
- ✅ **No cold starts** - perfect for hackathon demos
- ✅ **Production-grade reliability**
- ✅ **Integrated PostgreSQL database**

---

## 📋 Prerequisites

- GitHub Student Developer Pack activated
- Azure for Students account created
- Docker installed locally
- SprintForge code ready to deploy

---

## 🚀 Step-by-Step Azure Deployment

### Step 1: Activate Azure for Students (2 minutes)

1. **Go to:** https://education.github.com/pack
2. **Find:** "Azure for Students"
3. **Click:** "Get Started"
4. **Verify:** Student status with university email
5. **Receive:** $100 Azure credit

### Step 2: Create Azure Resource Group (1 minute)

```bash
# Install Azure CLI if not present
brew install azure-cli  # Mac
# or visit: https://docs.microsoft.com/cli/azure/install-azure-cli

# Login to Azure
az login

# Create resource group
az group create \
  --name sprintforge-rg \
  --location eastus
```

### Step 3: Create Azure PostgreSQL Database (5 minutes)

```bash
# Create PostgreSQL server
az postgres server create \
  --resource-group sprintforge-rg \
  --name sprintforge-db-$(date +%s) \
  --location eastus \
  --admin-user sprintforge \
  --admin-password YourStrongPassword123! \
  --sku-name B_Gen5_1 \
  --version 13

# Create database
az postgres db create \
  --resource-group sprintforge-rg \
  --server-name sprintforge-db-$(date +%s) \
  --name sprintforge

# Configure firewall rule (allow Azure services)
az postgres server firewall-rule create \
  --resource-group sprintforge-rg \
  --server-name sprintforge-db-$(date +%s) \
  --name allow-azure-services \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# Get connection string
az postgres server show-connection-string \
  --resource-group sprintforge-rg \
  --name sprintforge-db-$(date +%s) \
  --admin-name sprintforge \
  --admin-password YourStrongPassword123!
```

**Save the connection string - you'll need it later:**
```
postgresql://sprintforge:YourStrongPassword123!@sprintforge-db-xxx.postgres.database.azure.com:5432/sprintforge?sslmode=require
```

### Step 4: Build Docker Image Locally (10 minutes)

```bash
# On your local machine
cd backend

# Build case store first
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m scripts.build_test_cases
.venv/bin/python -m scripts.split_case_bank
.venv/bin/python -m scripts.build_curriculum_manifest

# Build Docker image
docker build -t sprintforge-api .

# Test locally
docker run -p 8000:8000 \
  -e DATABASE_URL="your-azure-connection-string" \
  -e AUTH_SECRET="test-secret" \
  -e ENVIRONMENT=development \
  sprintforge-api
```

### Step 5: Push to Azure Container Registry (5 minutes)

```bash
# Create Azure Container Registry
az acr create \
  --resource-group sprintforge-rg \
  --name sprintforgeacr$(date +%s) \
  --sku Basic \
  --location eastus

# Login to ACR
az acr login --name sprintforgeacr$(date +%s)

# Tag and push image
ACR_NAME=sprintforgeacr$(date +%s)
az acr update --name $ACR_NAME --admin-enabled true
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

docker tag sprintforge-api $ACR_NAME.azurecr.io/sprintforge-api:latest
docker push $ACR_NAME.azurecr.io/sprintforge-api:latest
```

### Step 6: Create Azure Container Instance (5 minutes)

```bash
# Create container instance
az container create \
  --resource-group sprintforge-rg \
  --name sprintforge-api \
  --image $ACR_NAME.azurecr.io/sprintforge-api:latest \
  --registry-login-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_NAME \
  --registry-password $ACR_PASSWORD \
  --cpu 4 \
  --memory 8 \
  --ports 8000 \
  --environment-variables \
    DATABASE_URL="your-azure-connection-string" \
    AUTH_SECRET="your-64-character-secret" \
    ENVIRONMENT=production \
    CORS_ORIGINS="https://your-app.vercel.app" \
    AI_PROVIDER=mock \
    CODE_EXECUTION_PROVIDER=local \
    PISTON_URL=http://localhost:2000/api/v2 \
  --dns-name-label sprintforge-api-$(date +%s)
```

### Step 7: Setup Piston for Code Execution (Optional)

**Option A: Use local execution (not recommended for production)**
```bash
# Keep CODE_EXECUTION_PROVIDER=local
# This runs code in the same container (development only)
```

**Option B: Use public Piston (recommended for hackathon)**
```bash
# Set CODE_EXECUTION_PROVIDER=piston
# PISTON_URL=https://emkc.org/api/v2/piston
```

### Step 8: Verify Deployment (2 minutes)

```bash
# Get container logs
az container logs --resource-group sprintforge-rg --name sprintforge-api

# Test health endpoint
CONTAINER_FQDN=$(az container show \
  --resource-group sprintforge-rg \
  --name sprintforge-api \
  --query ipAddress.fqdn -o tsv)

curl https://$CONTAINER_FQDN:8000/health

# Expected response:
# {"status":"ok","app":"SprintForge.AI","environment":"production",...}
```

### Step 9: Update Vercel Frontend (1 minute)

1. **Go to Vercel Dashboard** → Settings → Environment Variables
2. **Update `NEXT_PUBLIC_API_URL`:**
   ```bash
   NEXT_PUBLIC_API_URL=https://your-container-fqdn.azurewebsites.net:8000
   ```
3. **Redeploy** Vercel project

---

## 🔧 Azure-Specific Configuration

### Environment Variables for Azure

```bash
# Core
ENVIRONMENT=production
DATABASE_URL=postgresql://sprintforge:password@server.postgres.database.azure.com:5432/sprintforge?sslmode=require
AUTH_SECRET=your-64-character-random-secret
CORS_ORIGINS=https://your-app.vercel.app

# AI (use mock for free tier)
AI_PROVIDER=mock

# Code Execution
CODE_EXECUTION_PROVIDER=piston
PISTON_URL=https://emkc.org/api/v2/piston
EXECUTION_TIMEOUT_SECONDS=10
```

### Azure Resource Limits (Free Tier)

- **Container Instance:** 4 CPU, 8GB RAM
- **PostgreSQL:** B_Gen5_1 (1 vCore, 2GB RAM)
- **Storage:** 5GB included
- **Bandwidth:** 100GB/month

---

## 📊 Monitoring & Management

### Check Container Status

```bash
# Check container status
az container show --resource-group sprintforge-rg --name sprintforge-api

# View logs
az container logs --resource-group sprintforge-rg --name sprintforge-api --follow

# Restart container
az container restart --resource-group sprintforge-rg --name sprintforge-api
```

### Monitor Resources

```bash
# View container metrics
az monitor metrics list \
  --resource /subscriptions/{subscription-id}/resourceGroups/sprintforge-rg/providers/Microsoft.ContainerInstance/containerGroups/sprintforge-api \
  --metric "CPU Usage,Memory Usage"
```

### Scale Resources (if needed)

```bash
# Update container resources
az container update \
  --resource-group sprintforge-rg \
  --name sprintforge-api \
  --cpu 2 \
  --memory 4
```

---

## 🛡️ Security Configuration

### Configure PostgreSQL Firewall

```bash
# Add your IP for development
az postgres server firewall-rule create \
  --resource-group sprintforge-rg \
  --server-name sprintforge-db-xxx \
  --name allow-dev-ip \
  --start-ip-address YOUR_IP \
  --end-ip-address YOUR_IP
```

### Set Up SSL/TLS

Azure Container Instances automatically use HTTPS with Azure-managed certificates.

---

## 🔄 Updates & Maintenance

### Update Application

```bash
# Build new image locally
cd backend
docker build -t sprintforge-api .

# Push to ACR
docker tag sprintforge-api $ACR_NAME.azurecr.io/sprintforge-api:latest
docker push $ACR_NAME.azurecr.io/sprintforge-api:latest

# Restart Azure container
az container restart --resource-group sprintforge-rg --name sprintforge-api
```

### Database Maintenance

```bash
# Backup database
az postgres db create \
  --resource-group sprintforge-rg \
  --server-name sprintforge-db-xxx \
  --name sprintforge-backup-$(date +%Y%m%d)

# Monitor database performance
az postgres server list \
  --resource-group sprintforge-rg
```

---

## 🚨 Troubleshooting

### Container Not Starting

```bash
# Check logs
az container logs --resource-group sprintforge-rg --name sprintforge-api

# Common issues:
# - DATABASE_URL incorrect
# - AUTH_SECRET missing
# - Case store not loaded
```

### Database Connection Issues

```bash
# Test connection from local machine
psql $DATABASE_URL

# Check firewall rules
az postgres server firewall-rule list \
  --resource-group sprintforge-rg \
  --server-name sprintforge-db-xxx
```

### Performance Issues

```bash
# Check resource usage
az container show --resource-group sprintforge-rg --name sprintforge-api

# Scale up if needed
az container update \
  --resource-group sprintforge-rg \
  --name sprintforge-api \
  --cpu 4 \
  --memory 8
```

---

## 💰 Cost Management

### Monitor Costs

```bash
# View current costs
az consumption usage list \
  --resource-group sprintforge-rg \
  --start-date 2026-08-01 \
  --end-date 2026-08-31

# Set up budget alerts
az consumption budget create \
  --resource-group sprintforge-rg \
  --name sprintforge-budget \
  --amount 80 \
  --time-grain Monthly
```

### Stay Within Free Tier

- **Container Instance:** Monitor CPU/memory usage
- **PostgreSQL:** Keep database size under 5GB
- **Bandwidth:** Stay under 100GB/month

---

## 🎯 Hackathon Tips

### Pre-Demo Checklist

- [ ] All services running and healthy
- [ ] Database connection verified
- [ ] Frontend connected to backend
- [ ] Code execution working
- [ ] SSL/TLS configured
- [ ] Cost alerts set up

### Demo Preparation

```bash
# Wake up services 10 minutes before demo
az container restart --resource-group sprintforge-rg --name sprintforge-api

# Test all endpoints
curl https://your-container-fqdn.azurewebsites.net:8000/health
curl https://your-app.vercel.app

# Have backup plan ready
# - Local deployment script
# - Alternative DNS ready
```

---

## 📞 Support & Resources

- **Azure Documentation:** https://docs.microsoft.com/azure/
- **Azure CLI:** https://docs.microsoft.com/cli/azure/
- **GitHub Student Pack:** https://education.github.com/pack
- **Azure for Students:** https://azure.microsoft.com/free/students/

---

## ✅ Deployment Summary

With Azure for Students, you get:

- ✅ **Production-grade deployment** 
- ✅ **No cold starts** for demos
- ✅ **Full Docker support**
- ✅ **Integrated PostgreSQL**
- ✅ **$100 free credit** (plenty for hackathon)
- ✅ **No credit card required**
- ✅ **Reliable Microsoft infrastructure**

**Total deployment time: ~30 minutes**
**Monthly cost: $0 (within free tier)**

Your SprintForge.AI will run reliably throughout your hackathon without any sleep issues or resource limits! 🏆