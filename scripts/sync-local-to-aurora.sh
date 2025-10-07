#!/bin/bash

# Sync Local MySQL Data to Aurora MySQL
# ローカルMySQLのデータをAurora MySQLに同期

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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
LOCAL_DB_HOST="localhost"
LOCAL_DB_PORT="3306"
LOCAL_DB_NAME="csr_lambda_dev"
LOCAL_DB_USER="dev_user"
LOCAL_DB_PASSWORD="dev_password"

# Aurora configuration (read from environment file)
if [ -f "backend/.env.dev.aurora" ]; then
    source backend/.env.dev.aurora
    AURORA_HOST="$DB_HOST"
    AURORA_PORT="$DB_PORT"
    AURORA_DB_NAME="$DB_NAME"
    AURORA_USER="$DB_USER"
    AURORA_PASSWORD="$DB_PASSWORD"
else
    print_error "Aurora環境設定ファイルが見つかりません: backend/.env.dev.aurora"
    print_status "先にAuroraセットアップを実行してください: ./scripts/setup-dev-aurora.sh"
    exit 1
fi

# Check if local MySQL is running
check_local_mysql() {
    print_status "ローカルMySQLの接続を確認中..."
    
    if ! docker exec csr-lambda-mysql mysql -u "$LOCAL_DB_USER" -p"$LOCAL_DB_PASSWORD" -e "SELECT 1;" &> /dev/null; then
        print_error "ローカルMySQLに接続できません"
        print_status "開発環境を起動してください: ./scripts/dev-setup.sh start"
        exit 1
    fi
    
    print_success "ローカルMySQLに接続しました"
}

# Check Aurora connection
check_aurora_connection() {
    print_status "Aurora MySQLの接続を確認中..."
    
    if ! mysql -h "$AURORA_HOST" -P "$AURORA_PORT" -u "$AURORA_USER" -p"$AURORA_PASSWORD" -e "SELECT 1;" &> /dev/null; then
        print_error "Aurora MySQLに接続できません"
        print_status "Aurora MySQLが起動していることを確認してください"
        print_status "セキュリティグループの設定も確認してください"
        exit 1
    fi
    
    print_success "Aurora MySQLに接続しました"
}

# Create tables in Aurora
create_aurora_tables() {
    print_status "Auroraにテーブルを作成中..."
    
    # Export table structure from local MySQL
    docker exec csr-lambda-mysql mysqldump \
        -u "$LOCAL_DB_USER" \
        -p"$LOCAL_DB_PASSWORD" \
        --no-data \
        --routines \
        --triggers \
        "$LOCAL_DB_NAME" > /tmp/aurora_schema.sql
    
    # Import table structure to Aurora
    mysql -h "$AURORA_HOST" -P "$AURORA_PORT" -u "$AURORA_USER" -p"$AURORA_PASSWORD" "$AURORA_DB_NAME" < /tmp/aurora_schema.sql
    
    print_success "Auroraにテーブルを作成しました"
    
    # Clean up
    rm -f /tmp/aurora_schema.sql
}

# Sync data from local to Aurora
sync_data() {
    print_status "ローカルデータをAuroraに同期中..."
    
    # Export data from local MySQL
    docker exec csr-lambda-mysql mysqldump \
        -u "$LOCAL_DB_USER" \
        -p"$LOCAL_DB_PASSWORD" \
        --no-create-info \
        --complete-insert \
        --single-transaction \
        "$LOCAL_DB_NAME" > /tmp/aurora_data.sql
    
    # Import data to Aurora
    mysql -h "$AURORA_HOST" -P "$AURORA_PORT" -u "$AURORA_USER" -p"$AURORA_PASSWORD" "$AURORA_DB_NAME" < /tmp/aurora_data.sql
    
    print_success "データの同期が完了しました"
    
    # Clean up
    rm -f /tmp/aurora_data.sql
}

# Verify data sync
verify_sync() {
    print_status "データ同期を検証中..."
    
    # Count records in local MySQL
    LOCAL_USERS=$(docker exec csr-lambda-mysql mysql -u "$LOCAL_DB_USER" -p"$LOCAL_DB_PASSWORD" -N -e "SELECT COUNT(*) FROM $LOCAL_DB_NAME.users;")
    LOCAL_PROFILES=$(docker exec csr-lambda-mysql mysql -u "$LOCAL_DB_USER" -p"$LOCAL_DB_PASSWORD" -N -e "SELECT COUNT(*) FROM $LOCAL_DB_NAME.user_profiles;")
    
    # Count records in Aurora
    AURORA_USERS=$(mysql -h "$AURORA_HOST" -P "$AURORA_PORT" -u "$AURORA_USER" -p"$AURORA_PASSWORD" -N -e "SELECT COUNT(*) FROM $AURORA_DB_NAME.users;")
    AURORA_PROFILES=$(mysql -h "$AURORA_HOST" -P "$AURORA_PORT" -u "$AURORA_USER" -p"$AURORA_PASSWORD" -N -e "SELECT COUNT(*) FROM $AURORA_DB_NAME.user_profiles;")
    
    echo ""
    print_status "=== データ同期検証結果 ==="
    echo "ローカル MySQL:"
    echo "  - users: $LOCAL_USERS 件"
    echo "  - user_profiles: $LOCAL_PROFILES 件"
    echo ""
    echo "Aurora MySQL:"
    echo "  - users: $AURORA_USERS 件"
    echo "  - user_profiles: $AURORA_PROFILES 件"
    echo ""
    
    if [ "$LOCAL_USERS" -eq "$AURORA_USERS" ] && [ "$LOCAL_PROFILES" -eq "$AURORA_PROFILES" ]; then
        print_success "データ同期が正常に完了しました"
    else
        print_warning "データ件数に差異があります。手動で確認してください。"
    fi
}

