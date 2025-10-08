#!/bin/bash

# MySQLクライアントでRDS Auroraに接続

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
DB_HOST="csr-lambda-api-dev-aurora.cluster-cpqwmygo62qx.ap-northeast-1.rds.amazonaws.com"
DB_PORT="3306"
DB_NAME="csr_lambda_dev"
DB_USER="dev_user"
DB_PASSWORD="DevPassword123!"

print_status "MySQLクライアントでRDS Auroraに接続"
echo "ホスト: $DB_HOST"
echo "データベース: $DB_NAME"
echo "ユーザー: $DB_USER"
echo ""

# MySQL clientの存在確認
if ! command -v mysql &> /dev/null; then
    print_error "mysqlクライアントが見つかりません"
    print_status "インストール方法:"
    print_status "  macOS: brew install mysql-client"
    exit 1
fi

print_status "接続中..."
print_status "終了するには 'exit' または Ctrl+D を入力してください"
echo ""

# MySQLクライアントで接続（認証プラグイン指定）
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" \
    --default-auth=caching_sha2_password \
    --ssl-mode=REQUIRED \
    --prompt="MySQL [$DB_NAME]> "