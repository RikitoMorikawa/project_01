#!/bin/bash

# CSR Lambda API System - IAM Roles Deployment Script
# このスクリプトは IAM ロールとポリシーを AWS にデプロイします

set -e

# 設定
PROJECT_NAME="csr-lambda-api"
AWS_REGION="ap-northeast-1"

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 使用方法の表示
show_usage() {
    echo "使用方法: $0 <environment>"
    echo ""
    echo "環境:"
    echo "  dev      - 開発環境"
    echo "  staging  - ステージング環境"
    echo "  prod     - 本番環境"
    echo ""
    echo "例:"
    echo "  $0 dev"
    echo "  $0 staging"
    echo "  $0 prod"
}

# 引数チェック
if [ $# -ne 1 ]; then
    log_error "引数が不正です"
    show_usage
    exit 1
fi

ENVIRONMENT=$1

# 環境の検証
case $ENVIRONMENT in
    dev|staging|prod)
        log_info "環境: $ENVIRONMENT"
        ;;
    *)
        log_error "無効な環境です: $ENVIRONMENT"
        show_usage
        exit 1
        ;;
esac

# AWS CLI の確認
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI がインストールされていません"
    exit 1
fi

# AWS 認証情報の確認
log_info "AWS 認証情報を確認中..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    log_error "AWS 認証情報が設定されていません"
    log_info "以下のコマンドで設定してください:"
    log_info "  aws configure"
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
log_success "AWS アカウント ID: $AWS_ACCOUNT_ID"

# スタック名の設定
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}-iam-roles"

log_info "IAM ロールスタックをデプロイ中: $STACK_NAME"

# CloudFormation テンプレートの存在確認
TEMPLATE_PATH="$(dirname "$0")/../shared/iam-roles.yaml"
if [ ! -f "$TEMPLATE_PATH" ]; then
    log_error "CloudFormation テンプレートが見つかりません: $TEMPLATE_PATH"
    exit 1
fi

# CloudFormation デプロイ
log_info "CloudFormation スタックをデプロイ中..."
aws cloudformation deploy \
    --template-file "$TEMPLATE_PATH" \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        ProjectName="$PROJECT_NAME" \
        Environment="$ENVIRONMENT" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$AWS_REGION" \
    --no-fail-on-empty-changeset

if [ $? -eq 0 ]; then
    log_success "IAM ロールスタックのデプロイが完了しました"
else
    log_error "IAM ロールスタックのデプロイに失敗しました"
    exit 1
fi

# 出力値の取得
log_info "デプロイされたリソース情報を取得中..."

# CloudFormation 出力の取得
OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs' \
    --output json)

if [ $? -eq 0 ]; then
    log_success "リソース情報:"
    echo "$OUTPUTS" | jq -r '.[] | "  \(.OutputKey): \(.OutputValue)"'
    
    # GitHub Actions 用の認証情報を取得
    ACCESS_KEY_ID=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="GitHubActionsAccessKeyId") | .OutputValue')
    SECRET_ACCESS_KEY=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="GitHubActionsSecretAccessKey") | .OutputValue')
    CLOUDFORMATION_ROLE_ARN=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="CloudFormationDeployRoleArn") | .OutputValue')
    
    echo ""
    log_warning "=== GitHub Secrets に設定する値 ==="
    echo "AWS_ACCESS_KEY_ID: $ACCESS_KEY_ID"
    echo "AWS_SECRET_ACCESS_KEY: $SECRET_ACCESS_KEY"
    echo "AWS_CLOUDFORMATION_ROLE_ARN: $CLOUDFORMATION_ROLE_ARN"
    echo ""
    log_warning "これらの値を GitHub リポジトリの Secrets に設定してください"
    log_info "設定方法: GitHub リポジトリ > Settings > Secrets and variables > Actions"
    
else
    log_error "リソース情報の取得に失敗しました"
    exit 1
fi

log_success "IAM ロールのデプロイが完了しました！"
log_info "次のステップ:"
log_info "1. 上記の GitHub Secrets を設定"
log_info "2. GitHub Actions ワークフローを実行"
log_info "3. アプリケーションのデプロイを確認"