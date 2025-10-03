#!/bin/bash

# CSR Lambda API System - 開発環境クリーンアップスクリプト
# 既存のリソースを削除して、クリーンな状態からデプロイを開始

set -e

PROJECT_NAME="csr-lambda-api"
ENVIRONMENT="dev"
REGION="ap-northeast-1"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}-main"

# カラー出力用
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

log_info "=== 開発環境クリーンアップ開始 ==="

# 1. CloudFormationスタックの削除
log_info "CloudFormationスタックの状態を確認中..."
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "NOT_EXISTS")

if [[ "$STACK_STATUS" != "NOT_EXISTS" ]]; then
    log_info "既存のスタックを削除中: $STACK_NAME"
    aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION"
    
    log_info "スタック削除完了を待機中..."
    aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION"
    log_success "CloudFormationスタックを削除しました"
else
    log_info "CloudFormationスタックは存在しません"
fi

# 2. S3バケットの削除
log_info "関連するS3バケットを確認・削除中..."

# Lambda デプロイメント用バケット
LAMBDA_BUCKET="csr-lambda-api-dev-lambda-deployments-992382521689"
if aws s3 ls "s3://$LAMBDA_BUCKET" --region "$REGION" >/dev/null 2>&1; then
    log_info "Lambda デプロイメント用バケットを削除中: $LAMBDA_BUCKET"
    aws s3 rb "s3://$LAMBDA_BUCKET" --force --region "$REGION"
    log_success "Lambda デプロイメント用バケットを削除しました"
else
    log_info "Lambda デプロイメント用バケットは存在しません"
fi

# フロントエンド用バケット
FRONTEND_BUCKET="csr-lambda-api-dev-frontend-992382521689"
if aws s3 ls "s3://$FRONTEND_BUCKET" --region "$REGION" >/dev/null 2>&1; then
    log_info "フロントエンド用バケットを削除中: $FRONTEND_BUCKET"
    aws s3 rb "s3://$FRONTEND_BUCKET" --force --region "$REGION"
    log_success "フロントエンド用バケットを削除しました"
else
    log_info "フロントエンド用バケットは存在しません"
fi

# 3. その他の関連バケットも確認
log_info "その他の関連バケットを確認中..."
OTHER_BUCKETS=$(aws s3 ls | grep "csr-lambda-api-dev" | awk '{print $3}' || echo "")

if [[ -n "$OTHER_BUCKETS" ]]; then
    echo "$OTHER_BUCKETS" | while read -r bucket; do
        if [[ -n "$bucket" ]]; then
            log_warning "関連バケットを発見: $bucket"
            read -p "このバケットを削除しますか？ (y/N): " -r
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                aws s3 rb "s3://$bucket" --force --region "$REGION"
                log_success "バケットを削除しました: $bucket"
            fi
        fi
    done
else
    log_info "その他の関連バケットは見つかりませんでした"
fi

log_success "=== クリーンアップが完了しました ==="
log_info "これで新しいデプロイを実行できます"