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

# CloudFormation スタックのデプロイ
echo "CloudFormation スタックをデプロイ中..."

aws cloudformation deploy \
  --template-file main.yaml \
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