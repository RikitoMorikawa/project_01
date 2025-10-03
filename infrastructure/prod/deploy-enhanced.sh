#!/bin/bash

# CSR Lambda API System - Enhanced Production Deployment Script
# 本番環境用の包括的なデプロイメントスクリプト

set -euo pipefail

# 設定変数
PROJECT_NAME="csr-lambda-api"
ENVIRONMENT="prod"
AWS_REGION="ap-northeast-1"
STACK_PREFIX="${PROJECT_NAME}-${ENVIRONMENT}"

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

# 前提条件チェック
check_prerequisites() {
    log_info "前提条件をチェック中..."
    
    # AWS CLI チェック
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI がインストールされていません"
        exit 1
    fi
    
    # jq チェック
    if ! command -v jq &> /dev/null; then
        log_error "jq がインストールされていません"
        exit 1
    fi
    
    # AWS 認証情報チェック
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS 認証情報が設定されていません"
        exit 1
    fi
    
    # 必要なファイルの存在チェック
    local required_files=(
        "main.yaml"
        "database.yaml"
        "lambda-enhanced.yaml"
        "api.yaml"
        "frontend.yaml"
        "monitoring-enhanced.yaml"
        "waf-api.yaml"
        "parameters.json"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "必要なファイルが見つかりません: $file"
            exit 1
        fi
    done
    
    log_success "前提条件チェック完了"
}

# パラメータ検証
validate_parameters() {
    log_info "デプロイメントパラメータを検証中..."
    
    # parameters.json の検証
    if ! jq empty parameters.json 2>/dev/null; then
        log_error "parameters.json が無効な JSON 形式です"
        exit 1
    fi
    
    # 必須パラメータの確認
    local required_params=(
        "NotificationEmail"
        "LambdaCodeS3Bucket"
        "FrontendCodeS3Bucket"
    )
    
    for param in "${required_params[@]}"; do
        if [[ -z "${!param:-}" ]]; then
            log_error "必須パラメータが設定されていません: $param"
            log_info "環境変数として設定してください: export $param=value"
            exit 1
        fi
    done
    
    log_success "パラメータ検証完了"
}

# S3 バケット作成（必要に応じて）
create_s3_buckets() {
    log_info "S3 バケットを確認・作成中..."
    
    local buckets=("$LambdaCodeS3Bucket" "$FrontendCodeS3Bucket")
    
    for bucket in "${buckets[@]}"; do
        if ! aws s3 ls "s3://$bucket" &> /dev/null; then
            log_info "S3 バケットを作成中: $bucket"
            aws s3 mb "s3://$bucket" --region "$AWS_REGION"
            
            # バケットの暗号化を有効化
            aws s3api put-bucket-encryption \
                --bucket "$bucket" \
                --server-side-encryption-configuration '{
                    "Rules": [{
                        "ApplyServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256"
                        }
                    }]
                }'
            
            # パブリックアクセスをブロック
            aws s3api put-public-access-block \
                --bucket "$bucket" \
                --public-access-block-configuration \
                "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
        else
            log_info "S3 バケットが既に存在します: $bucket"
        fi
    done
    
    log_success "S3 バケット確認・作成完了"
}

