#!/bin/bash

# RDS Aurora クラスターのパスワードをリセット

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

# RDS設定
DB_CLUSTER_IDENTIFIER="csr-lambda-api-dev-aurora"
DB_USER="dev_user"
NEW_PASSWORD="DevPassword123!"

print_status "RDS Aurora クラスターのパスワードをリセット"
echo "クラスター: $DB_CLUSTER_IDENTIFIER"
echo "ユーザー: $DB_USER"
echo "新しいパスワード: $NEW_PASSWORD"
echo ""

# 確認
read -p "パスワードをリセットしますか？ (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "キャンセルしました"
    exit 0
fi

print_status "RDS Aurora クラスターのパスワードを変更中..."

# パスワードを変更
aws rds modify-db-cluster \
    --db-cluster-identifier "$DB_CLUSTER_IDENTIFIER" \
    --master-user-password "$NEW_PASSWORD" \
    --apply-immediately

if [ $? -eq 0 ]; then
    print_success "パスワード変更リクエストを送信しました"
    
    print_status "変更の適用を待機中..."
    print_status "これには数分かかる場合があります..."
    
    # クラスターの状態を監視
    while true; do
        STATUS=$(aws rds describe-db-clusters \
            --db-cluster-identifier "$DB_CLUSTER_IDENTIFIER" \
            --query 'DBClusters[0].Status' \
            --output text)
        
        echo "現在の状態: $STATUS"
        
        if [ "$STATUS" = "available" ]; then
            print_success "パスワード変更が完了しました"
            break
        elif [ "$STATUS" = "modifying" ]; then
            print_status "変更中... 30秒後に再確認します"
            sleep 30
        else
            print_error "予期しない状態: $STATUS"
            break
        fi
    done
    
    # 接続テスト
    print_status "新しいパスワードで接続テスト中..."
    
    DB_HOST="csr-lambda-api-dev-aurora-instance-1.cpqwmygo62qx.ap-northeast-1.rds.amazonaws.com"
    DB_PORT="3306"
    DB_NAME="csr_lambda_dev"
    
    if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$NEW_PASSWORD" "$DB_NAME" -e "SELECT 1 as test;" > /dev/null 2>&1; then
        print_success "接続テスト成功!"
        
        # .env.dev.rds ファイルを更新
        print_status ".env.dev.rds ファイルを更新中..."
        
        cat > ../backend/.env.dev.rds << EOF
# Development Environment RDS Configuration
ENVIRONMENT=dev

# RDS Database Configuration (Development)
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$NEW_PASSWORD
DATABASE_URL=mysql+pymysql://$DB_USER:$NEW_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME

# AWS Configuration
AWS_REGION=ap-northeast-1
COGNITO_USER_POOL_ID=ap-northeast-1_HluYCXwCo
COGNITO_CLIENT_ID=71mnemjh6en2qpd5cmv21qp30u

# API Configuration
API_TITLE=CSR Lambda API - Development (RDS)
CORS_ORIGINS=["https://d2m0cmcbfsdzr7.cloudfront.net", "http://localhost:3000"]

# CloudFront Configuration
CLOUDFRONT_DISTRIBUTION_ID=E1RDC06Y79TYSS
CLOUDFRONT_DOMAIN_NAME=d2m0cmcbfsdzr7.cloudfront.net
FRONTEND_URL=https://d2m0cmcbfsdzr7.cloudfront.net
S3_FRONTEND_BUCKET=csr-lambda-api-dev-main-frontends3bucket-a8n79be9xmun
EOF
        
        print_success ".env.dev.rds ファイルを更新しました"
        
        # データベース情報を表示
        print_status "データベース情報:"
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$NEW_PASSWORD" "$DB_NAME" -e "
            SELECT 
                DATABASE() as current_database,
                USER() as current_user,
                VERSION() as mysql_version;
        "
        
        print_success "=== RDSパスワードリセット完了 ==="
        echo "新しいパスワード: $NEW_PASSWORD"
        echo "接続文字列: mysql+pymysql://$DB_USER:$NEW_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
        
    else
        print_error "接続テストに失敗しました"
        print_status "パスワード変更は完了していますが、接続に問題があります"
    fi
    
else
    print_error "パスワード変更に失敗しました"
    exit 1
fi