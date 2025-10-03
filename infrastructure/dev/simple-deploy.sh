#!/bin/bash

# CSR Lambda API System - シンプルな開発環境デプロイスクリプト

set -e

PROJECT_NAME="csr-lambda-api"
ENVIRONMENT="dev"
REGION="ap-northeast-1"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}-main"

echo "=== 開発環境デプロイ開始 ==="
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"

# 既存のスタックが失敗状態の場合は削除
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "NOT_EXISTS")

if [[ "$STACK_STATUS" == *"FAILED"* ]] || [[ "$STACK_STATUS" == "ROLLBACK_COMPLETE" ]]; then
  echo "既存のスタックが失敗状態です。削除中..."
  aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION"
  echo "スタック削除完了を待機中..."
  aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION"
fi

# CloudFormation スタックのデプロイ
echo "CloudFormation スタックをデプロイ中..."

# 最小限のテンプレートを使用
TEMPLATE_FILE="minimal.yaml"
if [[ ! -f "$TEMPLATE_FILE" ]]; then
  TEMPLATE_FILE="main.yaml"
fi

aws cloudformation deploy \
  --template-file "$TEMPLATE_FILE" \
  --stack-name "$STACK_NAME" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$REGION" \
  --tags Project="$PROJECT_NAME" Environment="$ENVIRONMENT" \
  --no-fail-on-empty-changeset

echo "✅ デプロイが完了しました"

# スタック情報の表示
echo "=== スタック情報 ==="
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs'