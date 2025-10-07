#!/bin/bash

# Create CloudFront Distribution for Development Environment
# 開発環境用CloudFrontディストリビューションを作成

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
PROJECT_NAME="csr-lambda-api"
ENVIRONMENT="dev"
S3_BUCKET="csr-lambda-api-dev-main-frontends3bucket-a8n79be9xmun"
S3_REGION="ap-northeast-1"

# Create CloudFront distribution configuration
create_distribution_config() {
    cat > /tmp/cloudfront-config.json << EOF
{
    "CallerReference": "${PROJECT_NAME}-${ENVIRONMENT}-$(date +%s)",
    "Comment": "${PROJECT_NAME} ${ENVIRONMENT} CloudFront Distribution",
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3Origin",
        "ViewerProtocolPolicy": "redirect-to-https",
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        },
        "ForwardedValues": {
            "QueryString": false,
            "Cookies": {
                "Forward": "none"
            }
        },
        "MinTTL": 0,
        "DefaultTTL": 86400,
        "MaxTTL": 31536000,
        "Compress": true,
        "AllowedMethods": {
            "Quantity": 2,
            "Items": ["GET", "HEAD"],
            "CachedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"]
            }
        }
    },
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "S3Origin",
                "DomainName": "${S3_BUCKET}.s3-website-${S3_REGION}.amazonaws.com",
                "CustomOriginConfig": {
                    "HTTPPort": 80,
                    "HTTPSPort": 443,
                    "OriginProtocolPolicy": "http-only",
                    "OriginSslProtocols": {
                        "Quantity": 1,
                        "Items": ["TLSv1.2"]
                    }
                }
            }
        ]
    },
    "DefaultRootObject": "index.html",
    "Enabled": true,
    "PriceClass": "PriceClass_100",
    "CustomErrorResponses": {
        "Quantity": 2,
        "Items": [
            {
                "ErrorCode": 403,
                "ResponsePagePath": "/index.html",
                "ResponseCode": "200",
                "ErrorCachingMinTTL": 300
            },
            {
                "ErrorCode": 404,
                "ResponsePagePath": "/index.html",
                "ResponseCode": "200",
                "ErrorCachingMinTTL": 300
            }
        ]
    },
    "HttpVersion": "http2",
    "IsIPV6Enabled": true
}
EOF
}

# Create CloudFront distribution
create_cloudfront_distribution() {
    print_status "CloudFrontディストリビューションを作成中..."
    
    # Create distribution configuration
    create_distribution_config
    
    # Create CloudFront distribution
    DISTRIBUTION_RESULT=$(aws cloudfront create-distribution \
        --distribution-config file:///tmp/cloudfront-config.json \
        --region us-east-1 \
        --output json)
    
    if [ $? -eq 0 ]; then
        DISTRIBUTION_ID=$(echo "$DISTRIBUTION_RESULT" | jq -r '.Distribution.Id')
        DOMAIN_NAME=$(echo "$DISTRIBUTION_RESULT" | jq -r '.Distribution.DomainName')
        
        print_success "CloudFrontディストリビューションを作成しました"
        echo "  ディストリビューションID: $DISTRIBUTION_ID"
        echo "  ドメイン名: $DOMAIN_NAME"
        
        # Clean up
        rm -f /tmp/cloudfront-config.json
        
        # Wait for deployment
        print_status "ディストリビューションのデプロイを待機中..."
        print_warning "これには10-15分かかる場合があります..."
        
        aws cloudfront wait distribution-deployed \
            --id "$DISTRIBUTION_ID" \
            --region us-east-1
        
        print_success "ディストリビューションのデプロイが完了しました"
        
        # Output final information
        echo ""
        print_success "=== 開発環境CloudFront作成完了 ==="
        echo "ディストリビューションID: $DISTRIBUTION_ID"
        echo "CloudFrontドメイン: https://$DOMAIN_NAME"
        echo "オリジンS3バケット: $S3_BUCKET"
        echo ""
        print_status "次のステップ:"
        print_status "  1. フロントエンドをビルド・デプロイ"
        print_status "  2. https://$DOMAIN_NAME でアクセステスト"
        echo ""
        
        # Save distribution info for later use
        cat > backend/.env.dev.cloudfront << EOF
# Development Environment CloudFront Configuration
CLOUDFRONT_DISTRIBUTION_ID=$DISTRIBUTION_ID
CLOUDFRONT_DOMAIN_NAME=$DOMAIN_NAME
FRONTEND_URL=https://$DOMAIN_NAME
S3_FRONTEND_BUCKET=$S3_BUCKET
EOF
        
        print_success "CloudFront設定ファイルを作成しました: backend/.env.dev.cloudfront"
        
    else
        print_error "CloudFrontディストリビューションの作成に失敗しました"
        rm -f /tmp/cloudfront-config.json
        exit 1
    fi
}

