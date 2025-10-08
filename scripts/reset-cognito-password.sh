#!/bin/bash

# Cognitoユーザーのパスワードをリセット

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

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Cognito設定
USER_POOL_ID="ap-northeast-1_HluYCXwCo"
USERNAME="test@example.com"
NEW_PASSWORD="TestPassword123!"

print_status "Cognitoユーザーのパスワードをリセット"
echo "User Pool ID: $USER_POOL_ID"
echo "ユーザー名: $USERNAME"
echo "新しいパスワード: $NEW_PASSWORD"
echo ""

# 確認
read -p "パスワードをリセットしますか？ (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "キャンセルしました"
    exit 0
fi

print_status "Cognitoユーザーのパスワードを変更中..."

# パスワードを変更（管理者として）
aws cognito-idp admin-set-user-password \
    --user-pool-id "$USER_POOL_ID" \
    --username "$USERNAME" \
    --password "$NEW_PASSWORD" \
    --permanent

if [ $? -eq 0 ]; then
    print_success "パスワード変更が完了しました"
    
    # ユーザー情報を確認
    print_status "ユーザー情報を確認中..."
    aws cognito-idp admin-get-user \
        --user-pool-id "$USER_POOL_ID" \
        --username "$USERNAME" \
        --query '{Username:Username,UserStatus:UserStatus,Enabled:Enabled,UserAttributes:UserAttributes}' \
        --output table
    
    print_success "=== Cognitoログイン情報 ==="
    echo "フロントエンドURL: https://d2m0cmcbfsdzr7.cloudfront.net"
    echo "メールアドレス: $USERNAME"
    echo "パスワード: $NEW_PASSWORD"
    echo ""
    print_status "この情報でログインしてください"
    
else
    print_error "パスワード変更に失敗しました"
    exit 1
fi