# Lambda デプロイメントパッケージの作成とアップロード
build_and_upload_lambda() {
    log_info "Lambda デプロイメントパッケージを構築中..."
    
    # 一時ディレクトリ作成
    local temp_dir=$(mktemp -d)
    local package_dir="$temp_dir/lambda-package"
    mkdir -p "$package_dir"
    
    # バックエンドコードをコピー
    cp -r ../../backend/* "$package_dir/"
    
    # 依存関係をインストール
    cd "$package_dir"
    pip install -r requirements.txt -t .
    
    # 不要なファイルを削除
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # ZIP パッケージ作成
    zip -r lambda-deployment-package.zip . -x "*.git*" "*.DS_Store*" "venv/*" ".env*"
    
    # S3 にアップロード
    aws s3 cp lambda-deployment-package.zip "s3://$LambdaCodeS3Bucket/"
    
    # クリーンアップ
    cd - > /dev/null
    rm -rf "$temp_dir"
    
    log_success "Lambda デプロイメントパッケージのアップロード完了"
}

# フロントエンドビルドとアップロード
build_and_upload_frontend() {
    log_info "フロントエンドをビルド中..."
    
    cd ../../frontend
    
    # 依存関係インストール
    npm ci
    
    # 本番環境用ビルド
    npm run build
    
    # S3 にアップロード
    aws s3 sync out/ "s3://$FrontendCodeS3Bucket/" --delete
    
    cd - > /dev/null
    
    log_success "フロントエンドのビルドとアップロード完了"
}

# CloudFormation スタックのデプロイ
deploy_stack() {
    local stack_name="$1"
    local template_file="$2"
    local parameters_file="$3"
    local capabilities="${4:-}"
    
    log_info "CloudFormation スタックをデプロイ中: $stack_name"
    
    local deploy_cmd="aws cloudformation deploy \
        --template-file $template_file \
        --stack-name $stack_name \
        --parameter-overrides file://$parameters_file \
        --region $AWS_REGION \
        --no-fail-on-empty-changeset"
    
    if [[ -n "$capabilities" ]]; then
        deploy_cmd="$deploy_cmd --capabilities $capabilities"
    fi
    
    # タグを追加
    deploy_cmd="$deploy_cmd --tags \
        Project=$PROJECT_NAME \
        Environment=$ENVIRONMENT \
        DeployedBy=$(whoami) \
        DeployedAt=$(date -u +%Y-%m-%dT%H:%M:%SZ) \
        CostCenter=Production"
    
    if eval "$deploy_cmd"; then
        log_success "スタックデプロイ完了: $stack_name"
    else
        log_error "スタックデプロイ失敗: $stack_name"
        return 1
    fi
}

# スタックの状態確認
wait_for_stack() {
    local stack_name="$1"
    local max_wait_time="${2:-1800}"  # 30分
    
    log_info "スタックの完了を待機中: $stack_name"
    
    aws cloudformation wait stack-deploy-complete \
        --stack-name "$stack_name" \
        --region "$AWS_REGION" \
        --cli-read-timeout "$max_wait_time" \
        --cli-connect-timeout 60
    
    if [[ $? -eq 0 ]]; then
        log_success "スタック完了: $stack_name"
    else
        log_error "スタック完了待機タイムアウト: $stack_name"
        return 1
    fi
}

# デプロイメント後の検証
validate_deployment() {
    log_info "デプロイメント検証を実行中..."
    
    # API Gateway エンドポイントの取得
    local api_url=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_PREFIX}-api" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text)
    
    if [[ -n "$api_url" ]]; then
        log_info "API Gateway URL: $api_url"
        
        # ヘルスチェック
        if curl -f -s "${api_url}/health" > /dev/null; then
            log_success "API ヘルスチェック成功"
        else
            log_warning "API ヘルスチェック失敗（初期化中の可能性があります）"
        fi
    fi
    
    # CloudFront ディストリビューション URL の取得
    local cloudfront_url=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_PREFIX}-frontend" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
        --output text)
    
    if [[ -n "$cloudfront_url" ]]; then
        log_info "CloudFront URL: $cloudfront_url"
    fi
    
    # Lambda 関数の確認
    local lambda_function=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_PREFIX}-lambda-enhanced" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`EnhancedLambdaFunctionName`].OutputValue' \
        --output text)
    
    if [[ -n "$lambda_function" ]]; then
        log_info "Lambda 関数: $lambda_function"
        
        # Lambda 関数の状態確認
        local function_state=$(aws lambda get-function \
            --function-name "$lambda_function" \
            --region "$AWS_REGION" \
            --query 'Configuration.State' \
            --output text)
        
        if [[ "$function_state" == "Active" ]]; then
            log_success "Lambda 関数がアクティブ状態です"
        else
            log_warning "Lambda 関数の状態: $function_state"
        fi
    fi
    
    log_success "デプロイメント検証完了"
}

# ロールバック機能
rollback_deployment() {
    log_warning "デプロイメントのロールバックを開始します..."
    
    local stacks=(
        "${STACK_PREFIX}-monitoring-enhanced"
        "${STACK_PREFIX}-waf"
        "${STACK_PREFIX}-frontend"
        "${STACK_PREFIX}-api"
        "${STACK_PREFIX}-lambda-enhanced"
        "${STACK_PREFIX}-database"
        "${STACK_PREFIX}-main"
    )
    
    for stack in "${stacks[@]}"; do
        if aws cloudformation describe-stacks --stack-name "$stack" --region "$AWS_REGION" &> /dev/null; then
            log_info "スタックを削除中: $stack"
            aws cloudformation delete-stack --stack-name "$stack" --region "$AWS_REGION"
        fi
    done
    
    log_warning "ロールバック完了（手動でリソースの削除を確認してください）"
}

# メイン実行関数
main() {
    log_info "=== CSR Lambda API System - Enhanced Production Deployment ==="
    log_info "プロジェクト: $PROJECT_NAME"
    log_info "環境: $ENVIRONMENT"
    log_info "リージョン: $AWS_REGION"
    log_info "デプロイ開始時刻: $(date)"
    
    # 前提条件チェック
    check_prerequisites
    
    # パラメータ検証
    validate_parameters
    
    # 確認プロンプト
    echo
    log_warning "本番環境へのデプロイを実行します。続行しますか？ (y/N)"
    read -r confirmation
    if [[ ! "$confirmation" =~ ^[Yy]$ ]]; then
        log_info "デプロイメントがキャンセルされました"
        exit 0
    fi
    
    # デプロイメント実行
    trap rollback_deployment ERR
    
    # S3 バケット準備
    create_s3_buckets
    
    # アプリケーションビルド
    build_and_upload_lambda
    build_and_upload_frontend
    
    # インフラストラクチャデプロイ（順序重要）
    log_info "=== インフラストラクチャデプロイ開始 ==="
    
    # 1. メインインフラ（VPC、ネットワーク）
    deploy_stack "${STACK_PREFIX}-main" "main.yaml" "parameters.json" "CAPABILITY_NAMED_IAM"
    wait_for_stack "${STACK_PREFIX}-main"
    
    # 2. データベース
    deploy_stack "${STACK_PREFIX}-database" "database.yaml" "parameters.json" "CAPABILITY_NAMED_IAM"
    wait_for_stack "${STACK_PREFIX}-database"
    
    # 3. Enhanced Lambda
    deploy_stack "${STACK_PREFIX}-lambda-enhanced" "lambda-enhanced.yaml" "parameters.json" "CAPABILITY_NAMED_IAM"
    wait_for_stack "${STACK_PREFIX}-lambda-enhanced"
    
    # 4. API Gateway
    deploy_stack "${STACK_PREFIX}-api" "api.yaml" "parameters.json" "CAPABILITY_NAMED_IAM"
    wait_for_stack "${STACK_PREFIX}-api"
    
    # 5. WAF
    deploy_stack "${STACK_PREFIX}-waf" "waf-api.yaml" "parameters.json"
    wait_for_stack "${STACK_PREFIX}-waf"
    
    # 6. フロントエンド
    deploy_stack "${STACK_PREFIX}-frontend" "frontend.yaml" "parameters.json"
    wait_for_stack "${STACK_PREFIX}-frontend"
    
    # 7. Enhanced Monitoring
    deploy_stack "${STACK_PREFIX}-monitoring-enhanced" "monitoring-enhanced.yaml" "parameters.json" "CAPABILITY_NAMED_IAM"
    wait_for_stack "${STACK_PREFIX}-monitoring-enhanced"
    
    log_info "=== インフラストラクチャデプロイ完了 ==="
    
    # デプロイメント検証
    validate_deployment
    
    # 完了メッセージ
    echo
    log_success "=== Enhanced Production Deployment 完了 ==="
    log_success "デプロイ完了時刻: $(date)"
    log_info "次のステップ:"
    log_info "1. CloudWatch ダッシュボードで監視状況を確認"
    log_info "2. アラート通知の設定を確認"
    log_info "3. パフォーマンステストの実行"
    log_info "4. セキュリティテストの実行"
    log_info "5. ドキュメントの更新"
    
    # 重要な URL を表示
    echo
    log_info "=== 重要な URL ==="
    aws cloudformation describe-stacks \
        --region "$AWS_REGION" \
        --query 'Stacks[?starts_with(StackName, `'${STACK_PREFIX}'`)].Outputs[?contains(OutputKey, `Url`) || contains(OutputKey, `Endpoint`)].{Stack:@[0].StackName,Key:OutputKey,Value:OutputValue}' \
        --output table
}

# スクリプト実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi