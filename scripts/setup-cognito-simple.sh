#!/bin/bash

# Simple AWS Cognito Setup Script for CSR Lambda Development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create User Pool
create_user_pool() {
    print_status "Creating Cognito User Pool..."
    
    local user_pool_id=$(aws cognito-idp create-user-pool \
        --pool-name "csr-lambda-dev-pool" \
        --auto-verified-attributes email \
        --username-attributes email \
        --query 'UserPool.Id' \
        --output text 2>/dev/null)
    
    if [ -z "$user_pool_id" ]; then
        print_error "Failed to create User Pool"
        exit 1
    fi
    
    print_success "User Pool created: $user_pool_id"
    echo "$user_pool_id"
}

# Create App Client
create_app_client() {
    local user_pool_id=$1
    
    print_status "Creating App Client..."
    
    local client_id=$(aws cognito-idp create-user-pool-client \
        --user-pool-id "$user_pool_id" \
        --client-name "csr-lambda-dev-client" \
        --explicit-auth-flows ALLOW_USER_SRP_AUTH ALLOW_REFRESH_TOKEN_AUTH \
        --query 'UserPoolClient.ClientId' \
        --output text 2>/dev/null)
    
    if [ -z "$client_id" ]; then
        print_error "Failed to create App Client"
        exit 1
    fi
    
    print_success "App Client created: $client_id"
    echo "$client_id"
}

# Update environment files
update_env_files() {
    local user_pool_id=$1
    local client_id=$2
    local region=$(aws configure get region || echo "ap-northeast-1")
    
    print_status "Updating environment files..."
    
    # Update backend .env.dev
    sed -i.bak "s/COGNITO_USER_POOL_ID=.*/COGNITO_USER_POOL_ID=$user_pool_id/" backend/.env.dev
    sed -i.bak "s/COGNITO_CLIENT_ID=.*/COGNITO_CLIENT_ID=$client_id/" backend/.env.dev
    
    # Update frontend .env.local
    sed -i.bak "s/NEXT_PUBLIC_COGNITO_USER_POOL_ID=.*/NEXT_PUBLIC_COGNITO_USER_POOL_ID=$user_pool_id/" frontend/.env.local
    sed -i.bak "s/NEXT_PUBLIC_COGNITO_CLIENT_ID=.*/NEXT_PUBLIC_COGNITO_CLIENT_ID=$client_id/" frontend/.env.local
    
    # Remove backup files
    rm -f backend/.env.dev.bak frontend/.env.local.bak
    
    print_success "Environment files updated"
}

# Create test user
create_test_user() {
    local user_pool_id=$1
    local email="test@example.com"
    
    print_status "Creating test user: $email"
    
    # Create user
    aws cognito-idp admin-create-user \
        --user-pool-id "$user_pool_id" \
        --username "$email" \
        --user-attributes Name=email,Value="$email" Name=email_verified,Value=true \
        --temporary-password "TempPass123!" \
        --message-action SUPPRESS \
        > /dev/null
    
    # Set permanent password
    aws cognito-idp admin-set-user-password \
        --user-pool-id "$user_pool_id" \
        --username "$email" \
        --password "Test123!@#" \
        --permanent \
        > /dev/null
    
    print_success "Test user created successfully"
}

# Main function
main() {
    print_status "=== AWS Cognito Setup Started ==="
    
    # Create resources
    user_pool_id=$(create_user_pool)
    client_id=$(create_app_client "$user_pool_id")
    
    # Update configuration
    update_env_files "$user_pool_id" "$client_id"
    
    # Create test user
    create_test_user "$user_pool_id"
    
    echo ""
    print_success "=== Cognito Setup Complete ==="
    print_status "User Pool ID: $user_pool_id"
    print_status "Client ID: $client_id"
    print_status "Test User: test@example.com / Test123!@#"
    echo ""
    print_status "Next steps:"
    print_status "  1. Restart development environment: ./scripts/dev-setup.sh restart"
    print_status "  2. Visit: http://localhost:3000/login"
    print_status "  3. Login with: test@example.com / Test123!@#"
}

main