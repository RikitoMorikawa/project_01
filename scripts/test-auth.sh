#!/bin/bash

# Test Authentication Setup Script
# Cognito設定とテストユーザーの動作確認

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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check environment variables
check_env_vars() {
    print_status "Checking environment variables..."
    
    # Backend environment
    if [ -f "backend/.env.dev" ]; then
        print_status "Backend environment variables:"
        grep -E "(COGNITO_USER_POOL_ID|COGNITO_CLIENT_ID|AWS_REGION)" backend/.env.dev || print_warning "Some backend env vars missing"
    else
        print_error "backend/.env.dev not found"
    fi
    
    echo ""
    
    # Frontend environment
    if [ -f "frontend/.env.local" ]; then
        print_status "Frontend environment variables:"
        grep -E "(NEXT_PUBLIC_COGNITO_USER_POOL_ID|NEXT_PUBLIC_COGNITO_CLIENT_ID|NEXT_PUBLIC_AWS_REGION)" frontend/.env.local || print_warning "Some frontend env vars missing"
    else
        print_error "frontend/.env.local not found"
    fi
}

# Check Cognito resources
check_cognito() {
    print_status "Checking Cognito resources..."
    
    local user_pool_id=$(grep "COGNITO_USER_POOL_ID=" backend/.env.dev | cut -d'=' -f2)
    
    if [ -z "$user_pool_id" ]; then
        print_error "User Pool ID not found in environment"
        return 1
    fi
    
    # Check User Pool
    if aws cognito-idp describe-user-pool --user-pool-id "$user_pool_id" > /dev/null 2>&1; then
        print_success "User Pool exists: $user_pool_id"
    else
        print_error "User Pool not found: $user_pool_id"
        return 1
    fi
    
    # Check App Clients
    local clients=$(aws cognito-idp list-user-pool-clients --user-pool-id "$user_pool_id" --query 'UserPoolClients[].ClientName' --output text)
    if [ -n "$clients" ]; then
        print_success "App Clients found: $clients"
    else
        print_warning "No App Clients found"
    fi
    
    # Check test user
    if aws cognito-idp admin-get-user --user-pool-id "$user_pool_id" --username "test@example.com" > /dev/null 2>&1; then
        print_success "Test user exists: test@example.com"
    else
        print_warning "Test user not found: test@example.com"
    fi
}

# Check database
check_database() {
    print_status "Checking database..."
    
    if docker exec csr-lambda-mysql mysql -u dev_user -pdev_password -e "USE csr_lambda_dev; SELECT COUNT(*) as user_count FROM users;" 2>/dev/null | grep -q "user_count"; then
        local count=$(docker exec csr-lambda-mysql mysql -u dev_user -pdev_password -e "USE csr_lambda_dev; SELECT COUNT(*) as user_count FROM users;" 2>/dev/null | tail -n 1)
        print_success "Database accessible, users table has $count records"
    else
        print_error "Database connection failed"
        return 1
    fi
}

# Check services
check_services() {
    print_status "Checking services..."
    
    # Backend API
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        print_success "Backend API is responding"
    else
        print_error "Backend API is not responding"
    fi
    
    # Frontend
    if curl -s http://localhost:3000/ > /dev/null 2>&1; then
        print_success "Frontend is responding"
    else
        print_error "Frontend is not responding"
    fi
}

# Show test credentials
show_test_info() {
    echo ""
    print_success "=== Test Information ==="
    print_status "Test User Credentials:"
    print_status "  📧 Email: test@example.com"
    print_status "  🔑 Password: Test123!@#"
    echo ""
    print_status "URLs:"
    print_status "  🌐 Frontend: http://localhost:3000"
    print_status "  🔗 Login: http://localhost:3000/login"
    print_status "  📚 API Docs: http://localhost:8000/docs"
    echo ""
    print_status "Next Steps:"
    print_status "  1. Open http://localhost:3000/login in your browser"
    print_status "  2. Login with test@example.com / Test123!@#"
    print_status "  3. Check if authentication works correctly"
}

# Main function
main() {
    print_status "=== Authentication Setup Test ==="
    echo ""
    
    check_env_vars
    echo ""
    
    check_cognito
    echo ""
    
    check_database
    echo ""
    
    check_services
    echo ""
    
    show_test_info
}

main