# ClashArena Automation Guide

This guide covers the comprehensive automation framework implemented for ClashArena, including CI/CD, testing, monitoring, deployment, and infrastructure management.

## 🚀 Overview

The automation framework includes:

- **CI/CD Pipeline** - GitHub Actions for automated testing and deployment
- **Automated Testing** - Unit, integration, security, and performance tests
- **Monitoring & Alerting** - Prometheus, Grafana, and comprehensive health checks
- **Database Automation** - Automated backups, migrations, and maintenance
- **Security Automation** - Dependency scanning and vulnerability checks
- **Infrastructure as Code** - Terraform for cloud resource management
- **Deployment Automation** - Blue-green deployment with rollback capabilities

## 📋 Prerequisites

### Required Tools
- Docker & Docker Compose
- Python 3.12+
- Node.js 18+
- Git
- AWS CLI (for cloud deployment)
- Terraform (for infrastructure)

### Required Accounts
- GitHub (for CI/CD)
- AWS Account (for cloud infrastructure)
- Docker Hub or ECR (for container registry)

## 🔧 Setup Instructions

### 1. Environment Configuration

Create a `.env` file with your configuration:

```bash
# Copy the example file
cp env.example .env

# Edit with your values
nano .env
```

Required environment variables:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/clasharena
DB_PASSWORD=your-secure-password

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key

# Payment Gateways
PAYSTACK_SECRET_KEY=your-paystack-secret
FLUTTERWAVE_SECRET_KEY=your-flutterwave-secret

# Monitoring
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=alerts@clasharena.com
TO_EMAILS=admin@clasharena.com

# Deployment
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
NOTIFICATION_EMAIL=admin@clasharena.com
```

### 2. GitHub Actions Setup

1. **Create GitHub Secrets:**
   - Go to your repository settings
   - Navigate to Secrets and Variables > Actions
   - Add the following secrets:
     - `AWS_ACCESS_KEY_ID`
     - `AWS_SECRET_ACCESS_KEY`
     - `DOCKER_USERNAME`
     - `DOCKER_PASSWORD`
     - `WEBHOOK_URL`

2. **Enable GitHub Actions:**
   - The CI/CD pipeline will automatically run on push and pull requests
   - Check the Actions tab in your GitHub repository

### 3. Local Development Setup

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

cd ../frontend
npm install

# Start development environment
docker-compose up -d

# Run tests
python scripts/automated_testing.py
```

## 🧪 Testing Framework

### Running Tests

```bash
# Run all tests
python scripts/automated_testing.py

# Run specific test suites
cd backend && pytest                    # Backend tests
cd frontend && npm test                 # Frontend tests
python scripts/test_api.py              # Integration tests
python scripts/health_check.py          # Health checks
```

### Test Coverage

- **Backend Tests**: Unit tests for API endpoints, business logic
- **Frontend Tests**: Component tests, integration tests
- **Integration Tests**: End-to-end API testing
- **Security Tests**: Vulnerability scanning, dependency checks
- **Performance Tests**: Load testing, response time monitoring
- **Accessibility Tests**: WCAG compliance testing

## 📊 Monitoring & Alerting

### Monitoring Stack

The monitoring stack includes:

- **Prometheus**: Metrics collection
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notifications
- **Jaeger**: Distributed tracing
- **ELK Stack**: Log aggregation and analysis
- **Uptime Kuma**: Uptime monitoring

### Starting Monitoring

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access services
# Grafana: http://localhost:3001 (admin/admin123)
# Prometheus: http://localhost:9090
# Jaeger: http://localhost:16686
# Kibana: http://localhost:5601
# Uptime Kuma: http://localhost:3002
```

### Health Monitoring

```bash
# Run health checks
python scripts/health_monitor.py

# Run once
python scripts/health_monitor.py once

# Continuous monitoring
python scripts/health_monitor.py
```

## 🗄️ Database Automation

### Automated Backups

```bash
# Create backup
python scripts/automated_backup.py

# Restore backup
python scripts/automated_backup.py restore backup_file.sql.gz

