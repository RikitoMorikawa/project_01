#!/bin/bash

# CSR Lambda API System - ビルドとデプロイスクリプト
# フロントエンドとバックエンドのビルド、パッケージング、デプロイを実行

set -e

# 設定
PROJECT_NAME="csr-lambda-api"
REGION="ap-northeast-1"

# カラー出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 使用方法を表示
usage() {
    echo "使用方法: $0 <environment> [options]"
    echo ""
    echo "環境:"
    echo "  dev       開発環境"
    echo "  staging   ステージング環境"
    echo "  prod      本番環境"
    echo ""
    echo "オプション:"
    echo "  --frontend-only    フロントエンドのみビルド・デプロイ"
    echo "  --backend-only     バックエンドのみビルド・デプロイ"
    echo "  --build-only       ビルドのみ実行（デプロイしない）"
    echo "  --deploy-only      デプロイのみ実行（ビルドしない）"
    echo "  --help            このヘルプを表示"
    exit 1
}

# 環境変数の設定
setup_environment() {
    local env="$1"
    
    export ENVIRONMENT="$env"
    export STACK_PREFIX="${PROJECT_NAME}-${env}"
    export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    
    # 環境別設定
    case "$env" in
        "dev")
            export LAMBDA_MEMORY_SIZE=128
            export LAMBDA_TIMEOUT=30
            ;;
        "staging")
            export LAMBDA_MEMORY_SIZE=512
            export LAMBDA_TIMEOUT=60
            ;;
        "prod")
            export LAMBDA_MEMORY_SIZE=1024
            export LAMBDA_TIMEOUT=60
            ;;
        *)
            log_error "無効な環境: $env"
            usage
            ;;
    esac
    
    log_info "環境設定完了: $env"
    log_info "AWS Account ID: $AWS_ACCOUNT_ID"
    log_info "Stack Prefix: $STACK_PREFIX"
}

# バックエンドのビルド
build_backend() {
    log_info "=== バックエンドのビルド開始 ==="
    
    # 作業ディレクトリの作成
    BUILD_DIR="build"
    BACKEND_BUILD_DIR="$BUILD_DIR/backend"
    
    rm -rf "$BACKEND_BUILD_DIR"
    mkdir -p "$BACKEND_BUILD_DIR"
    
    # バックエンドファイルのコピー
    log_info "バックエンドファイルをコピー中..."
    cp -r backend/app "$BACKEND_BUILD_DIR/"
    cp backend/lambda_handler.py "$BACKEND_BUILD_DIR/"
    cp backend/requirements.txt "$BACKEND_BUILD_DIR/"
    
    # 依存関係のインストール
    log_info "Python依存関係をインストール中..."
    cd "$BACKEND_BUILD_DIR"
    
    # 仮想環境を作成してパッケージをインストール
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt -t .
    deactivate
    
    # 不要なファイルを削除
    rm -rf venv
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    
    # デプロイメントパッケージの作成
    log_info "Lambdaデプロイメントパッケージを作成中..."
    zip -r "../lambda-deployment-package.zip" . -x "*.git*" "*.DS_Store*" "tests/*" "*.pytest_cache*"
    
    cd - >/dev/null
    
    log_success "バックエンドのビルドが完了しました"
}

# フロントエンドのビルド
build_frontend() {
    log_info "=== フロントエンドのビルド開始 ==="
    
    cd frontend
    
    # 依存関係のインストール
    log_info "Node.js依存関係をインストール中..."
    npm ci
    
    # 環境変数の設定
    log_info "環境変数を設定中..."
    
    # API Gateway URLを取得
    API_URL=""
    if aws cloudformation describe-stacks --stack-name "${STACK_PREFIX}-api" --region "$REGION" >/dev/null 2>&1; then
        API_URL=$(aws cloudformation describe-stacks \
            --stack-name "${STACK_PREFIX}-api" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
            --output text 2>/dev/null || echo "")
    fi
    
    # 環境変数ファイルの作成
    cat > .env.production << EOF
NEXT_PUBLIC_API_URL=${API_URL}
NEXT_PUBLIC_ENVIRONMENT=${ENVIRONMENT}
NEXT_PUBLIC_AWS_REGION=${REGION}
EOF
    
    # ビルドの実行
    log_info "Next.jsアプリケーションをビルド中..."
    npm run build
    
    cd - >/dev/null
    
    log_success "フロントエンドのビルドが完了しました"
}

