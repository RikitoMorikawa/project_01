#!/bin/bash

# Aurora MySQL Cluster Management Script
# Aurora MySQLクラスターの開始・停止・状態確認

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
CLUSTER_ID="csr-lambda-api-dev-aurora"
INSTANCE_ID="csr-lambda-api-dev-aurora-instance-1"
AWS_REGION="ap-northeast-1"

# Check cluster status
check_status() {
    print_status "Aurora クラスターの状態を確認中..."
    
    CLUSTER_STATUS=$(aws rds describe-db-clusters \
        --db-cluster-identifier "$CLUSTER_ID" \
        --region "$AWS_REGION" \
        --query 'DBClusters[0].Status' \
        --output text 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$CLUSTER_STATUS" = "NOT_FOUND" ]; then
        print_error "Aurora クラスターが見つかりません: $CLUSTER_ID"
        exit 1
    fi
    
    INSTANCE_STATUS=$(aws rds describe-db-instances \
        --db-instance-identifier "$INSTANCE_ID" \
        --region "$AWS_REGION" \
        --query 'DBInstances[0].DBInstanceStatus' \
        --output text 2>/dev/null || echo "NOT_FOUND")
    
    echo ""
    print_status "=== Aurora MySQL 状態 ==="
    echo "クラスター: $CLUSTER_STATUS"
    echo "インスタンス: $INSTANCE_STATUS"
    echo ""
    
    if [ "$CLUSTER_STATUS" = "available" ]; then
        # Get endpoint information
        ENDPOINT=$(aws rds describe-db-clusters \
            --db-cluster-identifier "$CLUSTER_ID" \
            --region "$AWS_REGION" \
            --query 'DBClusters[0].Endpoint' \
            --output text)
        
        print_status "接続エンドポイント: $ENDPOINT"
        echo ""
    fi
}

# Start Aurora cluster
start_cluster() {
    print_status "Aurora クラスターを開始中..."
    
    # Check current status
    CLUSTER_STATUS=$(aws rds describe-db-clusters \
        --db-cluster-identifier "$CLUSTER_ID" \
        --region "$AWS_REGION" \
        --query 'DBClusters[0].Status' \
        --output text)
    
    if [ "$CLUSTER_STATUS" = "available" ]; then
        print_warning "Aurora クラスターは既に稼働中です"
        return 0
    fi
    
    if [ "$CLUSTER_STATUS" != "stopped" ]; then
        print_error "Aurora クラスターの状態が不正です: $CLUSTER_STATUS"
        print_status "現在の状態では開始できません"
        exit 1
    fi
    
    # Start cluster
    aws rds start-db-cluster \
        --db-cluster-identifier "$CLUSTER_ID" \
        --region "$AWS_REGION"
    
    print_status "クラスターが利用可能になるまで待機中..."
    
    # Wait for cluster to be available
    aws rds wait db-cluster-available \
        --db-cluster-identifier "$CLUSTER_ID" \
        --region "$AWS_REGION"
    
    print_success "Aurora クラスターが開始されました"
    
    # Show connection info
    check_status
}

# Stop Aurora cluster
stop_cluster() {
    print_status "Aurora クラスターを停止中..."
    
    # Check current status
    CLUSTER_STATUS=$(aws rds describe-db-clusters \
        --db-cluster-identifier "$CLUSTER_ID" \
        --region "$AWS_REGION" \
        --query 'DBClusters[0].Status' \
        --output text)
    
    if [ "$CLUSTER_STATUS" = "stopped" ]; then
        print_warning "Aurora クラスターは既に停止中です"
        return 0
    fi
    
    if [ "$CLUSTER_STATUS" != "available" ]; then
        print_error "Aurora クラスターの状態が不正です: $CLUSTER_STATUS"
        print_status "現在の状態では停止できません"
        exit 1
    fi
    
    # Stop cluster
    aws rds stop-db-cluster \
        --db-cluster-identifier "$CLUSTER_ID" \
        --region "$AWS_REGION"
    
    print_status "クラスターが停止するまで待機中..."
    
    # Wait for cluster to be stopped
    aws rds wait db-cluster-stopped \
        --db-cluster-identifier "$CLUSTER_ID" \
        --region "$AWS_REGION"
    
    print_success "Aurora クラスターが停止されました"
    print_warning "一時停止は最大7日間です。その後自動的に再開されます。"
}

# Show help
show_help() {
    echo "Aurora MySQL Cluster Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start Aurora MySQL cluster"
    echo "  stop      Stop Aurora MySQL cluster temporarily"
    echo "  status    Show current cluster status (default)"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start    # Start the cluster"
    echo "  $0 stop     # Stop the cluster temporarily"
    echo "  $0 status   # Check current status"
    echo ""
}

# Main function
case "${1:-status}" in
    "start")
        start_cluster
        ;;
    "stop")
        stop_cluster
        ;;
    "status")
        check_status
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