# Add Cognito user to Aurora
add_cognito_user() {
    print_status "CognitoユーザーをAuroraに追加中..."
    
    # Check if Cognito user already exists
    COGNITO_USER_ID="47e47af8-2021-704c-366a-e05251677028"
    EXISTING_USER=$(mysql -h "$AURORA_HOST" -P "$AURORA_PORT" -u "$AURORA_USER" -p"$AURORA_PASSWORD" -N -e "SELECT COUNT(*) FROM $AURORA_DB_NAME.users WHERE cognito_user_id='$COGNITO_USER_ID';")
    
    if [ "$EXISTING_USER" -eq "0" ]; then
        # Add Cognito user
        mysql -h "$AURORA_HOST" -P "$AURORA_PORT" -u "$AURORA_USER" -p"$AURORA_PASSWORD" "$AURORA_DB_NAME" << EOF
INSERT INTO users (cognito_user_id, email, username, created_at, updated_at) 
VALUES ('$COGNITO_USER_ID', 'test@example.com', 'testuser', NOW(), NOW());

INSERT INTO user_profiles (user_id, first_name, last_name, bio, created_at, updated_at)
VALUES (LAST_INSERT_ID(), 'Test', 'User', 'Cognito test user for development', NOW(), NOW());
EOF
        
        print_success "CognitoユーザーをAuroraに追加しました"
    else
        print_warning "Cognitoユーザーは既にAuroraに存在します"
    fi
}

# Test Aurora connection with backend
test_backend_connection() {
    print_status "バックエンドからAurora接続をテスト中..."
    
    # Create temporary test script
    cat > /tmp/test_aurora_connection.py << 'EOF'
import os
import sys
sys.path.append('/app')

from app.database import get_db_connection

try:
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        print(f"✅ Aurora接続成功: users テーブルに {count} 件のレコード")
        
        cursor.execute("SELECT COUNT(*) FROM user_profiles")
        count = cursor.fetchone()[0]
        print(f"✅ Aurora接続成功: user_profiles テーブルに {count} 件のレコード")
        
except Exception as e:
    print(f"❌ Aurora接続エラー: {e}")
    sys.exit(1)
EOF
    
    # Copy Aurora environment file to container
    docker cp backend/.env.dev.aurora csr-lambda-backend:/app/.env.dev
    
    # Run test in backend container
    if docker exec csr-lambda-backend python /tmp/test_aurora_connection.py; then
        print_success "バックエンドからAurora接続テスト成功"
    else
        print_error "バックエンドからAurora接続テスト失敗"
    fi
    
    # Restore original environment file
    docker cp backend/.env.dev csr-lambda-backend:/app/.env.dev
    
    # Clean up
    rm -f /tmp/test_aurora_connection.py
}

# Main function
main() {
    print_status "=== ローカルデータをAuroraに同期開始 ==="
    echo ""
    
    # Check connections
    check_local_mysql
    check_aurora_connection
    echo ""
    
    # Create tables and sync data
    create_aurora_tables
    echo ""
    
    sync_data
    echo ""
    
    # Add Cognito user
    add_cognito_user
    echo ""
    
    # Verify sync
    verify_sync
    echo ""
    
    # Test backend connection
    test_backend_connection
    echo ""
    
    print_success "=== データ同期完了 ==="
    echo ""
    print_status "次のステップ:"
    print_status "  1. バックエンドでAurora接続を使用: cp backend/.env.dev.aurora backend/.env.dev"
    print_status "  2. 開発環境を再起動: ./scripts/dev-setup.sh restart"
    print_status "  3. ログインテスト: http://localhost:3000/login"
    echo ""
}

# Show help
show_help() {
    echo "Sync Local MySQL Data to Aurora MySQL"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  sync      Sync local data to Aurora (default)"
    echo "  help      Show this help message"
    echo ""
    echo "Prerequisites:"
    echo "  - Local development environment running"
    echo "  - Aurora MySQL cluster created and accessible"
    echo "  - backend/.env.dev.aurora file exists"
    echo ""
}

# Handle command line arguments
case "${1:-sync}" in
    "sync")
        main
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac