#!/bin/bash

# SprintForge.AI - Oracle Cloud Deployment Script
# This script automates the deployment process on Oracle Cloud ARM instance

set -e

echo "🚀 SprintForge.AI - Oracle Cloud Deployment"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}Please don't run as root${NC}"
   exit 1
fi

# Update system
echo -e "${YELLOW}📦 Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}🐳 Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo -e "${GREEN}✅ Docker installed${NC}"
else
    echo -e "${GREEN}✅ Docker already installed${NC}"
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}📋 Installing Docker Compose...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✅ Docker Compose already installed${NC}"
fi

# Create project directory
PROJECT_DIR="$HOME/sprintforge"
echo -e "${YELLOW}📁 Creating project directory: $PROJECT_DIR${NC}"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Clone repository if not present
if [ ! -d "SPRINTFORGE" ]; then
    echo -e "${YELLOW}📥 Cloning repository...${NC}"
    git clone https://github.com/prnvmishra/SPRINTFORGE.git
    cd SPRINTFORGE
else
    echo -e "${GREEN}✅ Repository already exists, pulling latest...${NC}"
    cd SPRINTFORGE
    git pull
fi

# Check for case store
if [ ! -d "backend/app/data/cases" ]; then
    echo -e "${RED}❌ Case store not found!${NC}"
    echo "Please run the following on your local machine:"
    echo "  cd backend"
    echo "  python -m scripts.build_test_cases"
    echo "  python -m scripts.split_case_bank"
    echo "  python -m scripts.build_curriculum_manifest"
    echo "  tar czf cases.tgz -C app/data cases"
    echo "  scp cases.tgz ubuntu@$(hostname -I | awk '{print $1}'):~/sprintforge/SPRINTFORGE/backend/"
    echo "  ssh ubuntu@$(hostname -I | awk '{print $1}')"
    echo "  cd ~/sprintforge/SPRINTFORGE/backend"
    echo "  tar xzf cases.tgz"
    echo "  rm cases.tgz"
    exit 1
fi

# Setup environment file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚙️  Creating environment file...${NC}"
    cp deploy/oracle-cloud/.env.example .env
    echo -e "${RED}⚠️  Please edit .env with your actual values:${NC}"
    echo "   - DATABASE_URL (from Neon)"
    echo "   - AUTH_SECRET (generate with: openssl rand -hex 32)"
    echo "   - CORS_ORIGINS (your Vercel URL)"
    echo "   - AI_PROVIDER (mock or gemini)"
    echo ""
    read -p "Press Enter after editing .env file..."
fi

# Build and start services
echo -e "${YELLOW}🔨 Building Docker images...${NC}"
cd deploy/oracle-cloud
docker-compose -f docker-compose.prod.yml build

echo -e "${YELLOW}🚀 Starting services...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 30

# Install Piston languages
echo -e "${YELLOW}📦 Installing Piston languages...${NC}"
docker exec sprintforge-piston piston install python3
docker exec sprintforge-piston piston install node
docker exec sprintforge-piston piston install java
docker exec sprintforge-piston piston install c++
docker exec sprintforge-piston piston install c

# Check service status
echo -e "${GREEN}✅ Checking service status...${NC}"
docker-compose -f docker-compose.prod.yml ps

# Health check
echo -e "${YELLOW}🏥 Running health check...${NC}"
if curl -f http://localhost:8000/health; then
    echo -e "${GREEN}✅ Backend is healthy!${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    docker-compose -f docker-compose.prod.yml logs sprintforge-api
    exit 1
fi

if curl -f http://localhost:2000/api/v2/runtimes; then
    echo -e "${GREEN}✅ Piston is healthy!${NC}"
else
    echo -e "${RED}❌ Piston health check failed${NC}"
    docker-compose -f docker-compose.prod.yml logs piston
    exit 1
fi

echo -e "${GREEN}🎉 Deployment successful!${NC}"
echo ""
echo "📍 Your services are running:"
echo "   Backend API: http://$(hostname -I | awk '{print $1}'):8000"
echo "   Health Check: http://$(hostname -I | awk '{print $1}'):8000/health"
echo "   Piston: http://$(hostname -I | awk '{print $1}'):2000"
echo ""
echo "📝 Next steps:"
echo "   1. Update your Vercel frontend with this backend URL"
echo "   2. Configure your domain name (optional)"
echo "   3. Setup SSL certificate (recommended)"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: docker-compose -f deploy/oracle-cloud/docker-compose.prod.yml logs -f"
echo "   Stop services: docker-compose -f deploy/oracle-cloud/docker-compose.prod.yml down"
echo "   Restart services: docker-compose -f deploy/oracle-cloud/docker-compose.prod.yml restart"