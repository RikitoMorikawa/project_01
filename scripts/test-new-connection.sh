#!/bin/bash

# 新しいパスワードでRDS接続をテスト

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

# RDS接続情報（クラスターエンドポイントを使用）
DB_CLUSTER_ENDPOINT="csr-lambda-api-dev-aurora.cluster-cpqwmygo62qx.ap-northeast-1.rds.amazonaws.com"
DB_INSTANCE_ENDPOINT="csr-lambda-api-dev-aurora-instance-1.cpqwmygo62qx.ap-northeast-1.rds.amazonaws.com"
DB_PORT="3306"
DB_NAME="csr_lambda_dev"
DB_USER="dev_user"
NEW_PASSWORD="DevPassword123!"

print_status "RDS接続テスト - 新しいパスワード"
echo "クラスターエンドポイント: $DB_CLUSTER_ENDPOINT"
echo "インスタンスエンドポイント: $DB_INSTANCE_ENDPOINT"
echo "データベース: $DB_NAME"
echo "ユーザー: $DB_USER"
echo ""

# MySQL clientの存在確認
if ! command -v mysql &> /dev/null; then
    print_error "mysqlクライアントが見つかりません"
    exit 1
fi

# クラスターエンドポイントで接続テスト
print_status "クラスターエンドポイントで接続テスト中..."
if mysql -h "$DB_CLUSTER_ENDPOINT" -P "$DB_PORT" -u "$DB_USER" -p"$NEW_PASSWORD" "$DB_NAME" --default-auth=caching_sha2_password --ssl-mode=REQUIRED -e "SELECT 1 as test;" 2>/dev/null; then
    print_success "クラスターエンドポイント接続成功!"
    WORKING_ENDPOINT="$DB_CLUSTER_ENDPOINT"
else
    print_error "クラスターエンドポイント接続失敗"
    
    # インスタンスエンドポイントで接続テスト
    print_status "インスタンスエンドポイントで接続テスト中..."
    if mysql -h "$DB_INSTANCE_ENDPOINT" -P "$DB_PORT" -u "$DB_USER" -p"$NEW_PASSWORD" "$DB_NAME" --default-auth=caching_sha2_password --ssl-mode=REQUIRED -e "SELECT 1 as test;" 2>/dev/null; then
        print_success "インスタンスエンドポイント接続成功!"
        WORKING_ENDPOINT="$DB_INSTANCE_ENDPOINT"
    else
        print_error "両方のエンドポイントで接続失敗"
        
        # 詳細なエラー情報を取得
        print_status "詳細なエラー情報を取得中..."
        mysql -h "$DB_CLUSTER_ENDPOINT" -P "$DB_PORT" -u "$DB_USER" -p"$NEW_PASSWORD" "$DB_NAME" --default-auth=caching_sha2_password --ssl-mode=REQUIRED -e "SELECT 1;" 2>&1 || true
        
        print_status "考えられる原因:"
        echo "1. パスワード変更がまだ反映されていない（数分待ってから再試行）"
        echo "2. セキュリティグループの設定"
        echo "3. ネットワーク接続の問題"
        
        # セキュリティグループを確認
        print_status "セキュリティグループを確認中..."
        aws ec2 describe-security-groups --group-ids sg-02e97051fbd471fbe --query 'SecurityGroups[0].IpPermissions[*].{Protocol:IpProtocol,Port:FromPort,Source:IpRanges[0].CidrIp}' --output table
        
        exit 1
    fi
fi

# 接続成功した場合の処理
if [ -n "$WORKING_ENDPOINT" ]; then
    print_success "接続成功! 使用エンドポイント: $WORKING_ENDPOINT"
    
    # データベース情報を取得
    print_status "データベース情報を取得中..."
    mysql -h "$WORKING_ENDPOINT" -P "$DB_PORT" -u "$DB_USER" -p"$NEW_PASSWORD" "$DB_NAME" --default-auth=caching_sha2_password --ssl-mode=REQUIRED -e "
        SELECT 
            DATABASE() as current_database,
            USER() as current_user,
            VERSION() as mysql_version;
    "
    
    # テーブル一覧を取得
    print_status "テーブル一覧を取得中..."
    TABLE_COUNT=$(mysql -h "$WORKING_ENDPOINT" -P "$DB_PORT" -u "$DB_USER" -p"$NEW_PASSWORD" "$DB_NAME" --default-auth=caching_sha2_password --ssl-mode=REQUIRED -e "SHOW TABLES;" -s -N | wc -l)
    echo "テーブル数: $TABLE_COUNT"
    
    if [ "$TABLE_COUNT" -gt 0 ]; then
        echo "テーブル一覧:"
        mysql -h "$WORKING_ENDPOINT" -P "$DB_PORT" -u "$DB_USER" -p"$NEW_PASSWORD" "$DB_NAME" --default-auth=caching_sha2_password --ssl-mode=REQUIRED -e "SHOW TABLES;" -s -N | sed 's/^/  - /'
    fi
    
    # .env.dev.rds ファイルを更新
    print_status ".env.dev.rds ファイルを更新中..."
    
    cat > ../backend/.env.dev.rds << EOF
# Development Environment RDS Configuration
ENVIRONMENT=dev

# RDS Database Configuration (Development)
DB_HOST=$WORKING_ENDPOINT
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$NEW_PASSWORD
DATABASE_URL=mysql+pymysql://$DB_USER:$NEW_PASSWORD@$WORKING_ENDPOINT:$DB_PORT/$DB_NAME

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
    
    print_success "=== RDS接続設定完了 ==="
    echo "エンドポイント: $WORKING_ENDPOINT"
    echo "パスワード: $NEW_PASSWORD"
    echo "接続文字列: mysql+pymysql://$DB_USER:$NEW_PASSWORD@$WORKING_ENDPOINT:$DB_PORT/$DB_NAME"
fi