# Schedule backups (crontab)
0 2 * * * /path/to/python /path/to/scripts/automated_backup.py
```

### Database Migrations

```bash
# Run migrations
docker-compose exec backend python -c "
from app.core.database import engine
from shared.models import Base
Base.metadata.create_all(bind=engine)
"
```

## 🔒 Security Automation

### Security Scanning

```bash
# Run security scans
python -m bandit -r backend/
npm audit
trivy image clasharena-backend:latest
```

### Dependency Updates

The system automatically creates pull requests for dependency updates:
- Python dependencies (weekly)
- Node.js dependencies (weekly)
- Docker base images (monthly)

## 🚀 Deployment Automation

### Local Deployment

```bash
# Development deployment
docker-compose up -d

# Production deployment
./scripts/auto_deploy.sh

# Staging deployment
ENVIRONMENT=staging ./scripts/auto_deploy.sh
```

### Cloud Deployment

```bash
# Deploy infrastructure
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply

# Deploy application
./scripts/deploy_infrastructure.sh
```

### Deployment Options

- **Blue-Green Deployment**: Zero-downtime deployments
- **Rollback Capability**: Automatic rollback on failure
- **Health Checks**: Automated health verification
- **Backup & Restore**: Automatic backup before deployment

## ☁️ Infrastructure as Code

### Terraform Configuration

The infrastructure is defined in the `terraform/` directory:

- **main.tf**: Main infrastructure resources
- **variables.tf**: Input variables
- **outputs.tf**: Output values
- **terraform.tfvars.example**: Example configuration

### Deploying Infrastructure

```bash
# Initialize Terraform
cd terraform
terraform init

# Plan deployment
terraform plan -var-file="terraform.tfvars"

# Apply changes
terraform apply -var-file="terraform.tfvars"
```

### Infrastructure Components

- **VPC**: Virtual Private Cloud with public/private subnets
- **ECS**: Container orchestration with Fargate
- **RDS**: Managed PostgreSQL database
- **ElastiCache**: Redis cache cluster
- **ALB**: Application Load Balancer
- **CloudWatch**: Logging and monitoring
- **S3**: Backup storage

## 📈 Performance Optimization

### Auto Scaling

The infrastructure includes auto-scaling capabilities:
- **ECS Auto Scaling**: Based on CPU and memory utilization
- **Database Scaling**: Read replicas and connection pooling
- **Cache Scaling**: Redis cluster scaling

### Monitoring Metrics

Key metrics monitored:
- Response time (95th percentile < 1s)
- Error rate (< 1%)
- CPU utilization (< 80%)
- Memory utilization (< 85%)
- Database connections
- Queue length

## 🔄 CI/CD Pipeline

### Pipeline Stages

1. **Code Quality**: Linting, formatting, type checking
2. **Testing**: Unit, integration, security, performance tests
3. **Security Scanning**: Vulnerability assessment
4. **Build**: Docker image creation
5. **Deploy**: Staging and production deployment
6. **Monitoring**: Health checks and alerting

### Pipeline Triggers

- **Push to main**: Production deployment
- **Push to develop**: Staging deployment
- **Pull Request**: Testing and security scanning
- **Schedule**: Weekly dependency updates and security scans

## 🛠️ Maintenance

### Regular Tasks

- **Daily**: Health checks, backup verification
- **Weekly**: Dependency updates, security scans
- **Monthly**: Infrastructure updates, performance reviews
- **Quarterly**: Security audits, disaster recovery testing

### Troubleshooting

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f service_name

# Health check
python scripts/health_check.py

# Database connection
docker-compose exec db psql -U clasharena_user -d clasharena

# Redis connection
docker-compose exec redis redis-cli ping
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Terraform Documentation](https://www.terraform.io/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests locally
5. Submit a pull request

The CI/CD pipeline will automatically test your changes.

## 📞 Support

For issues and questions:
- Check the logs: `docker-compose logs`
- Run health checks: `python scripts/health_check.py`
- Review monitoring dashboards
- Check GitHub Actions logs

---

**Note**: This automation framework is designed to be production-ready. Always test changes in a staging environment before deploying to production.
