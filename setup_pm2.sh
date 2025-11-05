#!/bin/bash

# ThePred PM2 Setup Script
# This script sets up the project with PM2 for application management

set -e  # Exit on error

echo "===================================="
echo "ThePred PM2 Setup"
echo "===================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

echo "1. Checking dependencies..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Node.js not found. Installing...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
else
    echo -e "${GREEN}✓ Node.js installed${NC}"
fi

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo -e "${YELLOW}PM2 not found. Installing...${NC}"
    npm install -g pm2
else
    echo -e "${GREEN}✓ PM2 installed${NC}"
fi

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 not found. Please install Python 3.11+${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Python3 installed${NC}"
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker not found. Installing...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    apt install -y docker-compose
else
    echo -e "${GREEN}✓ Docker installed${NC}"
fi

echo ""
echo "2. Setting up Python virtual environments..."

# Get project directory
PROJECT_DIR=$(pwd)

# Create venvs for each app
for app in backend webapp admin bot landing; do
    echo -e "${YELLOW}Setting up $app...${NC}"
    cd "$PROJECT_DIR/$app"

    # Remove old venv if exists
    [ -d "venv" ] && rm -rf venv

    # Create new venv
    python3 -m venv venv

    # Install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate

    echo -e "${GREEN}✓ $app setup complete${NC}"
done

cd "$PROJECT_DIR"

echo ""
echo "3. Starting infrastructure (Docker)..."

# Stop any running containers
docker-compose down 2>/dev/null || true

# Start infrastructure only
docker-compose -f docker-compose.infrastructure.yml up -d

echo -e "${GREEN}✓ Infrastructure started${NC}"

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}Waiting for PostgreSQL...${NC}"
sleep 5

echo ""
echo "4. Running database migrations..."

cd "$PROJECT_DIR/backend"
source venv/bin/activate
POSTGRES_HOST=localhost alembic upgrade head
deactivate
cd "$PROJECT_DIR"

echo -e "${GREEN}✓ Database migrations complete${NC}"

echo ""
echo "5. Uploading mission icons to S3..."

python3 upload_mission_icons_to_s3.py

echo -e "${GREEN}✓ Icons uploaded${NC}"

echo ""
echo "6. Starting applications with PM2..."

# Stop any existing PM2 processes
pm2 delete all 2>/dev/null || true

# Start applications
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 startup script
pm2 startup systemd -u root --hp /root

echo -e "${GREEN}✓ Applications started${NC}"

echo ""
echo "===================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "===================================="
echo ""
echo "Application Status:"
pm2 status
echo ""
echo "Useful Commands:"
echo "  pm2 status       - Check application status"
echo "  pm2 logs         - View logs"
echo "  pm2 monit        - Monitor resources"
echo "  pm2 restart all  - Restart all apps"
echo ""
echo "Infrastructure:"
echo "  PostgreSQL: localhost:5432"
echo "  Redis: localhost:6379"
echo "  MinIO: localhost:9000"
echo "  MinIO Console: localhost:9001"
echo ""
echo "Applications:"
echo "  Backend API: http://localhost:8000"
echo "  Webapp: http://localhost:8001"
echo "  Admin: http://localhost:8002"
echo "  Landing: http://localhost:8003"
echo "  Bot: Running in background"
echo ""
