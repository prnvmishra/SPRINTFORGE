#!/bin/bash

# SprintForge.AI - Monitoring Script
# This script checks the health and performance of deployed services

echo "🏥 SprintForge.AI - Health Monitor"
echo "=================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to check service health
check_service() {
    local name=$1
    local url=$2
    
    if curl -f -s "$url" > /dev/null; then
        echo -e "${GREEN}✅ $name: Healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ $name: Unhealthy${NC}"
        return 1
    fi
}

# Function to get response time
get_response_time() {
    local url=$1
    local time=$(curl -o /dev/null -s -w '%{time_total}' "$url")
    echo "${time}s"
}

# Check Backend
echo "📊 Backend Status"
BACKEND_URL="http://localhost:8000"
if check_service "Backend API" "$BACKEND_URL/health"; then
    RESPONSE_TIME=$(get_response_time "$BACKEND_URL/health")
    echo "   Response Time: $RESPONSE_TIME"
    
    # Get detailed health info
    HEALTH_INFO=$(curl -s "$BACKEND_URL/health")
    echo "   Details: $HEALTH_INFO"
else
    echo -e "${RED}   Checking logs...${NC}"
    docker logs --tail 20 sprintforge-api
fi

echo ""

# Check Piston
echo "📊 Piston Status"
PISTON_URL="http://localhost:2000"
if check_service "Piston" "$PISTON_URL/api/v2/runtimes"; then
    RESPONSE_TIME=$(get_response_time "$PISTON_URL/api/v2/runtimes")
    echo "   Response Time: $RESPONSE_TIME"
    
    # Check available runtimes
    RUNTIMES=$(curl -s "$PISTON_URL/api/v2/runtimes" | jq -r '.[].language' | sort -u)
    echo "   Available Languages: $RUNTIMES"
else
    echo -e "${RED}   Checking logs...${NC}"
    docker logs --tail 20 sprintforge-piston
fi

echo ""

# Check Docker Containers
echo "📊 Docker Container Status"
docker ps --filter "name=sprintforge" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""

# Check System Resources
echo "📊 System Resources"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%id.*/\1/" | awk '{print 100 - $1}')%"
echo "Memory Usage: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
echo "Disk Usage: $(df -h / | awk 'NR==2 {print $5}')"

echo ""

# Check Database Connection (if DATABASE_URL is set)
if [ -f .env ]; then
    echo "📊 Database Connection"
    source .env
    if PGPASSWORD=$DATABASE_URL psql -h "$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')" -U "$(echo $DATABASE_URL | sed -n 's/.*://\([^@]*\)@.*/\1/p')" -d "$(echo $DATABASE_URL | sed -n 's/.*/\([^?]*\).*/\1/p')" -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Database: Connected${NC}"
    else
        echo -e "${YELLOW}⚠️  Database: Connection check failed (might be normal if using external service)${NC}"
    fi
fi

echo ""
echo "📊 Recent Logs (Last 10 lines)"
echo "Backend:"
docker logs --tail 10 sprintforge-api 2>&1 | tail -5
echo "Piston:"
docker logs --tail 10 sprintforge-piston 2>&1 | tail -5

echo ""
echo "🔧 Quick Actions:"
echo "Restart services: docker-compose -f deploy/oracle-cloud/docker-compose.prod.yml restart"
echo "View logs: docker-compose -f deploy/oracle-cloud/docker-compose.prod.yml logs -f"
echo "Stop services: docker-compose -f deploy/oracle-cloud/docker-compose.prod.yml down"