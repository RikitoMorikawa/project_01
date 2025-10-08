#!/bin/bash

# 一般的な開発環境パスワードでRDS接続をテスト

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

# 一般的な開発環境パスワード
COMMON_PASSWORDS=(
    "password"
    "dev_password"
    "devpassword"
    "development"
    "admin"
    "admin123"
    "password123"
    "dev123"
    "csr-lambda-dev"
    "csr_lambda_dev"
    "csrlambda"
    "test123"
    "testpassword"
)

print_status "RDS接続テスト - 一般的なパスワードを試行"
echo "ホスト: $DB_HOST"
echo "データベース: $DB_NAME"
echo "ユーザー: $DB_USER"
echo ""

# MySQL clientの存在確認
if ! command -v mysql &> /dev/null; then
    print_error "mysqlクライアントが見つかりません"
    exit 1
fi

# 各パスワードを試行
for password in "${COMMON_PASSWORDS[@]}"; do
    print_status "パスワードを試行中: $password"
    
    if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$password" "$DB_NAME" -e "SELECT 1 as test;" > /dev/null 2>&1; then
        print_success "RDS接続成功! パスワード: $password"
        
        # データベース情報を取得
        print_status "データベース情報を取得中..."
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$password" "$DB_NAME" -e "
            SELECT 
                DATABASE() as current_database,
                USER() as current_user,
                VERSION() as mysql_version;
        "
        
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
DB_PASSWORD=$password
DATABASE_URL=mysql+pymysql://$DB_USER:$password@$DB_HOST:$DB_PORT/$DB_NAME

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
        print_success "正しいパスワード: $password"
        exit 0
    else
        echo "  ❌ 失敗"
    fi
done

print_error "すべての一般的なパスワードで接続に失敗しました"
print_status "手動でパスワードを確認する必要があります"
echo ""
print_status "次の方法を試してください:"
echo "1. AWS Systems Manager Parameter Store を確認"
echo "2. CloudFormation スタックの作成者に確認"
echo "3. RDS コンソールでパスワードをリセット"