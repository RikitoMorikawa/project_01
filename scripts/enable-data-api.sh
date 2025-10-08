#!/bin/bash

# RDS Aurora クラスターでData APIを有効化

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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# RDS設定
DB_CLUSTER_IDENTIFIER="csr-lambda-api-dev-aurora"

print_status "RDS Aurora クラスターでData APIを有効化"
echo "クラスター: $DB_CLUSTER_IDENTIFIER"
echo ""

# 現在の設定を確認
print_status "現在のクラスター設定を確認中..."
aws rds describe-db-clusters \
    --db-cluster-identifier "$DB_CLUSTER_IDENTIFIER" \
    --query 'DBClusters[0].{HttpEndpointEnabled:HttpEndpointEnabled,Status:Status,Engine:Engine}' \
    --output table

# 確認
read -p "Data APIを有効化しますか？ (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "キャンセルしました"
    exit 0
fi

print_status "Data APIを有効化中..."
print_warning "この操作には数分かかる場合があります..."

# Data APIを有効化
aws rds modify-db-cluster \
    --db-cluster-identifier "$DB_CLUSTER_IDENTIFIER" \
    --enable-http-endpoint \
    --apply-immediately

if [ $? -eq 0 ]; then
    print_success "Data API有効化リクエストを送信しました"
    
    print_status "変更の適用を待機中..."
    
    # クラスターの状態を監視
    while true; do
        STATUS=$(aws rds describe-db-clusters \
            --db-cluster-identifier "$DB_CLUSTER_IDENTIFIER" \
            --query 'DBClusters[0].Status' \
            --output text)
        
        HTTP_ENDPOINT=$(aws rds describe-db-clusters \
            --db-cluster-identifier "$DB_CLUSTER_IDENTIFIER" \
            --query 'DBClusters[0].HttpEndpointEnabled' \
            --output text)
        
        echo "現在の状態: $STATUS, Data API: $HTTP_ENDPOINT"
        
        if [ "$STATUS" = "available" ] && [ "$HTTP_ENDPOINT" = "True" ]; then
            print_success "Data API有効化が完了しました"
            break
        elif [ "$STATUS" = "modifying" ]; then
            print_status "変更中... 30秒後に再確認します"
            sleep 30
        else
            print_warning "状態: $STATUS, Data API: $HTTP_ENDPOINT"
            sleep 30
        fi
    done
    
    # 最終確認
    print_status "最終設定を確認中..."
    aws rds describe-db-clusters \
        --db-cluster-identifier "$DB_CLUSTER_IDENTIFIER" \
        --query 'DBClusters[0].{HttpEndpointEnabled:HttpEndpointEnabled,Status:Status,Endpoint:Endpoint}' \
        --output table
    
    print_success "=== Data API有効化完了 ==="
    echo "クラスター: $DB_CLUSTER_IDENTIFIER"
    echo "Data API: 有効"
    echo ""
    print_status "次のステップ:"
    echo "1. AWS RDSコンソールにアクセス"
    echo "2. クエリエディタを選択"
    echo "3. 以下の情報で接続:"
    echo "   - データベースクラスター: $DB_CLUSTER_IDENTIFIER"
    echo "   - ユーザー名: dev_user"
    echo "   - パスワード: DevPassword123!"
    echo "   - データベース名: csr_lambda_dev"
    
else
    print_error "Data API有効化に失敗しました"
    exit 1
fi