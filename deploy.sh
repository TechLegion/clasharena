#!/bin/bash

# ClashArena Production Deployment Script
set -e

echo "🚀 Deploying ClashArena to Production..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please create a .env file with your production configuration."
    exit 1
fi

# Load environment variables
source .env

# Validate required environment variables
required_vars=("SECRET_KEY" "DB_PASSWORD" "PAYSTACK_SECRET_KEY" "FLUTTERWAVE_SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}❌ Required environment variable $var is not set!${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ Environment variables validated${NC}"

# Create SSL directory if it doesn't exist
mkdir -p ssl

# Check if SSL certificates exist
if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
    echo -e "${YELLOW}⚠️  SSL certificates not found in ssl/ directory${NC}"
    echo "Please add your SSL certificates:"
    echo "  - ssl/cert.pem (certificate file)"
    echo "  - ssl/key.pem (private key file)"
    echo ""
    echo "For development, you can generate self-signed certificates:"
    echo "  openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes"
    echo ""
    read -p "Continue without SSL certificates? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose -f docker-compose.prod.yml down || true

# Build and start services
echo -e "${YELLOW}🔨 Building and starting services...${NC}"
docker-compose -f docker-compose.prod.yml up --build -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 30

# Check service health
echo -e "${YELLOW}🏥 Checking service health...${NC}"

# Check backend health
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    echo "Backend logs:"
    docker-compose -f docker-compose.prod.yml logs backend
    exit 1
fi

# Check database connection
echo -e "${YELLOW}🗄️  Checking database connection...${NC}"
if docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U clasharena_user -d clasharena > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database is ready${NC}"
else
    echo -e "${RED}❌ Database connection failed${NC}"
    exit 1
fi

# Check Redis connection
echo -e "${YELLOW}📦 Checking Redis connection...${NC}"
if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is ready${NC}"
else
    echo -e "${RED}❌ Redis connection failed${NC}"
    exit 1
fi

# Run database migrations (if needed)
echo -e "${YELLOW}🔄 Running database migrations...${NC}"
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.core.database import engine
from shared.models import Base
Base.metadata.create_all(bind=engine)
print('Database tables created/updated')
"

# Create admin user if needed
echo -e "${YELLOW}👑 Creating admin user...${NC}"
docker-compose -f docker-compose.prod.yml exec backend python -c "
import sys
sys.path.append('/app')
from app.core.database import get_db
from shared.models import User
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
import os

db = next(get_db())
admin_email = os.getenv('ADMIN_EMAIL', 'admin@clasharena.com')
admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')

existing_admin = db.query(User).filter(User.email == admin_email).first()
if not existing_admin:
    admin_user = User(
        email=admin_email,
        username='admin',
        full_name='System Administrator',
        hashed_password=get_password_hash(admin_password),
        is_admin=True,
        is_active=True,
        is_verified=True
    )
    db.add(admin_user)
    db.commit()
    print(f'Admin user created: {admin_email}')
else:
    print(f'Admin user already exists: {admin_email}')
"

# Show service status
echo -e "${GREEN}📊 Service Status:${NC}"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo -e "${GREEN}🎉 ClashArena deployed successfully!${NC}"
echo ""
echo -e "${YELLOW}📋 Access URLs:${NC}"
echo "  - Backend API: http://localhost:8001"
echo "  - Health Check: http://localhost:8001/health"
echo "  - Celery Flower: http://localhost:5555"
echo "  - Database: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo -e "${YELLOW}🔧 Management Commands:${NC}"
echo "  - View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  - Stop services: docker-compose -f docker-compose.prod.yml down"
echo "  - Restart: docker-compose -f docker-compose.prod.yml restart"
echo ""
echo -e "${YELLOW}🔒 Security Notes:${NC}"
echo "  - Change default admin password immediately"
echo "  - Configure proper SSL certificates"
echo "  - Set up firewall rules"
echo "  - Enable database backups"
echo ""
echo -e "${GREEN}🚀 Your ClashArena gaming platform is ready!${NC}"
