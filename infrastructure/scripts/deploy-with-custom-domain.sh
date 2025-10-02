#!/bin/bash

# CSR Lambda API システム - カスタムドメイン付きデプロイメントスクリプト
# 使用方法: ./deploy-with-custom-domain.sh <environment> <domain-name> <certificate-arn> <hosted-zone-id>

set -e

# パラメータチェック
if [ $# -lt 1 ]; then
    echo "使用方法: $0 <environment> [domain-name] [certificate-arn] [hosted-zone-id]"
    echo "例:"
    echo "  $0 dev"
    echo "  $0 staging staging.example.com arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012 Z1D633PJN98FT9"
    echo "  $0 prod www.example.com arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012 Z1D633PJN98FT9"
    exit 1
fi

ENVIRONMENT=$1
DOMAIN_NAME=${2:-""}
CERTIFICATE_ARN=${3:-""}
HOSTED_ZONE_ID=${4:-""}
PROJECT_NAME="csr-lambda-api"
REGION="ap-northeast-1"

# 環境別設定
case $ENVIRONMENT in
    "dev")
        CLOUDFRONT_ENABLED="false"
        ;;
    "staging")
        CLOUDFRONT_ENABLED="true"
        ;;
    "prod")
        CLOUDFRONT_ENABLED="true"
        ;;
    *)
        echo "エラー: 無効な環境名です。dev, staging, prod のいずれかを指定してください。"
        exit 1
        ;;
esac

echo "=== CSR Lambda API システム デプロイメント ==="
echo "環境: $ENVIRONMENT"
echo "プロジェクト名: $PROJECT_NAME"
echo "リージョン: $REGION"
echo "CloudFront有効: $CLOUDFRONT_ENABLED"

if [ -n "$DOMAIN_NAME" ]; then
    echo "カスタムドメイン: $DOMAIN_NAME"
    echo "SSL証明書ARN: $CERTIFICATE_ARN"
    echo "ホストゾーンID: $HOSTED_ZONE_ID"
fi

echo ""

# パラメータファイルの確認
PARAMS_FILE="infrastructure/${ENVIRONMENT}/parameters.json"
if [ ! -f "$PARAMS_FILE" ]; then
    echo "エラー: パラメータファイルが見つかりません: $PARAMS_FILE"
    exit 1
fi

# CloudFormation パラメータの構築
build_parameters() {
    local template_type=$1
    local params=""
    
    # 基本パラメータ
    params="ParameterKey=ProjectName,ParameterValue=$PROJECT_NAME"
    params="$params ParameterKey=Environment,ParameterValue=$ENVIRONMENT"
    
    # フロントエンド固有のパラメータ
    if [ "$template_type" = "frontend" ]; then
        params="$params ParameterKey=CloudFrontEnabled,ParameterValue=$CLOUDFRONT_ENABLED"
        
        if [ -n "$DOMAIN_NAME" ]; then
            params="$params ParameterKey=CustomDomainName,ParameterValue=$DOMAIN_NAME"
        fi
        
        if [ -n "$CERTIFICATE_ARN" ]; then
            params="$params ParameterKey=SSLCertificateArn,ParameterValue=$CERTIFICATE_ARN"
        fi
        
        if [ -n "$HOSTED_ZONE_ID" ]; then
            params="$params ParameterKey=HostedZoneId,ParameterValue=$HOSTED_ZONE_ID"
        fi
    fi
    
    echo "$params"
}

# スタックのデプロイ
deploy_stack() {
    local stack_name=$1
    local template_file=$2
    local template_type=$3
    
    echo "--- $stack_name のデプロイを開始 ---"
    
    local parameters=$(build_parameters "$template_type")
    
    # スタックの存在確認
    if aws cloudformation describe-stacks --stack-name "$stack_name" --region "$REGION" >/dev/null 2>&1; then
        echo "スタック $stack_name を更新中..."
        aws cloudformation update-stack \
            --stack-name "$stack_name" \
            --template-body "file://$template_file" \
            --parameters $parameters \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "$REGION"
        
        echo "スタック更新の完了を待機中..."
        aws cloudformation wait stack-update-complete \
            --stack-name "$stack_name" \
            --region "$REGION"
    else
        echo "スタック $stack_name を作成中..."
        aws cloudformation create-stack \
            --stack-name "$stack_name" \
            --template-body "file://$template_file" \
            --parameters $parameters \
            --capabilities CAPABILITY_NAMED_IAM \
            --region "$REGION"
        
        echo "スタック作成の完了を待機中..."
        aws cloudformation wait stack-create-complete \
            --stack-name "$stack_name" \
            --region "$REGION"
    fi
    
    echo "✅ $stack_name のデプロイが完了しました"
    echo ""
}

# メインインフラストラクチャのデプロイ
echo "=== インフラストラクチャのデプロイを開始 ==="

# 1. VPC とネットワーク
if [ -f "infrastructure/${ENVIRONMENT}/main.yaml" ]; then
    deploy_stack "${PROJECT_NAME}-${ENVIRONMENT}-main" "infrastructure/${ENVIRONMENT}/main.yaml" "main"
fi

# 2. データベース
if [ -f "infrastructure/${ENVIRONMENT}/database.yaml" ]; then
    deploy_stack "${PROJECT_NAME}-${ENVIRONMENT}-database" "infrastructure/${ENVIRONMENT}/database.yaml" "database"
fi

# 3. API Gateway と Lambda
if [ -f "infrastructure/${ENVIRONMENT}/api.yaml" ]; then
    deploy_stack "${PROJECT_NAME}-${ENVIRONMENT}-api" "infrastructure/${ENVIRONMENT}/api.yaml" "api"
fi

# 4. フロントエンド（S3 + CloudFront）
if [ -f "infrastructure/${ENVIRONMENT}/frontend.yaml" ]; then
    deploy_stack "${PROJECT_NAME}-${ENVIRONMENT}-frontend" "infrastructure/${ENVIRONMENT}/frontend.yaml" "frontend"
fi

# デプロイ結果の表示
echo "=== デプロイ結果 ==="

# フロントエンドURLの取得
FRONTEND_URL=$(aws cloudformation describe-stacks \
    --stack-name "${PROJECT_NAME}-${ENVIRONMENT}-frontend" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendURL'].OutputValue" \
    --output text 2>/dev/null || echo "取得できませんでした")

# API Gateway URLの取得
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "${PROJECT_NAME}-${ENVIRONMENT}-api" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" \
    --output text 2>/dev/null || echo "取得できませんでした")

echo "フロントエンドURL: $FRONTEND_URL"
echo "API Gateway URL: $API_URL"

if [ -n "$DOMAIN_NAME" ]; then
    echo "カスタムドメイン: https://$DOMAIN_NAME"
    echo ""
    echo "注意: カスタムドメインが有効になるまで数分かかる場合があります。"
    echo "DNS の伝播には最大48時間かかる場合があります。"
fi

echo ""
echo "🎉 デプロイが正常に完了しました！"