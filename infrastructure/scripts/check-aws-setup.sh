#!/bin/bash

# CSR Lambda API System - AWS Setup Verification Script
# このスクリプトは AWS 設定が正しく行われているかを確認します

set -e

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

# 設定
PROJECT_NAME="csr-lambda-api"
AWS_REGION="ap-northeast-1"

echo "🔍 AWS セットアップ確認スクリプト"
echo "=================================="
echo ""

# 1. AWS CLI の確認
log_info "1. AWS CLI の確認"
if command -v aws &> /dev/null; then
    AWS_VERSION=$(aws --version 2>&1 | cut -d' ' -f1)
    log_success "AWS CLI がインストールされています: $AWS_VERSION"
else
    log_error "AWS CLI がインストールされていません"
    echo "インストール方法: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

echo ""

# 2. AWS 認証情報の確認
log_info "2. AWS 認証情報の確認"
if aws sts get-caller-identity > /dev/null 2>&1; then
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
    log_success "AWS 認証情報が設定されています"
    log_info "  アカウント ID: $AWS_ACCOUNT_ID"
    log_info "  ユーザー ARN: $AWS_USER_ARN"
else
    log_error "AWS 認証情報が設定されていません"
    log_info "設定方法: aws configure"
    exit 1
fi

echo ""

# 3. 必要な権限の確認
log_info "3. 必要な権限の確認"

# CloudFormation 権限
if aws cloudformation list-stacks --max-items 1 > /dev/null 2>&1; then
    log_success "CloudFormation 権限: OK"
else
    log_error "CloudFormation 権限: NG"
fi

# IAM 権限
if aws iam list-roles --max-items 1 > /dev/null 2>&1; then
    log_success "IAM 権限: OK"
else
    log_error "IAM 権限: NG"
fi

# Lambda 権限
if aws lambda list-functions --max-items 1 > /dev/null 2>&1; then
    log_success "Lambda 権限: OK"
else
    log_error "Lambda 権限: NG"
fi

# S3 権限
if aws s3 ls > /dev/null 2>&1; then
    log_success "S3 権限: OK"
else
    log_error "S3 権限: NG"
fi

echo ""

# 4. 既存のスタックの確認
log_info "4. 既存の CloudFormation スタックの確認"

ENVIRONMENTS=("dev" "staging" "prod")
for ENV in "${ENVIRONMENTS[@]}"; do
    STACK_NAME="${PROJECT_NAME}-${ENV}-iam-roles"
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" > /dev/null 2>&1; then
        STACK_STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" --query 'Stacks[0].StackStatus' --output text)
        log_success "$ENV 環境 IAM スタック: $STACK_STATUS"
    else
        log_warning "$ENV 環境 IAM スタック: 未作成"
    fi
done

echo ""

# 5. GitHub リポジトリの確認
log_info "5. GitHub リポジトリの確認"
if [ -d ".git" ]; then
    REPO_URL=$(git remote get-url origin 2>/dev/null || echo "不明")
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "不明")
    log_success "Git リポジトリが設定されています"
    log_info "  リポジトリ URL: $REPO_URL"
    log_info "  現在のブランチ: $CURRENT_BRANCH"
else
    log_warning "Git リポジトリが初期化されていません"
fi

echo ""

# 6. 必要なファイルの確認
log_info "6. 必要なファイルの確認"

REQUIRED_FILES=(
    "infrastructure/shared/iam-roles.yaml"
    "infrastructure/shared/iam-policies.json"
    "infrastructure/scripts/deploy-iam-roles.sh"
    ".github/workflows/dev-deploy.yml"
    ".github/workflows/staging-deploy.yml"
    ".github/workflows/prod-deploy.yml"
)

for FILE in "${REQUIRED_FILES[@]}"; do
    if [ -f "$FILE" ]; then
        log_success "$FILE: 存在"
    else
        log_error "$FILE: 不存在"
    fi
done

echo ""

# 7. 推奨される次のステップ
log_info "7. 推奨される次のステップ"
echo ""
echo "✅ 準備完了の場合:"
echo "   1. IAM ロールをデプロイ: ./infrastructure/scripts/deploy-iam-roles.sh dev"
echo "   2. GitHub Secrets を設定"
echo "   3. GitHub Actions ワークフローを実行"
echo ""
echo "❌ 問題がある場合:"
echo "   1. AWS 認証情報を確認: aws configure"
echo "   2. 必要な権限を確認"
echo "   3. ドキュメントを参照: infrastructure/docs/AWS-SETUP-GUIDE.md"
echo ""

# 8. 設定サマリー
log_info "8. 設定サマリー"
echo "  プロジェクト名: $PROJECT_NAME"
echo "  AWS リージョン: $AWS_REGION"
echo "  AWS アカウント: $AWS_ACCOUNT_ID"
echo ""

log_success "AWS セットアップ確認が完了しました！"