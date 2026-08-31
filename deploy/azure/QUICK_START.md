# 🚀 Azure Quick Start - SprintForge.AI

## ⚡ 15-Minute Azure Deployment

### Prerequisites
- Azure for Students account activated
- Azure CLI installed
- Docker installed locally

### Step 1: Install Azure CLI (2 minutes)

**Mac:**
```bash
brew install azure-cli
```

**Windows:**
```bash
# Download from: https://docs.microsoft.com/cli/azure/install-azure-cli
```

**Linux:**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

### Step 2: Run Automated Setup (10 minutes)

```bash
# Navigate to project root
cd /Users/pranavmishra/Downloads/hcl_round2

# Run the Azure setup script
./deploy/azure/azure-setup.sh
```

**The script will:**
- ✅ Create Azure resource group
- ✅ Setup PostgreSQL database
- ✅ Create Azure Container Registry
- ✅ Build and push Docker image
- ✅ Deploy Azure Container Instance
- ✅ Configure all environment variables

### Step 3: Update Vercel (1 minute)

1. Get your Azure backend URL from script output
2. Go to Vercel → Settings → Environment Variables
3. Update `NEXT_PUBLIC_API_URL` to your Azure URL
4. Redeploy Vercel

### Step 4: Test (2 minutes)

```bash
# Test backend health
curl https://your-azure-container-url:8000/health

# Test frontend
# Open https://your-app.vercel.app
```

---

## 🎯 Manual Setup (If Script Fails)

### Create Resources Manually

```bash
# Login to Azure
az login

# Create resource group
az group create --name sprintforge-rg --location eastus

# Create PostgreSQL
az postgres server create \
  --resource-group sprintforge-rg \
  --name sprintforge-db-$(date +%s) \
  --location eastus \
  --admin-user sprintforge \
  --admin-password YourPassword123! \
  --sku-name B_Gen5_1

# Create database
az postgres db create \
  --resource-group sprintforge-rg \
  --server-name sprintforge-db-$(date +%s) \
  --name sprintforge

# Create ACR
az acr create \
  --resource-group sprintforge-rg \
  --name sprintforgeacr$(date +%s) \
  --sku Basic \
  --location eastus
```

### Build and Deploy

```bash
# Build case store
cd backend
python -m scripts.build_test_cases
python -m scripts.split_case_bank
python -m scripts.build_curriculum_manifest

# Build Docker image
docker build -t sprintforge-api .

# Push to ACR
az acr login --name your-acr-name
docker tag sprintforge-api your-acr-name.azurecr.io/sprintforge-api:latest
docker push your-acr-name.azurecr.io/sprintforge-api:latest

# Deploy container
az container create \
  --resource-group sprintforge-rg \
  --name sprintforge-api \
  --image your-acr-name.azurecr.io/sprintforge-api:latest \
  --cpu 4 \
  --memory 8 \
  --ports 8000
```

---

## 📊 Resource Limits (Free Tier)

| Resource | Free Tier Limit | SprintForge Needs |
|----------|----------------|-------------------|
| Container CPU | 4 cores | 4 cores ✅ |
| Container Memory | 8GB | 8GB ✅ |
| PostgreSQL | B_Gen5_1 (1 vCore, 2GB) | Sufficient ✅ |
| Storage | 5GB | Sufficient ✅ |
| Bandwidth | 100GB/month | Sufficient ✅ |

---

## 🔧 Environment Variables

```bash
DATABASE_URL=postgresql://sprintforge:password@server.postgres.database.azure.com:5432/sprintforge?sslmode=require
AUTH_SECRET=your-64-character-secret
ENVIRONMENT=production
CORS_ORIGINS=https://your-app.vercel.app
AI_PROVIDER=mock
CODE_EXECUTION_PROVIDER=piston
PISTON_URL=https://emkc.org/api/v2/piston
```

---

## 🛠️ Useful Commands

```bash
# Check container status
az container show --resource-group sprintforge-rg --name sprintforge-api

# View logs
az container logs --resource-group sprintforge-rg --name sprintforge-api --follow

# Restart container
az container restart --resource-group sprintforge-rg --name sprintforge-api

# Monitor costs
az consumption usage list --resource-group sprintforge-rg

# Delete everything (cleanup)
az group delete --name sprintforge-rg --yes
```

---

## 🚨 Troubleshooting

### Script fails at Azure login
```bash
# Manually login
az login
# Then run script again
```

### Docker build fails
```bash
# Ensure Docker is running
docker ps

# Build manually
cd backend
docker build -t sprintforge-api .
```

### Container not starting
```bash
# Check logs
az container logs --resource-group sprintforge-rg --name sprintforge-api

# Common issues:
# - DATABASE_URL incorrect
# - Case store missing
# - Resource limits exceeded
```

### Database connection issues
```bash
# Check firewall rules
az postgres server firewall-rule list \
  --resource-group sprintforge-rg \
  --server-name your-db-server

# Test connection
psql $DATABASE_URL
```

---

## 💰 Cost Monitoring

```bash
# Set budget alert (at $80)
az consumption budget create \
  --resource-group sprintforge-rg \
  --name sprintforge-budget \
  --amount 80 \
  --time-grain Monthly

# Check current spend
az consumption usage list \
  --resource-group sprintforge-rg \
  --start-date $(date -d '1 month ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d)
```

---

## ✅ Hackathon Checklist

- [ ] Azure CLI installed
- [ ] Azure for Students activated
- [ ] Script executed successfully
- [ ] Backend health check passing
- [ ] Frontend connected to Azure backend
- [ ] End-to-end testing completed
- [ ] Cost alerts configured
- [ ] Backup plan ready

---

## 🎉 Expected Result

**Deployment URL:** `https://sprintforge-api-xxx.eastus.azurecontainer.io:8000`

**Health Check:** `https://sprintforge-api-xxx.eastus.azurecontainer.io:8000/health`

**Frontend:** `https://your-app.vercel.app` (connected to Azure backend)

**Monthly Cost:** $0 (within $100 student credit)

**Reliability:** 99.9% uptime (no cold starts)

Perfect for hackathon demos! 🏆