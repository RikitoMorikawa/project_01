#!/bin/bash

# Deploy Frontend to Development Environment
# フロントエンドを開発環境にデプロイ

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
S3_BUCKET="csr-lambda-api-dev-main-frontends3bucket-a8n79be9xmun"
CLOUDFRONT_DISTRIBUTION_ID="E1RDC06Y79TYSS"
API_URL="https://your-api-gateway-url.execute-api.ap-northeast-1.amazonaws.com/v1"  # 後で更新

# Build frontend
build_frontend() {
    print_status "フロントエンドをビルド中..."
    
    cd frontend
    
    # Install dependencies
    if [ ! -d "node_modules" ]; then
        print_status "依存関係をインストール中..."
        npm ci
    fi
    
    # Create environment file for production build
    cat > .env.production << EOF
NEXT_PUBLIC_API_URL=${API_URL}
NEXT_PUBLIC_ENVIRONMENT=dev
NEXT_PUBLIC_AWS_REGION=ap-northeast-1
NEXT_PUBLIC_COGNITO_USER_POOL_ID=ap-northeast-1_HluYCXwCo
NEXT_PUBLIC_COGNITO_CLIENT_ID=71mnemjh6en2qpd5cmv21qp30u
EOF
    
    print_status "Next.jsアプリをビルド中..."
    npm run build
    
    if [ $? -eq 0 ]; then
        print_success "フロントエンドビルド完了"
    else
        print_error "フロントエンドビルドに失敗しました"
        cd ..
        exit 1
    fi
    
    cd ..
}

# Deploy to S3
deploy_to_s3() {
    print_status "S3にデプロイ中..."
    
    # Check if build output exists
    if [ ! -d "frontend/out" ] && [ ! -d "frontend/.next" ]; then
        print_error "ビルド出力が見つかりません"
        exit 1
    fi
    
    # Determine build output directory
    if [ -d "frontend/out" ]; then
        BUILD_DIR="frontend/out"
    else
        BUILD_DIR="frontend/.next"
    fi
    
    print_status "ビルド出力ディレクトリ: $BUILD_DIR"
    
    # Clear existing files in S3
    print_status "既存のS3ファイルを削除中..."
    aws s3 rm "s3://$S3_BUCKET" --recursive
    
    # Upload new files
    print_status "新しいファイルをS3にアップロード中..."
    aws s3 sync "$BUILD_DIR/" "s3://$S3_BUCKET" \
        --delete \
        --cache-control "public, max-age=31536000" \
        --exclude "*.html" \
        --exclude "*.json"
    
    # Upload HTML files with shorter cache
    aws s3 sync "$BUILD_DIR/" "s3://$S3_BUCKET" \
        --cache-control "public, max-age=300" \
        --include "*.html" \
        --include "*.json"
    
    print_success "S3デプロイ完了"
}

# Invalidate CloudFront cache
invalidate_cloudfront() {
    print_status "CloudFrontキャッシュを無効化中..."
    
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
        --paths "/*" \
        --region us-east-1 \
        --query 'Invalidation.Id' \
        --output text)
    
    print_success "CloudFrontキャッシュ無効化を開始: $INVALIDATION_ID"
    print_status "無効化完了まで数分かかります..."
}

# Test deployment
test_deployment() {
    print_status "デプロイメントをテスト中..."
    
    CLOUDFRONT_URL="https://d2m0cmcbfsdzr7.cloudfront.net"
    
    print_status "10秒後にアクセステストを実行します..."
    sleep 10
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$CLOUDFRONT_URL")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "デプロイメントテスト成功: $CLOUDFRONT_URL"
    else
        print_warning "デプロイメントテスト結果: HTTP $HTTP_CODE"
        print_status "キャッシュ無効化の完了を待ってから再度確認してください"
    fi
}

# Check Next.js configuration
check_nextjs_config() {
    print_status "Next.js設定を確認中..."
    
    if [ -f "frontend/next.config.js" ]; then
        print_status "next.config.js が見つかりました"
        
        # Check if static export is configured
        if grep -q "output.*export" frontend/next.config.js; then
            print_success "静的エクスポート設定が確認されました"
        else
            print_warning "静的エクスポート設定が見つかりません"
            print_status "next.config.js に output: 'export' を追加することを推奨します"
        fi
    else
        print_warning "next.config.js が見つかりません"
    fi
}

# Main function
main() {
    print_status "=== フロントエンド開発環境デプロイ開始 ==="
    echo ""
    
    # Check Next.js configuration
    check_nextjs_config
    echo ""
    
    # Build frontend
    build_frontend
    echo ""
    
    # Deploy to S3
    deploy_to_s3
    echo ""
    
    # Invalidate CloudFront cache
    invalidate_cloudfront
    echo ""
    
    # Test deployment
    test_deployment
    echo ""
    
    print_success "=== フロントエンドデプロイ完了 ==="
    echo ""
    print_status "CloudFrontURL: https://d2m0cmcbfsdzr7.cloudfront.net"
    print_status "ローカル環境: http://localhost:3000"
    echo ""
    print_status "注意: CloudFrontキャッシュの無効化完了まで数分かかる場合があります"
}

# Show help
show_help() {
    echo "Deploy Frontend to Development Environment"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  deploy    Deploy frontend to development (default)"
    echo "  help      Show this help message"
    echo ""
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
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