# Test S3 bucket accessibility
test_s3_bucket() {
    print_status "S3バケットのアクセシビリティをテスト中..."
    
    # Check if bucket exists and is accessible
    if aws s3 ls "s3://$S3_BUCKET" > /dev/null 2>&1; then
        print_success "S3バケットにアクセス可能: $S3_BUCKET"
    else
        print_error "S3バケットにアクセスできません: $S3_BUCKET"
        exit 1
    fi
    
    # Check website configuration
    if aws s3api get-bucket-website --bucket "$S3_BUCKET" > /dev/null 2>&1; then
        print_success "S3バケットの静的ウェブサイトホスティングが設定されています"
    else
        print_warning "S3バケットの静的ウェブサイトホスティングが設定されていません"
        print_status "静的ウェブサイトホスティングを設定中..."
        
        aws s3 website "s3://$S3_BUCKET" \
            --index-document index.html \
            --error-document error.html
        
        print_success "静的ウェブサイトホスティングを設定しました"
    fi
}

# Check if CloudFront distribution already exists
check_existing_distribution() {
    print_status "既存のCloudFrontディストリビューションを確認中..."
    
    EXISTING_DISTRIBUTIONS=$(aws cloudfront list-distributions \
        --region us-east-1 \
        --query "DistributionList.Items[?contains(Comment, '${PROJECT_NAME} ${ENVIRONMENT}')].{Id:Id,DomainName:DomainName,Comment:Comment}" \
        --output json)
    
    if [ "$(echo "$EXISTING_DISTRIBUTIONS" | jq length)" -gt 0 ]; then
        print_warning "既存の開発環境CloudFrontディストリビューションが見つかりました:"
        echo "$EXISTING_DISTRIBUTIONS" | jq -r '.[] | "  ID: \(.Id), Domain: \(.DomainName)"'
        echo ""
        read -p "既存のディストリビューションを削除して新しく作成しますか？ (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            EXISTING_ID=$(echo "$EXISTING_DISTRIBUTIONS" | jq -r '.[0].Id')
            print_status "既存のディストリビューションを削除中: $EXISTING_ID"
            
            # Disable distribution first
            aws cloudfront get-distribution-config --id "$EXISTING_ID" --region us-east-1 > /tmp/existing-config.json
            ETAG=$(jq -r '.ETag' /tmp/existing-config.json)
            jq '.DistributionConfig.Enabled = false' /tmp/existing-config.json > /tmp/disable-config.json
            
            aws cloudfront update-distribution \
                --id "$EXISTING_ID" \
                --distribution-config file:///tmp/disable-config.json \
                --if-match "$ETAG" \
                --region us-east-1 > /dev/null
            
            print_status "ディストリビューションを無効化しました。デプロイ完了を待機中..."
            aws cloudfront wait distribution-deployed --id "$EXISTING_ID" --region us-east-1
            
            # Delete distribution
            aws cloudfront delete-distribution --id "$EXISTING_ID" --if-match "$ETAG" --region us-east-1
            print_success "既存のディストリビューションを削除しました"
            
            # Clean up temp files
            rm -f /tmp/existing-config.json /tmp/disable-config.json
        else
            print_status "既存のディストリビューションを保持します。処理を終了します。"
            exit 0
        fi
    else
        print_success "既存のディストリビューションは見つかりませんでした。新規作成を続行します。"
    fi
}

# Main function
main() {
    print_status "=== 開発環境CloudFrontディストリビューション作成開始 ==="
    echo ""
    
    # Check existing distributions
    check_existing_distribution
    echo ""
    
    # Test S3 bucket
    test_s3_bucket
    echo ""
    
    # Create CloudFront distribution
    create_cloudfront_distribution
}

# Show help
show_help() {
    echo "Create CloudFront Distribution for Development Environment"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  create    Create CloudFront distribution (default)"
    echo "  help      Show this help message"
    echo ""
    echo "Prerequisites:"
    echo "  - AWS CLI configured with appropriate permissions"
    echo "  - S3 bucket for frontend already exists"
    echo "  - jq command installed"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    # Check jq
    if ! command -v jq &> /dev/null; then
        print_error "jq コマンドが見つかりません"
        print_status "macOSの場合: brew install jq"
        exit 1
    fi
    
    # Check AWS CLI
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS認証情報が設定されていません"
        exit 1
    fi
}

# Handle command line arguments
case "${1:-create}" in
    "create")
        check_prerequisites
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