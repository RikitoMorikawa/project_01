#!/bin/bash

# Deploy to Development CloudFront Environment with RDS
# CloudFront開発環境（RDS使用）へのデプロイ

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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Load CloudFront configuration
if [ -f "$BACKEND_DIR/.env.dev.cloudfront" ]; then
    source "$BACKEND_DIR/.env.dev.cloudfront"
else
    print_error "CloudFront設定ファイルが見つかりません: $BACKEND_DIR/.env.dev.cloudfront"
    exit 1
fi

# Load RDS configuration
if [ -f "$BACKEND_DIR/.env.dev.rds" ]; then
    source "$BACKEND_DIR/.env.dev.rds"
else
    print_error "RDS設定ファイルが見つかりません: $BACKEND_DIR/.env.dev.rds"
    exit 1
fi

# Deploy backend to AWS Lambda
deploy_backend() {
    print_status "バックエンドをAWS Lambdaにデプロイ中..."
    
    cd "$BACKEND_DIR"
    
    # Create deployment package
    print_status "デプロイメントパッケージを作成中..."
    
    # Install dependencies
    pip install -r requirements.txt -t ./deployment/
    
    # Copy application code
    cp -r app/ ./deployment/
    cp .env.dev.rds ./deployment/.env
    
    # Create ZIP package
    cd deployment
    zip -r ../lambda-deployment.zip .
    cd ..
    
    # Deploy to Lambda (assuming Lambda function exists)
    # 注意: 実際のLambda関数名に置き換えてください
    LAMBDA_FUNCTION_NAME="csr-lambda-api-dev"
    
    if aws lambda get-function --function-name "$LAMBDA_FUNCTION_NAME" > /dev/null 2>&1; then
        print_status "Lambda関数を更新中: $LAMBDA_FUNCTION_NAME"
        aws lambda update-function-code \
            --function-name "$LAMBDA_FUNCTION_NAME" \
            --zip-file fileb://lambda-deployment.zip
        
        # Update environment variables
        aws lambda update-function-configuration \
            --function-name "$LAMBDA_FUNCTION_NAME" \
            --environment Variables="{
                DB_HOST=$DB_HOST,
                DB_PORT=$DB_PORT,
                DB_NAME=$DB_NAME,
                DB_USER=$DB_USER,
                DB_PASSWORD=$DB_PASSWORD,
                AWS_REGION=$AWS_REGION,
                COGNITO_USER_POOL_ID=$COGNITO_USER_POOL_ID,
                COGNITO_CLIENT_ID=$COGNITO_CLIENT_ID,
                ENVIRONMENT=$ENVIRONMENT
            }"
        
        print_success "Lambda関数を更新しました"
    else
        print_error "Lambda関数が見つかりません: $LAMBDA_FUNCTION_NAME"
        print_status "Lambda関数を先に作成してください"
        exit 1
    fi
    
    # Clean up
    rm -rf deployment/
    rm -f lambda-deployment.zip
    
    cd "$PROJECT_ROOT"
}

# Deploy frontend to S3 and invalidate CloudFront
deploy_frontend() {
    print_status "フロントエンドをS3にデプロイ中..."
    
    cd "$FRONTEND_DIR"
    
    # Build frontend
    print_status "フロントエンドをビルド中..."
    npm run build
    
    # Deploy to S3
    print_status "S3バケットにアップロード中: $S3_FRONTEND_BUCKET"
    aws s3 sync ./out/ "s3://$S3_FRONTEND_BUCKET" --delete
    
    # Invalidate CloudFront cache
    print_status "CloudFrontキャッシュを無効化中..."
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text)
    
    print_success "CloudFrontキャッシュ無効化を開始しました: $INVALIDATION_ID"
    print_status "無効化完了を待機中..."
    
    aws cloudfront wait invalidation-completed \
        --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
        --id "$INVALIDATION_ID"
    
    print_success "CloudFrontキャッシュ無効化が完了しました"
    
    cd "$PROJECT_ROOT"
}

# Test RDS connection
test_rds_connection() {
    print_status "RDS接続をテスト中..."
    
    cd "$BACKEND_DIR"
    
    # Create test script
    cat > test_rds.py << EOF
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load RDS environment variables
load_dotenv('.env.dev.rds')

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in environment")
    sys.exit(1)

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("SUCCESS: RDS connection successful")
        print(f"Database: {os.getenv('DB_NAME')}")
        print(f"Host: {os.getenv('DB_HOST')}")
except Exception as e:
    print(f"ERROR: RDS connection failed: {e}")
    sys.exit(1)
EOF
    
    python test_rds.py
    rm -f test_rds.py
    
    cd "$PROJECT_ROOT"
}

# Main deployment function
main() {
    print_status "=== CloudFront開発環境デプロイ開始 (RDS使用) ==="
    echo ""
    
    print_status "設定情報:"
    echo "  CloudFrontドメイン: $CLOUDFRONT_DOMAIN_NAME"
    echo "  S3バケット: $S3_FRONTEND_BUCKET"
    echo "  RDSホスト: $DB_HOST"
    echo "  データベース: $DB_NAME"
    echo ""
    
    # Test RDS connection
    test_rds_connection
    echo ""
    
    # Deploy backend
    deploy_backend
    echo ""
    
    # Deploy frontend
    deploy_frontend
    echo ""
    
    print_success "=== デプロイ完了 ==="
    echo "フロントエンドURL: https://$CLOUDFRONT_DOMAIN_NAME"
    echo "バックエンドAPI: Lambda関数経由でRDSに接続"
    echo ""
}

# Show help
show_help() {
    echo "Deploy to Development CloudFront Environment with RDS"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  deploy    Deploy both frontend and backend (default)"
    echo "  frontend  Deploy frontend only"
    echo "  backend   Deploy backend only"
    echo "  test      Test RDS connection only"
    echo "  help      Show this help message"
    echo ""
    echo "Prerequisites:"
    echo "  - AWS CLI configured with appropriate permissions"
    echo "  - RDS instance running and accessible"
    echo "  - Lambda function created"
    echo "  - S3 bucket and CloudFront distribution configured"
    echo ""
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "frontend")
        deploy_frontend
        ;;
    "backend")
        deploy_backend
        ;;
    "test")
        test_rds_connection
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