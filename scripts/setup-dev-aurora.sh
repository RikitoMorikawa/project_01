#!/bin/bash

# AWS Aurora MySQL Development Environment Setup Script
# 開発環境用のAurora MySQLクラスターを作成

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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
PROJECT_NAME="csr-lambda-api"
ENVIRONMENT="dev"
AWS_REGION="ap-northeast-1"
DB_NAME="csr_lambda_dev"
DB_USERNAME="dev_user"
DB_PASSWORD="DevPassword123!"
CLUSTER_IDENTIFIER="${PROJECT_NAME}-${ENVIRONMENT}-aurora"
SUBNET_GROUP_NAME="${PROJECT_NAME}-${ENVIRONMENT}-subnet-group"

# Check AWS credentials
check_aws_credentials() {
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS 認証情報が設定されていません"
        print_status "AWS 認証情報を設定してください:"
        print_status "  aws configure"
        exit 1
    fi
    
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    local region=$(aws configure get region || echo "ap-northeast-1")
    print_success "AWS 認証情報が設定されています (Account: $account_id, Region: $region)"
}

# Get default VPC and subnets
get_vpc_info() {
    print_status "デフォルトVPCとサブネット情報を取得中..."
    
    # Get default VPC
    VPC_ID=$(aws ec2 describe-vpcs \
        --filters "Name=is-default,Values=true" \
        --query 'Vpcs[0].VpcId' \
        --output text \
        --region "$AWS_REGION")
    
    if [ "$VPC_ID" = "None" ] || [ -z "$VPC_ID" ]; then
        print_error "デフォルトVPCが見つかりません"
        exit 1
    fi
    
    print_success "デフォルトVPC: $VPC_ID"
    
    # Get subnets in different AZs
    SUBNET_IDS=$(aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=$VPC_ID" \
        --query 'Subnets[*].SubnetId' \
        --output text \
        --region "$AWS_REGION")
    
    if [ -z "$SUBNET_IDS" ]; then
        print_error "サブネットが見つかりません"
        exit 1
    fi
    
    print_success "サブネット: $SUBNET_IDS"
}

# Create DB subnet group
create_subnet_group() {
    print_status "DBサブネットグループを作成中..."
    
    # Check if subnet group already exists
    if aws rds describe-db-subnet-groups \
        --db-subnet-group-name "$SUBNET_GROUP_NAME" \
        --region "$AWS_REGION" &> /dev/null; then
        print_warning "DBサブネットグループが既に存在します: $SUBNET_GROUP_NAME"
        return 0
    fi
    
    # Create subnet group
    aws rds create-db-subnet-group \
        --db-subnet-group-name "$SUBNET_GROUP_NAME" \
        --db-subnet-group-description "Subnet group for ${PROJECT_NAME} ${ENVIRONMENT} Aurora cluster" \
        --subnet-ids $SUBNET_IDS \
        --region "$AWS_REGION" \
        --tags "Key=Environment,Value=$ENVIRONMENT" "Key=Project,Value=$PROJECT_NAME"
    
    print_success "DBサブネットグループを作成しました: $SUBNET_GROUP_NAME"
}

# Create security group
create_security_group() {
    print_status "セキュリティグループを作成中..."
    
    SG_NAME="${PROJECT_NAME}-${ENVIRONMENT}-aurora-sg"
    
    # Check if security group already exists
    SECURITY_GROUP_ID=$(aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=$SG_NAME" "Name=vpc-id,Values=$VPC_ID" \
        --query 'SecurityGroups[0].GroupId' \
        --output text \
        --region "$AWS_REGION" 2>/dev/null || echo "None")
    
    if [ "$SECURITY_GROUP_ID" != "None" ] && [ -n "$SECURITY_GROUP_ID" ]; then
        print_warning "セキュリティグループが既に存在します: $SECURITY_GROUP_ID"
        return 0
    fi
    
    # Create security group
    SECURITY_GROUP_ID=$(aws ec2 create-security-group \
        --group-name "$SG_NAME" \
        --description "Security group for ${PROJECT_NAME} ${ENVIRONMENT} Aurora cluster" \
        --vpc-id "$VPC_ID" \
        --region "$AWS_REGION" \
        --query 'GroupId' \
        --output text)
    
    # Add inbound rule for MySQL (port 3306)
    aws ec2 authorize-security-group-ingress \
        --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 3306 \
        --source-group "$SECURITY_GROUP_ID" \
        --region "$AWS_REGION"
    
    # Add inbound rule for Lambda functions (if needed)
    aws ec2 authorize-security-group-ingress \
        --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 3306 \
        --cidr "0.0.0.0/0" \
        --region "$AWS_REGION"
    
    # Add tags
    aws ec2 create-tags \
        --resources "$SECURITY_GROUP_ID" \
        --tags "Key=Name,Value=$SG_NAME" "Key=Environment,Value=$ENVIRONMENT" "Key=Project,Value=$PROJECT_NAME" \
        --region "$AWS_REGION"
    
    print_success "セキュリティグループを作成しました: $SECURITY_GROUP_ID"
}

# Create Aurora cluster
create_aurora_cluster() {
    print_status "Aurora MySQLクラスターを作成中..."
    
    # Check if cluster already exists
    if aws rds describe-db-clusters \
        --db-cluster-identifier "$CLUSTER_IDENTIFIER" \
        --region "$AWS_REGION" &> /dev/null; then
        print_warning "Auroraクラスターが既に存在します: $CLUSTER_IDENTIFIER"
        return 0
    fi
    
    # Create Aurora cluster
    aws rds create-db-cluster \
        --db-cluster-identifier "$CLUSTER_IDENTIFIER" \
        --engine aurora-mysql \
        --engine-version "8.0.mysql_aurora.3.10.1" \
        --master-username "$DB_USERNAME" \
        --master-user-password "$DB_PASSWORD" \
        --database-name "$DB_NAME" \
        --db-subnet-group-name "$SUBNET_GROUP_NAME" \
        --vpc-security-group-ids "$SECURITY_GROUP_ID" \
        --backup-retention-period 7 \
        --preferred-backup-window "03:00-04:00" \
        --preferred-maintenance-window "sun:04:00-sun:05:00" \
        --storage-encrypted \
        --tags "Key=Environment,Value=$ENVIRONMENT" "Key=Project,Value=$PROJECT_NAME" \
        --region "$AWS_REGION"
    
    print_success "Auroraクラスターを作成しました: $CLUSTER_IDENTIFIER"
    print_status "クラスターが利用可能になるまで待機中..."
    
    # Wait for cluster to be available
    aws rds wait db-cluster-available \
        --db-cluster-identifier "$CLUSTER_IDENTIFIER" \
        --region "$AWS_REGION"
    
    print_success "Auroraクラスターが利用可能になりました"
}

# Create Aurora instance
create_aurora_instance() {
    print_status "Auroraインスタンスを作成中..."
    
    INSTANCE_IDENTIFIER="${CLUSTER_IDENTIFIER}-instance-1"
    
    # Check if instance already exists
    if aws rds describe-db-instances \
        --db-instance-identifier "$INSTANCE_IDENTIFIER" \
        --region "$AWS_REGION" &> /dev/null; then
        print_warning "Auroraインスタンスが既に存在します: $INSTANCE_IDENTIFIER"
        return 0
    fi
    
    # Create Aurora instance
    aws rds create-db-instance \
        --db-instance-identifier "$INSTANCE_IDENTIFIER" \
        --db-instance-class "db.r5.large" \
        --engine aurora-mysql \
        --db-cluster-identifier "$CLUSTER_IDENTIFIER" \
        --publicly-accessible \
        --tags "Key=Environment,Value=$ENVIRONMENT" "Key=Project,Value=$PROJECT_NAME" \
        --region "$AWS_REGION"
    
    print_success "Auroraインスタンスを作成しました: $INSTANCE_IDENTIFIER"
    print_status "インスタンスが利用可能になるまで待機中..."
    
    # Wait for instance to be available
    aws rds wait db-instance-available \
        --db-instance-identifier "$INSTANCE_IDENTIFIER" \
        --region "$AWS_REGION"
    
    print_success "Auroraインスタンスが利用可能になりました"
}

# Get connection information
get_connection_info() {
    print_status "接続情報を取得中..."
    
    # Get cluster endpoint
    CLUSTER_ENDPOINT=$(aws rds describe-db-clusters \
        --db-cluster-identifier "$CLUSTER_IDENTIFIER" \
        --region "$AWS_REGION" \
        --query 'DBClusters[0].Endpoint' \
        --output text)
    
    # Get reader endpoint
    READER_ENDPOINT=$(aws rds describe-db-clusters \
        --db-cluster-identifier "$CLUSTER_IDENTIFIER" \
        --region "$AWS_REGION" \
        --query 'DBClusters[0].ReaderEndpoint' \
        --output text)
    
    print_success "接続情報を取得しました"
    echo ""
    print_status "=== Aurora MySQL 接続情報 ==="
    echo "クラスター識別子: $CLUSTER_IDENTIFIER"
    echo "エンドポイント: $CLUSTER_ENDPOINT"
    echo "リーダーエンドポイント: $READER_ENDPOINT"
    echo "ポート: 3306"
    echo "データベース名: $DB_NAME"
    echo "ユーザー名: $DB_USERNAME"
    echo "パスワード: $DB_PASSWORD"
    echo ""
    
    # Update environment variables
    print_status "環境変数ファイルを更新中..."
    
    # Create development environment file for Aurora
    cat > backend/.env.dev.aurora << EOF
# Development Environment Configuration (Aurora MySQL)
ENVIRONMENT=dev

# Database Configuration (Aurora MySQL)
DB_HOST=$CLUSTER_ENDPOINT
DB_PORT=3306
DB_NAME=$DB_NAME
DB_USER=$DB_USERNAME
DB_PASSWORD=$DB_PASSWORD
DATABASE_URL=mysql+pymysql://$DB_USERNAME:$DB_PASSWORD@$CLUSTER_ENDPOINT:3306/$DB_NAME

# AWS Configuration
AWS_REGION=$AWS_REGION
COGNITO_USER_POOL_ID=ap-northeast-1_HluYCXwCo
COGNITO_CLIENT_ID=71mnemjh6en2qpd5cmv21qp30u

# API Configuration
API_TITLE=CSR Lambda API - Development (Aurora)
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
EOF
    
    print_success "環境変数ファイルを作成しました: backend/.env.dev.aurora"
}

# Main function
main() {
    print_status "=== AWS Aurora MySQL 開発環境セットアップ開始 ==="
    echo ""
    
    # Check prerequisites
    check_aws_credentials
    echo ""
    
    # Get VPC information
    get_vpc_info
    echo ""
    
    # Create resources
    create_subnet_group
    echo ""
    
    create_security_group
    echo ""
    
    create_aurora_cluster
    echo ""
    
    create_aurora_instance
    echo ""
    
    get_connection_info
    echo ""
    
    print_success "=== Aurora MySQL セットアップ完了 ==="
    echo ""
    print_status "次のステップ:"
    print_status "  1. Aurora MySQLにテーブルを作成: ./scripts/migrate-to-aurora.sh"
    print_status "  2. ローカルデータをAuroraに移行: ./scripts/sync-local-to-aurora.sh"
    print_status "  3. バックエンドでAurora接続をテスト"
    echo ""
}

# Show help
show_help() {
    echo "AWS Aurora MySQL Development Environment Setup Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup     Create Aurora MySQL cluster for development (default)"
    echo "  help      Show this help message"
    echo ""
    echo "Prerequisites:"
    echo "  - AWS CLI installed and configured"
    echo "  - Appropriate AWS permissions for RDS operations"
    echo ""
}

# Handle command line arguments
case "${1:-setup}" in
    "setup")
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