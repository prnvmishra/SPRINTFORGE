#!/bin/bash

# SSL Certificate Setup for Oracle Cloud
# This script sets up SSL certificates using Let's Encrypt

set -e

echo "🔐 SSL Certificate Setup"
echo "========================"

# Check if domain is provided
if [ -z "$1" ]; then
    echo "Usage: ./setup-ssl.sh your-domain.com"
    echo "Example: ./setup-ssl.sh sprintforge.example.com"
    exit 1
fi

DOMAIN=$1

# Install Certbot
echo "📦 Installing Certbot..."
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
echo "🔑 Obtaining SSL certificate for $DOMAIN..."
sudo certbot certonly --standalone -d $DOMAIN --email your-email@example.com --agree-tos --non-interactive

# Setup certificate renewal
echo "⏰ Setting up auto-renewal..."
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Update Docker Compose to use SSL
echo "📝 Updating Docker Compose configuration..."
cat > docker-compose.ssl.yml << EOF
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    container_name: sprintforge-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - sprintforge-api
    networks:
      - sprintforge-network

  sprintforge-api:
    # Same configuration as docker-compose.prod.yml
    # Remove external ports since nginx will handle SSL
    expose:
      - "8000"
    networks:
      - sprintforge-network

networks:
  sprintforge-network:
    driver: bridge
EOF

echo "✅ SSL certificate setup complete!"
echo "📝 Certificate location: /etc/letsencrypt/live/$DOMAIN/"
echo "🔄 Auto-renewal: enabled via systemd timer"