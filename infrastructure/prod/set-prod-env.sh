#!/bin/bash

# CSR Lambda API System - Production Environment Setup Script
# 本番環境用の環境変数設定スクリプト

set -euo pipefail

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

# 設定値の検証
validate_email() {
    local email="$1"
    if [[ ! "$email" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
        log_error "無効なメールアドレス形式です: $email"
        return 1
    fi
}

validate_s3_bucket_name() {
    local bucket="$1"
    if [[ ! "$bucket" =~ ^[a-z0-9][a-z0-9-]*[a-z0-9]$ ]] || [[ ${#bucket} -lt 3 ]] || [[ ${#bucket} -gt 63 ]]; then
        log_error "無効な S3 バケット名です: $bucket"
        log_info "S3 バケット名は 3-63 文字で、小文字、数字、ハイフンのみ使用可能です"
        return 1
    fi
}

validate_url() {
    local url="$1"
    if [[ -n "$url" ]] && [[ ! "$url" =~ ^https?:// ]]; then
        log_error "無効な URL 形式です: $url"
        return 1
    fi
}

# 対話的な設定収集
collect_configuration() {
    log_info "=== CSR Lambda API System - 本番環境設定 ==="
    echo
    
    # 必須設定
    log_info "必須設定を入力してください:"
    
    # 通知メールアドレス
    while true; do
        read -p "アラート通知用メールアドレス: " NOTIFICATION_EMAIL
        if validate_email "$NOTIFICATION_EMAIL"; then
            break
        fi
    done
    
    # S3 バケット名（Lambda コード用）
    while true; do
        read -p "Lambda コード用 S3 バケット名 [csr-lambda-api-prod-lambda-code]: " LAMBDA_CODE_S3_BUCKET
        LAMBDA_CODE_S3_BUCKET=${LAMBDA_CODE_S3_BUCKET:-csr-lambda-api-prod-lambda-code}
        if validate_s3_bucket_name "$LAMBDA_CODE_S3_BUCKET"; then
            break
        fi
    done
    
    # S3 バケット名（フロントエンド用）
    while true; do
        read -p "フロントエンド用 S3 バケット名 [csr-lambda-api-prod-frontend-code]: " FRONTEND_CODE_S3_BUCKET
        FRONTEND_CODE_S3_BUCKET=${FRONTEND_CODE_S3_BUCKET:-csr-lambda-api-prod-frontend-code}
        if validate_s3_bucket_name "$FRONTEND_CODE_S3_BUCKET"; then
            break
        fi
    done
    
    echo
    log_info "オプション設定を入力してください（空白で省略可能）:"
    
    # Slack Webhook URL
    while true; do
        read -p "Slack Webhook URL（オプション）: " SLACK_WEBHOOK_URL
        if [[ -z "$SLACK_WEBHOOK_URL" ]] || validate_url "$SLACK_WEBHOOK_URL"; then
            break
        fi
    done
    
    # PagerDuty Integration Key
    read -p "PagerDuty Integration Key（オプション）: " PAGERDUTY_INTEGRATION_KEY
    
    # OpsGenie API Key
    read -p "OpsGenie API Key（オプション）: " OPSGENIE_API_KEY
    
    # カスタムドメイン設定
    read -p "カスタムドメイン名（オプション）: " CUSTOM_DOMAIN_NAME
    
    # SSL 証明書 ARN
    if [[ -n "$CUSTOM_DOMAIN_NAME" ]]; then
        read -p "SSL 証明書 ARN（カスタムドメイン用）: " SSL_CERTIFICATE_ARN
    fi
    
    echo
    log_info "パフォーマンス設定:"
    
    # Lambda メモリサイズ
    read -p "Lambda メモリサイズ (MB) [1024]: " LAMBDA_MEMORY_SIZE
    LAMBDA_MEMORY_SIZE=${LAMBDA_MEMORY_SIZE:-1024}
    
    # Provisioned Concurrency
    read -p "Lambda Provisioned Concurrency 初期値 [10]: " LAMBDA_PROVISIONED_CONCURRENCY
    LAMBDA_PROVISIONED_CONCURRENCY=${LAMBDA_PROVISIONED_CONCURRENCY:-10}
    
    # データベースインスタンスクラス
    read -p "データベースインスタンスクラス [db.t3.medium]: " DATABASE_INSTANCE_CLASS
    DATABASE_INSTANCE_CLASS=${DATABASE_INSTANCE_CLASS:-db.t3.medium}
    
    echo
    log_info "セキュリティ設定:"
    
    # WAF レート制限
    read -p "WAF レート制限（リクエスト/分） [2000]: " WAF_RATE_LIMIT
    WAF_RATE_LIMIT=${WAF_RATE_LIMIT:-2000}
    
    # ブロック対象国
    read -p "WAF ブロック対象国（カンマ区切り） [CN,RU]: " WAF_BLOCKED_COUNTRIES
    WAF_BLOCKED_COUNTRIES=${WAF_BLOCKED_COUNTRIES:-CN,RU}
}

# 環境変数の設定
set_environment_variables() {
    log_info "環境変数を設定中..."
    
    # 必須環境変数
    export PROJECT_NAME="csr-lambda-api"
    export ENVIRONMENT="prod"
    export AWS_REGION="ap-northeast-1"
    export AWS_DEFAULT_REGION="ap-northeast-1"
    
    # ユーザー入力値
    export NotificationEmail="$NOTIFICATION_EMAIL"
    export LambdaCodeS3Bucket="$LAMBDA_CODE_S3_BUCKET"
    export FrontendCodeS3Bucket="$FRONTEND_CODE_S3_BUCKET"
    export SlackWebhookUrl="$SLACK_WEBHOOK_URL"
    export PagerDutyIntegrationKey="$PAGERDUTY_INTEGRATION_KEY"
    export OpsGenieApiKey="$OPSGENIE_API_KEY"
    export CustomDomainName="$CUSTOM_DOMAIN_NAME"
    export SSLCertificateArn="$SSL_CERTIFICATE_ARN"
    export LambdaMemorySize="$LAMBDA_MEMORY_SIZE"
    export LambdaProvisionedConcurrency="$LAMBDA_PROVISIONED_CONCURRENCY"
    export DatabaseInstanceClass="$DATABASE_INSTANCE_CLASS"
    export WAFRateLimit="$WAF_RATE_LIMIT"
    export WAFBlockedCountries="$WAF_BLOCKED_COUNTRIES"
    
    # 固定設定値
    export LambdaTimeout="30"
    export LambdaReservedConcurrency="500"
    export DatabaseMultiAZ="true"
    export DatabaseReadReplica="true"
    export CloudFrontEnabled="true"
    export WAFEnabled="true"
    export EnableVPCFlowLogs="true"
    export EnableCloudTrail="true"
    export BackupEnabled="true"
    export DeletionProtection="true"
    export StorageEncrypted="true"
    
    log_success "環境変数設定完了"
}

# 設定ファイルの更新
update_parameters_file() {
    log_info "parameters.json を更新中..."
    
    local params_file="parameters.json"
    local temp_file=$(mktemp)
    
    # JSON ファイルを更新
    jq --arg email "$NOTIFICATION_EMAIL" \
       --arg lambdaBucket "$LAMBDA_CODE_S3_BUCKET" \
       --arg frontendBucket "$FRONTEND_CODE_S3_BUCKET" \
       --arg slackUrl "$SLACK_WEBHOOK_URL" \
       --arg pagerdutyKey "$PAGERDUTY_INTEGRATION_KEY" \
       --arg opsgenieKey "$OPSGENIE_API_KEY" \
       --arg customDomain "$CUSTOM_DOMAIN_NAME" \
       --arg sslCert "$SSL_CERTIFICATE_ARN" \
       --argjson lambdaMemory "$LAMBDA_MEMORY_SIZE" \
       --argjson provisionedConcurrency "$LAMBDA_PROVISIONED_CONCURRENCY" \
       --arg dbInstanceClass "$DATABASE_INSTANCE_CLASS" \
       --argjson wafRateLimit "$WAF_RATE_LIMIT" \
       --arg wafBlockedCountries "$WAF_BLOCKED_COUNTRIES" \
       '.NotificationEmail = $email |
        .LambdaCodeS3Bucket = $lambdaBucket |
        .FrontendCodeS3Bucket = $frontendBucket |
        .SlackWebhookUrl = $slackUrl |
        .PagerDutyIntegrationKey = $pagerdutyKey |
        .OpsGenieApiKey = $opsgenieKey |
        .CustomDomainName = $customDomain |
        .SSLCertificateArn = $sslCert |
        .LambdaMemorySize = $lambdaMemory |
        .LambdaProvisionedConcurrency = $provisionedConcurrency |
        .DatabaseInstanceClass = $dbInstanceClass |
        .WAFRateLimitPerMinute = $wafRateLimit |
        .WAFBlockedCountries = ($wafBlockedCountries | split(","))' \
       "$params_file" > "$temp_file"
    
    mv "$temp_file" "$params_file"
    
    log_success "parameters.json 更新完了"
}

# 環境変数エクスポートファイルの作成
create_env_export_file() {
    log_info "環境変数エクスポートファイルを作成中..."
    
    local env_file=".env.prod.export"
    
    cat > "$env_file" << EOF
#!/bin/bash
# CSR Lambda API System - Production Environment Variables
# このファイルを source することで環境変数を設定できます
# Usage: source .env.prod.export

# プロジェクト設定
export PROJECT_NAME="csr-lambda-api"
export ENVIRONMENT="prod"
export AWS_REGION="ap-northeast-1"
export AWS_DEFAULT_REGION="ap-northeast-1"

# 通知設定
export NotificationEmail="$NOTIFICATION_EMAIL"
export SlackWebhookUrl="$SLACK_WEBHOOK_URL"
export PagerDutyIntegrationKey="$PAGERDUTY_INTEGRATION_KEY"
export OpsGenieApiKey="$OPSGENIE_API_KEY"

# S3 バケット設定
export LambdaCodeS3Bucket="$LAMBDA_CODE_S3_BUCKET"
export FrontendCodeS3Bucket="$FRONTEND_CODE_S3_BUCKET"

# ドメイン設定
export CustomDomainName="$CUSTOM_DOMAIN_NAME"
export SSLCertificateArn="$SSL_CERTIFICATE_ARN"

# Lambda 設定
export LambdaMemorySize="$LAMBDA_MEMORY_SIZE"
export LambdaTimeout="30"
export LambdaReservedConcurrency="500"
export LambdaProvisionedConcurrency="$LAMBDA_PROVISIONED_CONCURRENCY"

# データベース設定
export DatabaseInstanceClass="$DATABASE_INSTANCE_CLASS"
export DatabaseMultiAZ="true"
export DatabaseReadReplica="true"

# セキュリティ設定
export WAFEnabled="true"
export WAFRateLimit="$WAF_RATE_LIMIT"
export WAFBlockedCountries="$WAF_BLOCKED_COUNTRIES"

# 監視・ログ設定
export EnableVPCFlowLogs="true"
export EnableCloudTrail="true"
export CloudWatchLogRetentionDays="90"

# バックアップ設定
export BackupEnabled="true"
export DeletionProtection="true"
export StorageEncrypted="true"

echo "本番環境用環境変数が設定されました"
echo "プロジェクト: \$PROJECT_NAME"
echo "環境: \$ENVIRONMENT"
echo "リージョン: \$AWS_REGION"
EOF
    
    chmod +x "$env_file"
    
    log_success "環境変数エクスポートファイル作成完了: $env_file"
}

# 設定確認
confirm_configuration() {
    echo
    log_info "=== 設定確認 ==="
    echo "プロジェクト名: $PROJECT_NAME"
    echo "環境: $ENVIRONMENT"
    echo "リージョン: $AWS_REGION"
    echo "通知メール: $NOTIFICATION_EMAIL"
    echo "Lambda バケット: $LAMBDA_CODE_S3_BUCKET"
    echo "フロントエンド バケット: $FRONTEND_CODE_S3_BUCKET"
    echo "Lambda メモリ: ${LAMBDA_MEMORY_SIZE}MB"
    echo "Provisioned Concurrency: $LAMBDA_PROVISIONED_CONCURRENCY"
    echo "データベース: $DATABASE_INSTANCE_CLASS"
    
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        echo "Slack 通知: 有効"
    fi
    
    if [[ -n "$CUSTOM_DOMAIN_NAME" ]]; then
        echo "カスタムドメイン: $CUSTOM_DOMAIN_NAME"
    fi
    
    echo
    log_warning "この設定で本番環境をデプロイしますか？ (y/N)"
    read -r confirmation
    if [[ ! "$confirmation" =~ ^[Yy]$ ]]; then
        log_info "設定がキャンセルされました"
        exit 0
    fi
}

# AWS 接続テスト
test_aws_connection() {
    log_info "AWS 接続をテスト中..."
    
    # AWS CLI 認証確認
    if ! aws sts get-caller-identity > /dev/null 2>&1; then
        log_error "AWS 認証に失敗しました"
        log_info "AWS CLI の設定を確認してください: aws configure"
        exit 1
    fi
    
    # リージョン確認
    local current_region=$(aws configure get region)
    if [[ "$current_region" != "$AWS_REGION" ]]; then
        log_warning "現在のリージョン ($current_region) が想定と異なります"
        log_info "リージョンを $AWS_REGION に設定することを推奨します"
    fi
    
    # 基本的な権限確認
    if ! aws cloudformation list-stacks --region "$AWS_REGION" > /dev/null 2>&1; then
        log_error "CloudFormation へのアクセス権限がありません"
        exit 1
    fi
    
    log_success "AWS 接続テスト完了"
}

# メイン実行関数
main() {
    log_info "=== CSR Lambda API System - 本番環境設定スクリプト ==="
    
    # AWS 接続テスト
    test_aws_connection
    
    # 設定収集
    collect_configuration
    
    # 設定確認
    confirm_configuration
    
    # 環境変数設定
    set_environment_variables
    
    # ファイル更新
    update_parameters_file
    create_env_export_file
    
    echo
    log_success "=== 本番環境設定完了 ==="
    log_info "次のステップ:"
    log_info "1. 設定を確認: cat parameters.json"
    log_info "2. 環境変数を読み込み: source .env.prod.export"
    log_info "3. デプロイメント実行: ./deploy-enhanced.sh"
    
    echo
    log_warning "重要: .env.prod.export ファイルには機密情報が含まれています"
    log_warning "適切に管理し、バージョン管理システムにコミットしないでください"
}

# スクリプト実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi