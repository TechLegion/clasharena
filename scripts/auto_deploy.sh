#!/bin/bash

# ClashArena Automated Deployment Script
set -e

echo "🚀 Starting ClashArena Automated Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
SKIP_TESTS="${SKIP_TESTS:-false}"
SKIP_BUILD="${SKIP_BUILD:-false}"
ROLLBACK_ON_FAILURE="${ROLLBACK_ON_FAILURE:-true}"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run tests
run_tests() {
    if [ "$SKIP_TESTS" = "true" ]; then
        print_warning "Skipping tests as requested"
        return 0
    fi
    
    print_status "Running automated tests..."
    
    if command_exists python3; then
        python3 scripts/automated_testing.py
        if [ $? -eq 0 ]; then
            print_success "All tests passed"
        else
            print_error "Tests failed"
            return 1
        fi
    else
        print_warning "Python3 not found, skipping automated tests"
    fi
}

# Function to build Docker images
build_images() {
    if [ "$SKIP_BUILD" = "true" ]; then
        print_warning "Skipping build as requested"
        return 0
    fi
    
    print_status "Building Docker images..."
    
    # Build backend image
    docker build -t clasharena-backend:latest ./backend
    if [ $? -eq 0 ]; then
        print_success "Backend image built successfully"
    else
        print_error "Failed to build backend image"
        return 1
    fi
    
    # Build frontend image (if needed)
    if [ -d "frontend" ]; then
        docker build -t clasharena-frontend:latest ./frontend
        if [ $? -eq 0 ]; then
            print_success "Frontend image built successfully"
        else
            print_error "Failed to build frontend image"
            return 1
        fi
    fi
}

# Function to run security scan
run_security_scan() {
    print_status "Running security scan..."
    
    if command_exists trivy; then
        trivy image clasharena-backend:latest
        if [ $? -eq 0 ]; then
            print_success "Security scan passed"
        else
            print_warning "Security scan found issues"
        fi
    else
        print_warning "Trivy not found, skipping security scan"
    fi
}

# Function to backup current deployment
backup_current_deployment() {
    print_status "Creating backup of current deployment..."
    
    # Create backup directory
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    if command_exists pg_dump; then
        pg_dump -h localhost -U clasharena_user -d clasharena > "$BACKUP_DIR/database.sql"
        print_success "Database backed up to $BACKUP_DIR/database.sql"
    fi
    
    # Backup configuration files
    cp -r backend/app/core/config.py "$BACKUP_DIR/" 2>/dev/null || true
    cp docker-compose.prod.yml "$BACKUP_DIR/" 2>/dev/null || true
    
    echo "$BACKUP_DIR" > .last_backup
    print_success "Backup created at $BACKUP_DIR"
}

# Function to deploy to staging
deploy_staging() {
    print_status "Deploying to staging environment..."
    
    # Use staging docker-compose file
    docker-compose -f docker-compose.yml up -d --force-recreate
    
    # Wait for services to be ready
    sleep 30
    
    # Run health checks
    if python3 scripts/health_check.py; then
        print_success "Staging deployment successful"
        return 0
    else
        print_error "Staging deployment failed health checks"
        return 1
    fi
}

# Function to deploy to production
deploy_production() {
    print_status "Deploying to production environment..."
    
    # Use production docker-compose file
    docker-compose -f docker-compose.prod.yml up -d --force-recreate
    
    # Wait for services to be ready
    sleep 60
    
    # Run health checks
    if python3 scripts/health_check.py; then
        print_success "Production deployment successful"
        return 0
    else
        print_error "Production deployment failed health checks"
        return 1
    fi
}

# Function to rollback deployment
rollback_deployment() {
    if [ "$ROLLBACK_ON_FAILURE" != "true" ]; then
        print_warning "Rollback disabled, skipping rollback"
        return 0
    fi
    
    print_status "Rolling back deployment..."
    
    if [ -f ".last_backup" ]; then
        BACKUP_DIR=$(cat .last_backup)
        
        # Restore database
        if [ -f "$BACKUP_DIR/database.sql" ] && command_exists psql; then
            psql -h localhost -U clasharena_user -d clasharena < "$BACKUP_DIR/database.sql"
            print_success "Database restored from backup"
        fi
        
        # Restart services
        docker-compose -f docker-compose.prod.yml restart
        
        print_success "Rollback completed"
    else
        print_error "No backup found for rollback"
        return 1
    fi
}

# Function to update monitoring
update_monitoring() {
    print_status "Updating monitoring configuration..."
    
    # Restart monitoring services
    docker-compose -f docker-compose.monitoring.yml up -d --force-recreate
    
    print_success "Monitoring updated"
}

# Function to send deployment notification
send_notification() {
    local status=$1
    local message=$2
    
    print_status "Sending deployment notification..."
    
    # Send webhook notification (if configured)
    if [ ! -z "$WEBHOOK_URL" ]; then
        curl -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"status\":\"$status\",\"message\":\"$message\",\"environment\":\"$ENVIRONMENT\",\"timestamp\":\"$(date -Iseconds)\"}"
    fi
    
    # Send email notification (if configured)
    if [ ! -z "$NOTIFICATION_EMAIL" ] && command_exists mail; then
        echo "$message" | mail -s "ClashArena Deployment $status" "$NOTIFICATION_EMAIL"
    fi
    
    print_success "Notification sent"
}

# Main deployment function
main() {
    print_status "Starting ClashArena automated deployment..."
    print_status "Environment: $ENVIRONMENT"
    print_status "Skip tests: $SKIP_TESTS"
    print_status "Skip build: $SKIP_BUILD"
    print_status "Rollback on failure: $ROLLBACK_ON_FAILURE"
    
    # Check prerequisites
    if ! command_exists docker; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Run deployment steps
    set +e  # Allow errors for rollback handling
    
    # Step 1: Run tests
    run_tests
    if [ $? -ne 0 ]; then
        print_error "Tests failed, aborting deployment"
        send_notification "failed" "Deployment failed at testing stage"
        exit 1
    fi
    
    # Step 2: Build images
    build_images
    if [ $? -ne 0 ]; then
        print_error "Build failed, aborting deployment"
        send_notification "failed" "Deployment failed at build stage"
        exit 1
    fi
    
    # Step 3: Run security scan
    run_security_scan
    
    # Step 4: Create backup
    backup_current_deployment
    
    # Step 5: Deploy to staging (if not production)
    if [ "$ENVIRONMENT" != "production" ]; then
        deploy_staging
        if [ $? -ne 0 ]; then
            print_error "Staging deployment failed"
            send_notification "failed" "Staging deployment failed"
            exit 1
        fi
    fi
    
    # Step 6: Deploy to production
    if [ "$ENVIRONMENT" = "production" ]; then
        deploy_production
        if [ $? -ne 0 ]; then
            print_error "Production deployment failed"
            rollback_deployment
            send_notification "failed" "Production deployment failed, rollback attempted"
            exit 1
        fi
    fi
    
    # Step 7: Update monitoring
    update_monitoring
    
    # Step 8: Send success notification
    send_notification "success" "Deployment completed successfully"
    
    print_success "🎉 ClashArena deployment completed successfully!"
    print_status "Environment: $ENVIRONMENT"
    print_status "Timestamp: $(date)"
}

# Handle script interruption
trap 'print_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"
