#!/bin/bash

# ローカル環境での AWS 設定確認スクリプト
# GitHub に secrets を設定する前の事前確認用

set -e

# カラー出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# AWS CLI 設定確認
check_aws_cli() {
    log_info "=== AWS CLI 設定確認 ==="
    
    # AWS CLI インストール確認
    if command -v aws >/dev/null 2>&1; then
        AWS_VERSION=$(aws --version)
        log_success "AWS CLI インストール済み: $AWS_VERSION"
    else
        log_error "AWS CLI がインストールされていません"
        echo "インストール方法: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    fi
    
    # 認証情報確認
    if aws sts get-caller-identity >/dev/null 2>&1; then
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
        REGION=$(aws configure get region || echo "未設定")
        
        log_success "AWS 認証成功"
        echo "  Account ID: $ACCOUNT_ID"
        echo "  User ARN: $USER_ARN"
        echo "  Default Region: $REGION"
        
        # 認証情報の取得
        ACCESS_KEY=$(aws configure get aws_access_key_id)
        SECRET_KEY=$(aws configure get aws_secret_access_key)
        
        if [[ -n "$ACCESS_KEY" && -n "$SECRET_KEY" ]]; then
            log_info "GitHub Secrets に設定する値:"
            echo "  AWS_ACCESS_KEY_ID: $ACCESS_KEY"
            echo "  AWS_SECRET_ACCESS_KEY: ${SECRET_KEY:0:4}...${SECRET_KEY: -4}"
        fi
        
    else
        log_error "AWS 認証に失敗しました"
        echo "設定方法: aws configure"
        exit 1
    fi
}

# 権限テスト
test_permissions() {
    log_info "=== 必要権限のテスト ==="
    
    local failed_tests=0
    
    # CloudFormation 権限
    echo -n "CloudFormation 権限テスト... "
    if aws cloudformation list-stacks --max-items 1 >/dev/null 2>&1; then
        echo "✅"
    else
        echo "❌"
        failed_tests=$((failed_tests + 1))
    fi
    
    # S3 権限
    echo -n "S3 権限テスト... "
    if aws s3 ls >/dev/null 2>&1; then
        echo "✅"
    else
        echo "❌"
        failed_tests=$((failed_tests + 1))
    fi
    
    # Lambda 権限
    echo -n "Lambda 権限テスト... "
    if aws lambda list-functions --max-items 1 >/dev/null 2>&1; then
        echo "✅"
    else
        echo "❌"
        failed_tests=$((failed_tests + 1))
    fi
    
    # API Gateway 権限
    echo -n "API Gateway 権限テスト... "
    if aws apigateway get-rest-apis --limit 1 >/dev/null 2>&1; then
        echo "✅"
    else
        echo "❌"
        failed_tests=$((failed_tests + 1))
    fi
    
    # CloudFront 権限
    echo -n "CloudFront 権限テスト... "
    if aws cloudfront list-distributions --max-items 1 >/dev/null 2>&1; then
        echo "✅"
    else
        echo "❌"
        failed_tests=$((failed_tests + 1))
    fi
    
    # RDS 権限
    echo -n "RDS 権限テスト... "
    if aws rds describe-db-clusters --max-items 1 >/dev/null 2>&1; then
        echo "✅"
    else
        echo "❌"
        failed_tests=$((failed_tests + 1))
    fi
    
    # IAM 権限
    echo -n "IAM 権限テスト... "
    if aws iam list-roles --max-items 1 >/dev/null 2>&1; then
        echo "✅"
    else
        echo "❌"
        failed_tests=$((failed_tests + 1))
    fi
    
    if [ $failed_tests -eq 0 ]; then
        log_success "すべての権限テストが成功しました"
    else
        log_warning "$failed_tests 個の権限テストが失敗しました"
        log_info "IAM ポリシーを確認してください: docs/aws-iam-policy.json"
    fi
}

# GitHub Secrets 設定手順の表示
show_github_setup_instructions() {
    log_info "=== GitHub Secrets 設定手順 ==="
    
    echo "1. GitHub リポジトリの Settings タブを開く"
    echo "2. 左サイドバーの 'Secrets and variables' → 'Actions' をクリック"
    echo "3. 'New repository secret' をクリック"
    echo "4. 以下の secrets を追加:"
    echo ""
    echo "   Name: AWS_ACCESS_KEY_ID"
    echo "   Secret: $(aws configure get aws_access_key_id)"
    echo ""
    echo "   Name: AWS_SECRET_ACCESS_KEY"
    echo "   Secret: $(aws configure get aws_secret_access_key)"
    echo ""
    echo "5. 本番環境用に Environment 'production' を作成"
    echo "6. Protection rules を設定（Required reviewers, Wait timer など）"
    echo ""
    log_info "設定完了後、以下のコマンドでテスト:"
    echo "git checkout -b test-secrets"
    echo "git push origin test-secrets"
    echo "# GitHub Actions の 'Test Secrets Configuration' ワークフローを確認"
}

# メイン処理
main() {
    log_info "=== ローカル AWS 設定確認開始 ==="
    
    check_aws_cli
    test_permissions
    show_github_setup_instructions
    
    log_success "=== 確認完了 ==="
}

# スクリプト実行
main "$@"