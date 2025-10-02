#!/bin/bash

# GitHub Secrets 設定確認スクリプト
# GitHub Actions 内で実行して secrets の設定を確認

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

# Secrets 確認関数
check_secret() {
    local secret_name="$1"
    local secret_value="$2"
    
    if [[ -n "$secret_value" ]]; then
        # 値の最初の4文字と最後の4文字のみ表示（セキュリティのため）
        local masked_value="${secret_value:0:4}...${secret_value: -4}"
        log_success "$secret_name: 設定済み ($masked_value)"
        return 0
    else
        log_error "$secret_name: 未設定"
        return 1
    fi
}

# AWS 認証情報の確認
check_aws_credentials() {
    log_info "=== AWS 認証情報の確認 ==="
    
    local aws_access_key_id="$1"
    local aws_secret_access_key="$2"
    
    # Secrets の存在確認
    check_secret "AWS_ACCESS_KEY_ID" "$aws_access_key_id"
    check_secret "AWS_SECRET_ACCESS_KEY" "$aws_secret_access_key"
    
    # AWS CLI での認証テスト
    if [[ -n "$aws_access_key_id" && -n "$aws_secret_access_key" ]]; then
        log_info "AWS 認証テストを実行中..."
        
        export AWS_ACCESS_KEY_ID="$aws_access_key_id"
        export AWS_SECRET_ACCESS_KEY="$aws_secret_access_key"
        export AWS_DEFAULT_REGION="ap-northeast-1"
        
        if aws sts get-caller-identity >/dev/null 2>&1; then
            ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
            USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
            
            log_success "AWS 認証成功"
            log_info "Account ID: $ACCOUNT_ID"
            log_info "User ARN: $USER_ARN"
            
            # 権限テスト
            log_info "基本権限をテスト中..."
            
            # S3 権限テスト
            if aws s3 ls >/dev/null 2>&1; then
                log_success "S3 権限: OK"
            else
                log_warning "S3 権限: 制限あり"
            fi
            
            # Lambda 権限テスト
            if aws lambda list-functions --max-items 1 >/dev/null 2>&1; then
                log_success "Lambda 権限: OK"
            else
                log_warning "Lambda 権限: 制限あり"
            fi
            
            # CloudFormation 権限テスト
            if aws cloudformation list-stacks --max-items 1 >/dev/null 2>&1; then
                log_success "CloudFormation 権限: OK"
            else
                log_warning "CloudFormation 権限: 制限あり"
            fi
            
        else
            log_error "AWS 認証失敗"
            return 1
        fi
    else
        log_error "AWS 認証情報が不完全です"
        return 1
    fi
}

# オプション Secrets の確認
check_optional_secrets() {
    log_info "=== オプション Secrets の確認 ==="
    
    local slack_webhook="$1"
    local notification_email="$2"
    
    if [[ -n "$slack_webhook" ]]; then
        check_secret "SLACK_WEBHOOK_URL" "$slack_webhook"
        
        # Slack webhook テスト
        log_info "Slack webhook テスト中..."
        if curl -f -s -X POST "$slack_webhook" \
           -H 'Content-type: application/json' \
           --data '{"text":"GitHub Actions Secrets テスト"}' >/dev/null 2>&1; then
            log_success "Slack 通知テスト成功"
        else
            log_warning "Slack 通知テスト失敗"
        fi
    else
        log_info "SLACK_WEBHOOK_URL: 未設定（オプション）"
    fi
    
    if [[ -n "$notification_email" ]]; then
        check_secret "NOTIFICATION_EMAIL" "$notification_email"
    else
        log_info "NOTIFICATION_EMAIL: 未設定（オプション）"
    fi
}

# 環境別設定の確認
check_environment_config() {
    local environment="$1"
    
    log_info "=== 環境設定の確認: $environment ==="
    
    case "$environment" in
        "dev")
            log_info "開発環境: 基本設定のみ必要"
            ;;
        "staging")
            log_info "ステージング環境: 包括的テスト設定"
            ;;
        "prod")
            log_info "本番環境: 厳格なセキュリティ設定"
            log_info "Environment protection rules の確認が必要"
            ;;
        *)
            log_warning "不明な環境: $environment"
            ;;
    esac
}

# セキュリティチェック
security_check() {
    log_info "=== セキュリティチェック ==="
    
    # GitHub Actions の実行環境確認
    if [[ "$GITHUB_ACTIONS" == "true" ]]; then
        log_success "GitHub Actions 環境で実行中"
        log_info "Repository: $GITHUB_REPOSITORY"
        log_info "Workflow: $GITHUB_WORKFLOW"
        log_info "Run ID: $GITHUB_RUN_ID"
    else
        log_warning "ローカル環境で実行中（本番では GitHub Actions で実行してください）"
    fi
    
    # 環境変数の漏洩チェック
    log_info "環境変数の安全性チェック..."
    
    # 危険な環境変数がないかチェック
    if env | grep -E "(PASSWORD|SECRET|KEY|TOKEN)" | grep -v "AWS_ACCESS_KEY_ID" >/dev/null 2>&1; then
        log_warning "機密情報が環境変数に含まれている可能性があります"
    else
        log_success "環境変数の安全性: OK"
    fi
}

# メイン処理
main() {
    log_info "=== GitHub Secrets 設定確認開始 ==="
    
    # 引数から環境を取得（デフォルトは dev）
    local environment="${1:-dev}"
    
    # 必須 Secrets の確認
    check_aws_credentials "$AWS_ACCESS_KEY_ID" "$AWS_SECRET_ACCESS_KEY"
    
    # オプション Secrets の確認
    check_optional_secrets "$SLACK_WEBHOOK_URL" "$NOTIFICATION_EMAIL"
    
    # 環境別設定の確認
    check_environment_config "$environment"
    
    # セキュリティチェック
    security_check
    
    log_success "=== Secrets 設定確認完了 ==="
}

# スクリプト実行
main "$@"