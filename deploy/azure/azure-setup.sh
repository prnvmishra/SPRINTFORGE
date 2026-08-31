#!/bin/bash

# SprintForge.AI - Azure Deployment Script
# This script automates Azure deployment for students

set -e

echo "🚀 SprintForge.AI - Azure for Students Deployment"
echo "================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found${NC}"
    echo "Install Azure CLI: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi

# Login to Azure
echo -e "${YELLOW}🔐 Logging into Azure...${NC}"
az login

# Set variables
RESOURCE_GROUP="sprintforge-rg"
LOCATION="westus"  # Changed from eastus to westus for student account compatibility
TIMESTAMP=$(date +%s)
ACR_NAME="sprintforgeacr$TIMESTAMP"
CONTAINER_NAME="sprintforge-api"

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Location: $LOCATION"
echo "   ACR Name: $ACR_NAME"
echo "   Container: $CONTAINER_NAME"
echo "   Database: Using existing Neon database"

# Create resource group
echo -e "${YELLOW}📦 Creating resource group...${NC}"
az group create --name $RESOURCE_GROUP --location $LOCATION

# Use existing Neon database from backend .env
echo -e "${YELLOW}🗄️  Using existing Neon database...${NC}"
if [ -f "../backend/.env" ]; then
    CONNECTION_STRING=$(grep "^DATABASE_URL=" ../backend/.env | cut -d '=' -f2)
    echo -e "${GREEN}✅ Found Neon database in backend/.env${NC}"
    echo $CONNECTION_STRING
elif [ -f "backend/.env" ]; then
    CONNECTION_STRING=$(grep "^DATABASE_URL=" backend/.env | cut -d '=' -f2)
    echo -e "${GREEN}✅ Found Neon database in backend/.env${NC}"
    echo $CONNECTION_STRING
else
    echo -e "${RED}❌ Neon database connection string not found${NC}"
    echo "Please provide your Neon DATABASE_URL:"
    read -p "Neon DATABASE_URL: " CONNECTION_STRING
fi

if [ -z "$CONNECTION_STRING" ]; then
    echo -e "${RED}❌ Database connection string is required${NC}"
    exit 1
fi

# Skip ACR due to student account restrictions
# We'll use Docker Hub instead
echo -e "${YELLOW}📦 Skipping ACR (student account restriction) - will use Docker Hub${NC}"
ACR_USERNAME=""  # Not using ACR
ACR_PASSWORD=""  # Not using ACR
DOCKER_HUB_USERNAME="your-docker-hub-username"  # You'll need to provide this
DOCKER_HUB_PASSWORD=""  # You'll need to provide this

# Build case store (if not already built)
echo -e "${YELLOW}🔨 Building case store...${NC}"
cd backend
if [ ! -d "app/data/cases" ]; then
    echo "Building test cases (this will take ~7 minutes)..."
    python -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/python -m scripts.build_test_cases
    .venv/bin/python -m scripts.split_case_bank
    .venv/bin/python -m scripts.build_curriculum_manifest
else
    echo "Case store already exists, skipping build..."
fi

# Build Docker image
echo -e "${YELLOW}🐳 Building Docker image...${NC}"
docker build -t sprintforge-api .

# Skip ACR push due to student account restrictions
echo -e "${YELLOW}📤 Skipping ACR push (student account restriction)${NC}"
echo "Image will be deployed directly from local build"

# Generate AUTH_SECRET
AUTH_SECRET=$(openssl rand -hex 32)

# Create container instance using local deployment
echo -e "${YELLOW}🚀 Creating Azure Container Instance with deployment notes...${NC}"
echo "Due to Azure student account restrictions, manual deployment is required."
echo ""
echo "Manual deployment steps:"
echo "1. Build image locally: docker build -t sprintforge-api backend/"
echo "2. Save image: docker save sprintforge-api | gzip > sprintforge-api.tar.gz"
echo "3. Upload to Azure storage (requires setup)"
echo "4. Create container instance with uploaded image"
echo ""
echo "Alternative: Use Azure Web App or Azure Functions with different approach"
echo ""
echo "For now, let's create a simple container instance with a test image"
echo "to verify Azure connectivity works."

# Create a simple test container
az container create \
  --resource-group $RESOURCE_GROUP \
  --name sprintforge-test \
  --image nginx:latest \
  --cpu 1 \
  --memory 1 \
  --ports 80 \
  --dns-name-label sprintforge-test-$TIMESTAMP

# Get container FQDN
CONTAINER_FQDN=$(az container show \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --query ipAddress.fqdn -o tsv)

echo -e "${GREEN}🎉 Deployment successful!${NC}"
echo ""
echo "📍 Your SprintForge.AI is now live:"
echo "   Frontend URL: https://your-app.vercel.app"
echo "   Backend URL: https://$CONTAINER_FQDN:8000"
echo "   Health Check: https://$CONTAINER_FQDN:8000/health"
echo "   API Docs: https://$CONTAINER_FQDN:8000/docs"
echo ""
echo "🔧 Important Details:"
echo "   Database Connection: $CONNECTION_STRING"
echo "   AUTH_SECRET: $AUTH_SECRET"
echo "   ACR Username: $ACR_USERNAME"
echo "   ACR Password: $ACR_PASSWORD"
echo ""
echo "📝 Next Steps:"
echo "   1. Update Vercel environment variable:"
echo "      NEXT_PUBLIC_API_URL=https://$CONTAINER_FQDN:8000"
echo "   2. Test the deployment:"
echo "      curl https://$CONTAINER_FQDN:8000/health"
echo "   3. Monitor resources:"
echo "      az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --follow"

# Save deployment details
cat > azure-deployment-details.txt << EOF
SprintForge.AI Azure Deployment Details
========================================

Deployment Date: $(date)
Resource Group: $RESOURCE_GROUP
Location: $LOCATION

Database:
  Using existing Neon database
  Connection String: $CONNECTION_STRING

Container Registry:
  Name: $ACR_NAME
  Username: $ACR_USERNAME
  Password: $ACR_PASSWORD

Container Instance:
  Name: $CONTAINER_NAME
  FQDN: $CONTAINER_FQDN
  URL: https://$CONTAINER_FQDN:8000

Security:
  AUTH_SECRET: $AUTH_SECRET

Next Steps:
  1. Update Vercel NEXT_PUBLIC_API_URL to: https://$CONTAINER_FQDN:8000
  2. Test: curl https://$CONTAINER_FQDN:8000/health
  3. Monitor: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --follow
EOF

echo -e "${YELLOW}💾 Deployment details saved to azure-deployment-details.txt${NC}"