# バックエンドのデプロイ
deploy_backend() {
    log_info "=== バックエンドのデプロイ開始 ==="
    
    # S3バケットの設定
    LAMBDA_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-lambda-deployments-${AWS_ACCOUNT_ID}"
    LAMBDA_KEY="lambda-deployment-package-$(date +%Y%m%d-%H%M%S).zip"
    
    # S3バケットが存在しない場合は作成
    if ! aws s3 ls "s3://$LAMBDA_BUCKET" --region "$REGION" >/dev/null 2>&1; then
        log_info "Lambda デプロイメント用 S3 バケットを作成中: $LAMBDA_BUCKET"
        aws s3 mb "s3://$LAMBDA_BUCKET" --region "$REGION"
        aws s3api put-bucket-versioning --bucket "$LAMBDA_BUCKET" --versioning-configuration Status=Enabled --region "$REGION"
        
        # バケットポリシーの設定（必要に応じて）
        cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowLambdaServiceAccess",
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${LAMBDA_BUCKET}/*"
        }
    ]
}
EOF
        aws s3api put-bucket-policy --bucket "$LAMBDA_BUCKET" --policy file://bucket-policy.json --region "$REGION"
        rm bucket-policy.json
    fi
    
    # デプロイメントパッケージをS3にアップロード
    log_info "Lambdaパッケージを S3 にアップロード中..."
    aws s3 cp "build/lambda-deployment-package.zip" "s3://$LAMBDA_BUCKET/$LAMBDA_KEY" --region "$REGION"
    
    # Lambda関数の更新
    if aws lambda get-function --function-name "${STACK_PREFIX}-api-function" --region "$REGION" >/dev/null 2>&1; then
        log_info "Lambda関数を更新中..."
        aws lambda update-function-code \
            --function-name "${STACK_PREFIX}-api-function" \
            --s3-bucket "$LAMBDA_BUCKET" \
            --s3-key "$LAMBDA_KEY" \
            --region "$REGION"
        
        # 関数の更新完了を待機
        aws lambda wait function-updated \
            --function-name "${STACK_PREFIX}-api-function" \
            --region "$REGION"
    else
        log_warning "Lambda関数が見つかりません。インフラストラクチャを先にデプロイしてください。"
    fi
    
    log_success "バックエンドのデプロイが完了しました"
}

# フロントエンドのデプロイ
deploy_frontend() {
    log_info "=== フロントエンドのデプロイ開始 ==="
    
    # S3バケット名を取得
    FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_PREFIX}-frontend" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`FrontendS3BucketName`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [[ -z "$FRONTEND_BUCKET" ]]; then
        log_error "フロントエンド S3 バケットが見つかりません。インフラストラクチャを先にデプロイしてください。"
        exit 1
    fi
    
    # 既存のファイルを削除
    log_info "既存のファイルを削除中..."
    aws s3 rm "s3://$FRONTEND_BUCKET" --recursive --region "$REGION" || true
    
    # ビルドファイルをS3にアップロード
    log_info "フロントエンドファイルを S3 にアップロード中..."
    cd frontend
    aws s3 sync out/ "s3://$FRONTEND_BUCKET" \
        --region "$REGION" \
        --delete \
        --cache-control "public, max-age=31536000" \
        --exclude "*.html" \
        --exclude "*.json"
    
    # HTMLファイルは短いキャッシュ時間で設定
    aws s3 sync out/ "s3://$FRONTEND_BUCKET" \
        --region "$REGION" \
        --cache-control "public, max-age=300" \
        --include "*.html" \
        --include "*.json"
    
    cd - >/dev/null
    
    # CloudFrontの無効化（有効な場合）
    CLOUDFRONT_DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_PREFIX}-frontend" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$CLOUDFRONT_DISTRIBUTION_ID" && "$CLOUDFRONT_DISTRIBUTION_ID" != "None" ]]; then
        log_info "CloudFrontキャッシュを無効化中..."
        aws cloudfront create-invalidation \
            --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
            --paths "/*" \
            --region "$REGION" >/dev/null
    fi
    
    log_success "フロントエンドのデプロイが完了しました"
}

# インフラストラクチャのデプロイ
deploy_infrastructure() {
    log_info "=== インフラストラクチャのデプロイ開始 ==="
    
    cd "infrastructure/$ENVIRONMENT"
    
    # デプロイスクリプトの実行
    if [[ -f "deploy.sh" ]]; then
        chmod +x deploy.sh
        ./deploy.sh
    else
        log_error "デプロイスクリプトが見つかりません: infrastructure/$ENVIRONMENT/deploy.sh"
        exit 1
    fi
    
    cd - >/dev/null
    
    log_success "インフラストラクチャのデプロイが完了しました"
}

# デプロイメント情報の表示
show_deployment_info() {
    log_info "=== デプロイメント情報 ==="
    
    # API Gateway URL
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_PREFIX}-api" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text 2>/dev/null || echo "取得できませんでした")
    echo "API Gateway URL: $API_URL"
    
    # フロントエンド URL
    if [[ "$ENVIRONMENT" == "dev" ]]; then
        # 開発環境はS3 Website URL
        FRONTEND_URL=$(aws cloudformation describe-stacks \
            --stack-name "${STACK_PREFIX}-frontend" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`FrontendS3BucketWebsiteURL`].OutputValue' \
            --output text 2>/dev/null || echo "取得できませんでした")
        echo "Frontend URL (S3): $FRONTEND_URL"
    else
        # ステージング・本番環境はCloudFront URL
        CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
            --stack-name "${STACK_PREFIX}-frontend" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionDomainName`].OutputValue' \
            --output text 2>/dev/null || echo "取得できませんでした")
        echo "Frontend URL (CloudFront): https://$CLOUDFRONT_URL"
    fi
    
    # データベースエンドポイント
    DB_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_PREFIX}-database" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`DatabaseClusterEndpoint`].OutputValue' \
        --output text 2>/dev/null || echo "取得できませんでした")
    echo "Database Endpoint: $DB_ENDPOINT"
}

# メイン処理
main() {
    # 引数の解析
    if [[ $# -eq 0 ]]; then
        usage
    fi
    
    ENVIRONMENT=""
    FRONTEND_ONLY=false
    BACKEND_ONLY=false
    BUILD_ONLY=false
    DEPLOY_ONLY=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            dev|staging|prod)
                ENVIRONMENT="$1"
                shift
                ;;
            --frontend-only)
                FRONTEND_ONLY=true
                shift
                ;;
            --backend-only)
                BACKEND_ONLY=true
                shift
                ;;
            --build-only)
                BUILD_ONLY=true
                shift
                ;;
            --deploy-only)
                DEPLOY_ONLY=true
                shift
                ;;
            --help)
                usage
                ;;
            *)
                log_error "不明なオプション: $1"
                usage
                ;;
        esac
    done
    
    if [[ -z "$ENVIRONMENT" ]]; then
        log_error "環境を指定してください"
        usage
    fi
    
    # 環境設定
    setup_environment "$ENVIRONMENT"
    
    # AWS CLI の設定確認
    if ! aws sts get-caller-identity --region "$REGION" >/dev/null 2>&1; then
        log_error "AWS CLI が正しく設定されていません。認証情報を確認してください。"
        exit 1
    fi
    
    log_info "=== CSR Lambda API System - ビルドとデプロイ開始 ==="
    log_info "環境: $ENVIRONMENT"
    
    # ビルド処理
    if [[ "$DEPLOY_ONLY" != true ]]; then
        if [[ "$BACKEND_ONLY" != true ]]; then
            build_frontend
        fi
        
        if [[ "$FRONTEND_ONLY" != true ]]; then
            build_backend
        fi
    fi
    
    # デプロイ処理
    if [[ "$BUILD_ONLY" != true ]]; then
        # インフラストラクチャのデプロイ（必要な場合）
        if [[ "$FRONTEND_ONLY" != true && "$BACKEND_ONLY" != true ]]; then
            deploy_infrastructure
        fi
        
        if [[ "$BACKEND_ONLY" != true ]]; then
            deploy_frontend
        fi
        
        if [[ "$FRONTEND_ONLY" != true ]]; then
            deploy_backend
        fi
        
        # デプロイメント情報の表示
        show_deployment_info
    fi
    
    log_success "=== ビルドとデプロイが完了しました ==="
}

# スクリプト実行
main "$@"