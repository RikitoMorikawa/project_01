#!/bin/bash

# RDS MySQL接続テスト (mysql clientを使用)

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

# RDS接続情報
DB_HOST="csr-lambda-api-dev-aurora-instance-1.cpqwmygo62qx.ap-northeast-1.rds.amazonaws.com"
DB_PORT="3306"
DB_NAME="csr_lambda_dev"
DB_USER="dev_user"

print_status "RDS接続テスト"
echo "ホスト: $DB_HOST"
echo "データベース: $DB_NAME"
echo "ユーザー: $DB_USER"
echo ""

# パスワードを入力
read -s -p "RDSパスワードを入力してください: " DB_PASSWORD
echo ""

# MySQL clientの存在確認
if ! command -v mysql &> /dev/null; then
    print_error "mysqlクライアントが見つかりません"
    print_status "インストール方法:"
    print_status "  macOS: brew install mysql-client"
    print_status "  または: brew install mysql"
    exit 1
fi

print_status "RDS接続を試行中..."

# 接続テスト
if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SELECT 1 as test;" > /dev/null 2>&1; then
    print_success "RDS接続成功!"
    
    # データベース情報を取得
    print_status "データベース情報を取得中..."
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "
        SELECT 
            DATABASE() as current_database,
            USER() as current_user,
            VERSION() as mysql_version;
    "
    
    # テーブル一覧を取得
    print_status "テーブル一覧を取得中..."
    TABLE_COUNT=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SHOW TABLES;" -s -N | wc -l)
    echo "テーブル数: $TABLE_COUNT"
    
    if [ "$TABLE_COUNT" -gt 0 ]; then
        echo "テーブル一覧:"
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SHOW TABLES;" -s -N | sed 's/^/  - /'
    fi
    
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
DB_PASSWORD=$DB_PASSWORD
DATABASE_URL=mysql+pymysql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME

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
    
else
    print_error "RDS接続失敗"
    echo ""
    print_status "考えられる原因:"
    echo "1. パスワードが間違っている"
    echo "2. セキュリティグループでアクセスが制限されている"
    echo "3. RDSインスタンスが停止している"
    echo "4. ネットワーク接続の問題"
    echo ""
    print_status "セキュリティグループを確認してください:"
    echo "aws ec2 describe-security-groups --group-ids \$(aws rds describe-db-instances --db-instance-identifier csr-lambda-api-dev-aurora-instance-1 --query 'DBInstances[0].VpcSecurityGroups[0].VpcSecurityGroupId' --output text)"
    exit 1
fi