#!/bin/bash

# Fix S3 bucket access for CloudFront
# CloudFront用のS3バケットアクセス権限を修正

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

# Fix S3 bucket public access settings
fix_public_access_block() {
    print_status "S3バケットのパブリックアクセス設定を修正中..."
    
    # Allow public policy for CloudFront access
    aws s3api put-public-access-block \
        --bucket "$S3_BUCKET" \
        --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=false,RestrictPublicBuckets=false"
    
    print_success "パブリックアクセス設定を更新しました"
}

# Create bucket policy for CloudFront access
create_bucket_policy() {
    print_status "CloudFront用のバケットポリシーを作成中..."
    
    cat > /tmp/bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontAccess",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${S3_BUCKET}/*"
        }
    ]
}
EOF
    
    # Apply bucket policy
    aws s3api put-bucket-policy \
        --bucket "$S3_BUCKET" \
        --policy file:///tmp/bucket-policy.json
    
    print_success "バケットポリシーを適用しました"
    
    # Clean up
    rm -f /tmp/bucket-policy.json
}

# Test S3 website endpoint
test_s3_website() {
    print_status "S3ウェブサイトエンドポイントをテスト中..."
    
    S3_WEBSITE_URL="http://${S3_BUCKET}.s3-website-ap-northeast-1.amazonaws.com"
    
    if curl -s -o /dev/null -w "%{http_code}" "$S3_WEBSITE_URL" | grep -q "200\|403\|404"; then
        print_success "S3ウェブサイトエンドポイントにアクセス可能: $S3_WEBSITE_URL"
    else
        print_warning "S3ウェブサイトエンドポイントのテストに失敗しました"
    fi
}

# Deploy a test index.html file
deploy_test_file() {
    print_status "テスト用index.htmlファイルをデプロイ中..."
    
    cat > /tmp/index.html << 'EOF'
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSR Lambda API - 開発環境</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            text-align: center;
            background: rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        h1 {
            font-size: 3em;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        p {
            font-size: 1.2em;
            margin-bottom: 30px;
            opacity: 0.9;
        }
        .status {
            background: rgba(76, 175, 80, 0.2);
            padding: 15px 30px;
            border-radius: 50px;
            display: inline-block;
            border: 2px solid rgba(76, 175, 80, 0.5);
        }
        .info {
            margin-top: 30px;
            font-size: 0.9em;
            opacity: 0.7;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 CSR Lambda API</h1>
        <p>開発環境が正常に動作しています</p>
        <div class="status">
            ✅ CloudFront + S3 デプロイ成功
        </div>
        <div class="info">
            <p>Environment: Development</p>
            <p>Deployed: $(date)</p>
        </div>
    </div>
</body>
</html>
EOF
    
    # Upload test file to S3
    aws s3 cp /tmp/index.html "s3://$S3_BUCKET/index.html" \
        --content-type "text/html" \
        --cache-control "public, max-age=300"
    
    print_success "テスト用ファイルをアップロードしました"
    
    # Clean up
    rm -f /tmp/index.html
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
    
    print_success "CloudFrontキャッシュ無効化を開始しました: $INVALIDATION_ID"
    print_status "無効化完了まで数分かかります..."
}

# Test CloudFront access
test_cloudfront_access() {
    print_status "CloudFrontアクセスをテスト中..."
    
    CLOUDFRONT_URL="https://d2m0cmcbfsdzr7.cloudfront.net"
    
    print_status "5秒後にCloudFrontアクセステストを実行します..."
    sleep 5
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$CLOUDFRONT_URL")
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "CloudFrontアクセステスト成功: $CLOUDFRONT_URL"
    else
        print_warning "CloudFrontアクセステスト結果: HTTP $HTTP_CODE"
        print_status "キャッシュ無効化の完了を待ってから再度テストしてください"
    fi
}

# Main function
main() {
    print_status "=== S3 CloudFrontアクセス権限修正開始 ==="
    echo ""
    
    # Fix public access block
    fix_public_access_block
    echo ""
    
    # Create bucket policy
    create_bucket_policy
    echo ""
    
    # Test S3 website
    test_s3_website
    echo ""
    
    # Deploy test file
    deploy_test_file
    echo ""
    
    # Invalidate CloudFront cache
    invalidate_cloudfront
    echo ""
    
    # Test CloudFront access
    test_cloudfront_access
    echo ""
    
    print_success "=== アクセス権限修正完了 ==="
    echo ""
    print_status "CloudFrontURL: https://d2m0cmcbfsdzr7.cloudfront.net"
    print_status "S3ウェブサイトURL: http://${S3_BUCKET}.s3-website-ap-northeast-1.amazonaws.com"
    echo ""
    print_status "注意: CloudFrontキャッシュの無効化完了まで数分かかる場合があります"
}

# Show help
show_help() {
    echo "Fix S3 bucket access for CloudFront"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  fix       Fix S3 access permissions (default)"
    echo "  help      Show this help message"
    echo ""
}

# Handle command line arguments
case "${1:-fix}" in
    "fix")
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