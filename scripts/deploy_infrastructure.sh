#!/bin/bash

# ClashArena Infrastructure Deployment Script
set -e

echo "🚀 Deploying ClashArena Infrastructure..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TERRAFORM_DIR="terraform"
TF_STATE_BUCKET="${TF_STATE_BUCKET:-clasharena-terraform-state}"
TF_STATE_KEY="${TF_STATE_KEY:-terraform.tfstate}"
TF_STATE_REGION="${TF_STATE_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-production}"

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

# Check if required tools are installed
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install Terraform first."
        exit 1
    fi
    
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install AWS CLI first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Initialize Terraform backend
init_terraform() {
    print_status "Initializing Terraform..."
    
    cd $TERRAFORM_DIR
    
    # Create S3 bucket for Terraform state if it doesn't exist
    if ! aws s3 ls "s3://$TF_STATE_BUCKET" 2>&1 | grep -q 'NoSuchBucket'; then
        print_status "Terraform state bucket already exists"
    else
        print_status "Creating Terraform state bucket: $TF_STATE_BUCKET"
        aws s3 mb "s3://$TF_STATE_BUCKET" --region $TF_STATE_REGION
        
        # Enable versioning
        aws s3api put-bucket-versioning \
            --bucket $TF_STATE_BUCKET \
            --versioning-configuration Status=Enabled
    fi
    
    # Initialize Terraform
    terraform init \
        -backend-config="bucket=$TF_STATE_BUCKET" \
        -backend-config="key=$TF_STATE_KEY" \
        -backend-config="region=$TF_STATE_REGION"
    
    print_success "Terraform initialized"
}

# Validate Terraform configuration
validate_terraform() {
    print_status "Validating Terraform configuration..."
    
    terraform validate
    
    print_success "Terraform configuration is valid"
}

# Plan Terraform deployment
plan_terraform() {
    print_status "Planning Terraform deployment..."
    
    terraform plan \
        -var-file="terraform.tfvars" \
        -out="terraform.tfplan"
    
    print_success "Terraform plan completed"
}

# Apply Terraform deployment
apply_terraform() {
    print_status "Applying Terraform deployment..."
    
    terraform apply "terraform.tfplan"
    
    print_success "Terraform deployment completed"
}

# Get deployment outputs
get_outputs() {
    print_status "Getting deployment outputs..."
    
    echo ""
    echo -e "${GREEN}🎉 Infrastructure Deployment Complete!${NC}"
    echo ""
    echo -e "${YELLOW}📋 Deployment Information:${NC}"
    echo "  Environment: $ENVIRONMENT"
    echo "  Load Balancer DNS: $(terraform output -raw load_balancer_dns)"
    echo "  Application URL: $(terraform output -raw application_url)"
    echo "  ECS Cluster: $(terraform output -raw ecs_cluster_name)"
    echo "  Database Endpoint: $(terraform output -raw database_endpoint)"
    echo "  Redis Endpoint: $(terraform output -raw redis_endpoint)"
    echo "  Backup Bucket: $(terraform output -raw backup_bucket_name)"
    echo ""
    echo -e "${YELLOW}🔧 Next Steps:${NC}"
    echo "  1. Update your DNS to point to the load balancer"
    echo "  2. Deploy your application using the CI/CD pipeline"
    echo "  3. Configure monitoring and alerting"
    echo "  4. Set up automated backups"
    echo ""
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    cd ..
    print_success "Cleanup completed"
}

# Main deployment function
main() {
    print_status "Starting ClashArena infrastructure deployment..."
    
    # Check if terraform.tfvars exists
    if [ ! -f "$TERRAFORM_DIR/terraform.tfvars" ]; then
        print_error "terraform.tfvars file not found in $TERRAFORM_DIR/"
        print_warning "Please copy terraform.tfvars.example to terraform.tfvars and configure it"
        exit 1
    fi
    
    # Check if user wants to proceed
    read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Deployment cancelled"
        exit 0
    fi
    
    # Execute deployment steps
    check_prerequisites
    init_terraform
    validate_terraform
    plan_terraform
    
    # Ask for confirmation before applying
    echo ""
    print_warning "Review the plan above. This will create AWS resources that may incur costs."
    read -p "Do you want to apply the changes? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Deployment cancelled"
        exit 0
    fi
    
    apply_terraform
    get_outputs
    cleanup
    
    print_success "Infrastructure deployment completed successfully!"
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@"
