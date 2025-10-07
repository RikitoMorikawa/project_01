#!/bin/bash

# AWS Cognito Setup Script for CSR Lambda Development
# ローカル開発用のCognito User PoolとApp Clientを作成

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if AWS CLI is installed
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI がインストールされていません"
        print_status "AWS CLI をインストールしてください: https://aws.amazon.com/cli/"
        exit 1
    fi
    print_success "AWS CLI が利用可能です"
}

# Check AWS credentials
check_aws_credentials() {
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS 認証情報が設定されていません"
        print_status "AWS 認証情報を設定してください:"
        print_status "  aws configure"
        print_status "または環境変数を設定してください:"
        print_status "  export AWS_ACCESS_KEY_ID=your_access_key"
        print_status "  export AWS_SECRET_ACCESS_KEY=your_secret_key"
        exit 1
    fi
    
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    local region=$(aws configure get region || echo "ap-northeast-1")
    print_success "AWS 認証情報が設定されています (Account: $account_id, Region: $region)"
}

# Create Cognito User Pool
create_user_pool() {
    local pool_name="csr-lambda-dev-pool"
    
    print_status "Cognito User Pool を作成中: $pool_name"
    
    local user_pool_id=$(aws cognito-idp create-user-pool \
        --pool-name "$pool_name" \
        --policies '{
            "PasswordPolicy": {
                "MinimumLength": 8,
                "RequireUppercase": true,
                "RequireLowercase": true,
                "RequireNumbers": true,
                "RequireSymbols": true
            }
        }' \
        --auto-verified-attributes email \
        --username-attributes email \
        --verification-message-template '{
            "DefaultEmailOption": "CONFIRM_WITH_CODE",
            "EmailSubject": "CSR Lambda - メールアドレスの確認",
            "EmailMessage": "CSR Lambda へようこそ！確認コード: {####}"
        }' \
        --admin-create-user-config '{
            "AllowAdminCreateUserOnly": false,
            "UnusedAccountValidityDays": 7
        }' \
        --user-pool-tags '{
            "Environment": "development",
            "Project": "csr-lambda"
        }' \
        --query 'UserPool.Id' \
        --output text)
    
    if [ -z "$user_pool_id" ]; then
        print_error "User Pool の作成に失敗しました"
        exit 1
    fi
    
    print_success "User Pool が作成されました: $user_pool_id"
    echo "$user_pool_id"
}

# Create Cognito App Client
create_app_client() {
    local user_pool_id=$1
    local client_name="csr-lambda-dev-client"
    
    print_status "Cognito App Client を作成中: $client_name"
    
    local client_id=$(aws cognito-idp create-user-pool-client \
        --user-pool-id "$user_pool_id" \
        --client-name "$client_name" \
        --no-generate-secret \
        --refresh-token-validity 30 \
        --access-token-validity 60 \
        --id-token-validity 60 \
        --token-validity-units '{
            "AccessToken": "minutes",
            "IdToken": "minutes",
            "RefreshToken": "days"
        }' \
        --explicit-auth-flows ALLOW_USER_SRP_AUTH ALLOW_REFRESH_TOKEN_AUTH \
        --prevent-user-existence-errors ENABLED \
        --enable-token-revocation \
        --query 'UserPoolClient.ClientId' \
        --output text)
    
    if [ -z "$client_id" ]; then
        print_error "App Client の作成に失敗しました"
        exit 1
    fi
    
    print_success "App Client が作成されました: $client_id"
    echo "$client_id"
}

# Update environment files
update_env_files() {
    local user_pool_id=$1
    local client_id=$2
    local region=$(aws configure get region || echo "ap-northeast-1")
    
    print_status "環境変数ファイルを更新中..."
    
    # Update backend .env.dev
    sed -i.bak "s/COGNITO_USER_POOL_ID=.*/COGNITO_USER_POOL_ID=$user_pool_id/" backend/.env.dev
    sed -i.bak "s/COGNITO_CLIENT_ID=.*/COGNITO_CLIENT_ID=$client_id/" backend/.env.dev
    sed -i.bak "s/AWS_REGION=.*/AWS_REGION=$region/" backend/.env.dev
    
    # Update frontend .env.local
    sed -i.bak "s/NEXT_PUBLIC_COGNITO_USER_POOL_ID=.*/NEXT_PUBLIC_COGNITO_USER_POOL_ID=$user_pool_id/" frontend/.env.local
    sed -i.bak "s/NEXT_PUBLIC_COGNITO_CLIENT_ID=.*/NEXT_PUBLIC_COGNITO_CLIENT_ID=$client_id/" frontend/.env.local
    sed -i.bak "s/NEXT_PUBLIC_AWS_REGION=.*/NEXT_PUBLIC_AWS_REGION=$region/" frontend/.env.local
    sed -i.bak "s/NEXT_PUBLIC_LOCAL_DEV_MODE=.*/NEXT_PUBLIC_LOCAL_DEV_MODE=false/" frontend/.env.local
    
    # Remove backup files
    rm -f backend/.env.dev.bak frontend/.env.local.bak
    
    print_success "環境変数ファイルが更新されました"
}

# Create test user
create_test_user() {
    local user_pool_id=$1
    local email="test@example.com"
    local temp_password="TempPass123!"
    
    print_status "テストユーザーを作成中: $email"
    
    aws cognito-idp admin-create-user \
        --user-pool-id "$user_pool_id" \
        --username "$email" \
        --user-attributes Name=email,Value="$email" Name=email_verified,Value=true \
        --temporary-password "$temp_password" \
        --message-action SUPPRESS \
        > /dev/null
    
    # Set permanent password
    aws cognito-idp admin-set-user-password \
        --user-pool-id "$user_pool_id" \
        --username "$email" \
        --password "Test123!@#" \
        --permanent \
        > /dev/null
    
    print_success "テストユーザーが作成されました"
    print_status "  📧 Email: $email"
    print_status "  🔑 Password: Test123!@#"
}

# Main function
main() {
    print_status "=== AWS Cognito セットアップ開始 ==="
    echo ""
    
    # Check prerequisites
    check_aws_cli
    check_aws_credentials
    echo ""
    
    # Create Cognito resources
    user_pool_id=$(create_user_pool)
    client_id=$(create_app_client "$user_pool_id")
    echo ""
    
    # Update configuration files
    update_env_files "$user_pool_id" "$client_id"
    echo ""
    
    # Create test user
    create_test_user "$user_pool_id"
    echo ""
    
    print_success "=== Cognito セットアップ完了 ==="
    echo ""
    print_status "設定情報:"
    print_status "  User Pool ID: $user_pool_id"
    print_status "  Client ID: $client_id"
    print_status "  Region: $(aws configure get region || echo "ap-northeast-1")"
    echo ""
    print_status "次のステップ:"
    print_status "  1. 開発環境を再起動: ./scripts/dev-setup.sh restart"
    print_status "  2. ブラウザで http://localhost:3000/login にアクセス"
    print_status "  3. テストユーザーでログイン: test@example.com / Test123!@#"
    echo ""
}

# Show help
show_help() {
    echo "AWS Cognito Setup Script for CSR Lambda Development"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup     Create Cognito User Pool and App Client (default)"
    echo "  help      Show this help message"
    echo ""
    echo "Prerequisites:"
    echo "  - AWS CLI installed and configured"
    echo "  - Appropriate AWS permissions for Cognito operations"
    echo ""
}

# Handle command line arguments
case "${1:-setup}" in
    "setup")
        main
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac