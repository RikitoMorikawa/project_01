#!/bin/bash

# CSR Lambda API System - 緊急ロールバックスクリプト
# 本番環境で問題が発生した場合の緊急ロールバック用

set -e

# 設定
PROJECT_NAME="csr-lambda-api"
REGION="ap-northeast-1"

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

# 使用方法を表示
usage() {
    echo "使用方法: $0 <environment> [options]"
    echo ""
    echo "環境:"
    echo "  staging   ステージング環境"
    echo "  prod      本番環境"
    echo ""
    echo "オプション:"
    echo "  --lambda-only      Lambda関数のみロールバック"
    echo "  --frontend-only    フロントエンドのみロールバック"
    echo "  --to-version <n>   指定バージョンにロールバック"
    echo "  --confirm          確認プロンプトをスキップ"
    echo "  --help            このヘルプを表示"
    exit 1
}

# 確認プロンプト
confirm_rollback() {
    local env="$1"
    local component="$2"
    
    if [[ "$SKIP_CONFIRM" != "true" ]]; then
        echo ""
        log_warning "=== 緊急ロールバック確認 ==="
        echo "環境: $env"
        echo "対象: $component"
        echo ""
        read -p "本当にロールバックを実行しますか？ (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            echo "ロールバックをキャンセルしました"
            exit 0
        fi
    fi
}

# Lambda関数のロールバック
rollback_lambda() {
    local env="$1"
    local target_version="$2"
    local stack_prefix="${PROJECT_NAME}-${env}"
    
    log_info "=== Lambda関数ロールバック開始 ==="
    
    # 現在のバージョンを確認
    if aws lambda get-alias --function-name "${stack_prefix}-api-function" --name "LIVE" --region "$REGION" >/dev/null 2>&1; then
        CURRENT_VERSION=$(aws lambda get-alias \
            --function-name "${stack_prefix}-api-function" \
            --name "LIVE" \
            --region "$REGION" \
            --query 'FunctionVersion' \
            --output text)
        
        log_info "現在のバージョン: $CURRENT_VERSION"
        
        # ターゲットバージョンの決定
        if [[ -n "$target_version" ]]; then
            ROLLBACK_VERSION="$target_version"
        else
            # 前のバージョンを計算
            if [[ "$CURRENT_VERSION" =~ ^[0-9]+$ ]] && [ "$CURRENT_VERSION" -gt 1 ]; then
                ROLLBACK_VERSION=$((CURRENT_VERSION - 1))
            else
                log_error "ロールバック可能な前のバージョンがありません"
                exit 1
            fi
        fi
        
        log_info "ロールバック先バージョン: $ROLLBACK_VERSION"
        
        # バージョンが存在するか確認
        if aws lambda get-function --function-name "${stack_prefix}-api-function" --qualifier "$ROLLBACK_VERSION" --region "$REGION" >/dev/null 2>&1; then
            log_info "バージョン $ROLLBACK_VERSION にロールバック中..."
            
            # エイリアスを更新
            aws lambda update-alias \
                --function-name "${stack_prefix}-api-function" \
                --name "LIVE" \
                --function-version "$ROLLBACK_VERSION" \
                --region "$REGION"
            
            log_success "Lambda関数のロールバックが完了しました"
            
            # ヘルスチェック
            log_info "ロールバック後のヘルスチェックを実行中..."
            
            # API Gateway URLを取得
            API_URL=$(aws cloudformation describe-stacks \
                --stack-name "${stack_prefix}-api" \
                --region "$REGION" \
                --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
                --output text 2>/dev/null || echo "")
            
            if [[ -n "$API_URL" ]]; then
                for i in {1..10}; do
                    if curl -f -s "${API_URL}/health" >/dev/null; then
                        log_success "ロールバック後のヘルスチェック成功"
                        break
                    else
                        log_warning "ヘルスチェック失敗 (試行 $i/10)"
                        if [ $i -eq 10 ]; then
                            log_error "ロールバック後のヘルスチェックが失敗しました"
                            exit 1
                        else
                            sleep 10
                        fi
                    fi
                done
            fi
        else
            log_error "指定されたバージョン $ROLLBACK_VERSION が存在しません"
            exit 1
        fi
    else
        log_error "Lambda関数のエイリアス 'LIVE' が見つかりません"
        exit 1
    fi
}

# フロントエンドのロールバック
rollback_frontend() {
    local env="$1"
    local stack_prefix="${PROJECT_NAME}-${env}"
    
    log_info "=== フロントエンドロールバック開始 ==="
    
    # S3バケット名を取得
    FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name "${stack_prefix}-frontend" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`FrontendS3BucketName`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [[ -z "$FRONTEND_BUCKET" ]]; then
        log_error "フロントエンド S3 バケットが見つかりません"
        exit 1
    fi
    
    # バックアップバケットの確認
    BACKUP_BUCKET="${FRONTEND_BUCKET}-backup"
    if aws s3 ls "s3://$BACKUP_BUCKET" --region "$REGION" >/dev/null 2>&1; then
        log_info "バックアップからフロントエンドを復元中..."
        
        # 現在のファイルを一時的にバックアップ
        TEMP_BACKUP_BUCKET="${FRONTEND_BUCKET}-temp-backup-$(date +%Y%m%d-%H%M%S)"
        aws s3 sync "s3://$FRONTEND_BUCKET" "s3://$TEMP_BACKUP_BUCKET" --region "$REGION"
        
        # バックアップから復元
        aws s3 sync "s3://$BACKUP_BUCKET" "s3://$FRONTEND_BUCKET" --region "$REGION" --delete
        
        log_success "フロントエンドのロールバックが完了しました"
        log_info "現在のファイルは s3://$TEMP_BACKUP_BUCKET にバックアップされました"
        
        # CloudFrontの無効化
        CLOUDFRONT_DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
            --stack-name "${stack_prefix}-frontend" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
            --output text 2>/dev/null || echo "")
        
        if [[ -n "$CLOUDFRONT_DISTRIBUTION_ID" && "$CLOUDFRONT_DISTRIBUTION_ID" != "None" ]]; then
            log_info "CloudFrontキャッシュを無効化中..."
            INVALIDATION_ID=$(aws cloudfront create-invalidation \
                --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
                --paths "/*" \
                --region "$REGION" \
                --query 'Invalidation.Id' \
                --output text)
            
            log_info "CloudFront無効化ID: $INVALIDATION_ID"
        fi
    else
        log_error "バックアップバケット s3://$BACKUP_BUCKET が見つかりません"
        exit 1
    fi
}

# バージョン一覧表示
list_versions() {
    local env="$1"
    local stack_prefix="${PROJECT_NAME}-${env}"
    
    log_info "=== Lambda関数バージョン一覧 ==="
    
    if aws lambda get-function --function-name "${stack_prefix}-api-function" --region "$REGION" >/dev/null 2>&1; then
        # 現在のLIVEバージョン
        CURRENT_VERSION=$(aws lambda get-alias \
            --function-name "${stack_prefix}-api-function" \
            --name "LIVE" \
            --region "$REGION" \
            --query 'FunctionVersion' \
            --output text 2>/dev/null || echo "不明")
        
        echo "現在のLIVEバージョン: $CURRENT_VERSION"
        echo ""
        
        # 利用可能なバージョン一覧
        echo "利用可能なバージョン:"
        aws lambda list-versions-by-function \
            --function-name "${stack_prefix}-api-function" \
            --region "$REGION" \
            --query 'Versions[?Version!=`$LATEST`].[Version,LastModified,Description]' \
            --output table
    else
        log_error "Lambda関数が見つかりません"
        exit 1
    fi
}

# システム状態確認
check_system_status() {
    local env="$1"
    local stack_prefix="${PROJECT_NAME}-${env}"
    
    log_info "=== システム状態確認 ==="
    
    # API Gateway URLを取得
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name "${stack_prefix}-api" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$API_URL" ]]; then
        echo "API Gateway URL: $API_URL"
        
        # ヘルスチェック
        if curl -f -s "${API_URL}/health" >/dev/null; then
            log_success "API ヘルスチェック: 正常"
        else
            log_error "API ヘルスチェック: 異常"
        fi
    else
        log_error "API Gateway URLが取得できません"
    fi
    
    # CloudFront URL
    CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
        --stack-name "${stack_prefix}-frontend" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionDomainName`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [[ -n "$CLOUDFRONT_URL" ]]; then
        echo "Frontend URL: https://$CLOUDFRONT_URL"
        
        # フロントエンドチェック
        if curl -f -s "https://$CLOUDFRONT_URL" >/dev/null; then
            log_success "フロントエンド: 正常"
        else
            log_error "フロントエンド: 異常"
        fi
    else
        log_error "CloudFront URLが取得できません"
    fi
    
    # Lambda関数バージョン
    LAMBDA_VERSION=$(aws lambda get-alias \
        --function-name "${stack_prefix}-api-function" \
        --name "LIVE" \
        --region "$REGION" \
        --query 'FunctionVersion' \
        --output text 2>/dev/null || echo "不明")
    echo "Lambda バージョン: $LAMBDA_VERSION"
}

# メイン処理
main() {
    # 引数の解析
    if [[ $# -eq 0 ]]; then
        usage
    fi
    
    ENVIRONMENT=""
    LAMBDA_ONLY=false
    FRONTEND_ONLY=false
    TARGET_VERSION=""
    SKIP_CONFIRM=false
    LIST_VERSIONS=false
    CHECK_STATUS=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            staging|prod)
                ENVIRONMENT="$1"
                shift
                ;;
            --lambda-only)
                LAMBDA_ONLY=true
                shift
                ;;
            --frontend-only)
                FRONTEND_ONLY=true
                shift
                ;;
            --to-version)
                TARGET_VERSION="$2"
                shift 2
                ;;
            --confirm)
                SKIP_CONFIRM=true
                shift
                ;;
            --list-versions)
                LIST_VERSIONS=true
                shift
                ;;
            --status)
                CHECK_STATUS=true
                shift
                ;;
            --help)
                usage
                ;;
            *)
                log_error "不明なオプション: $1"
                usage
                ;;
        esac
    done
    
    if [[ -z "$ENVIRONMENT" ]]; then
        log_error "環境を指定してください"
        usage
    fi
    
    # 開発環境でのロールバックは禁止
    if [[ "$ENVIRONMENT" == "dev" ]]; then
        log_error "開発環境でのロールバックはサポートされていません"
        exit 1
    fi
    
    # AWS CLI の設定確認
    if ! aws sts get-caller-identity --region "$REGION" >/dev/null 2>&1; then
        log_error "AWS CLI が正しく設定されていません。認証情報を確認してください。"
        exit 1
    fi
    
    # バージョン一覧表示
    if [[ "$LIST_VERSIONS" == true ]]; then
        list_versions "$ENVIRONMENT"
        exit 0
    fi
    
    # システム状態確認
    if [[ "$CHECK_STATUS" == true ]]; then
        check_system_status "$ENVIRONMENT"
        exit 0
    fi
    
    log_info "=== CSR Lambda API System - 緊急ロールバック開始 ==="
    log_info "環境: $ENVIRONMENT"
    
    # ロールバック実行
    if [[ "$FRONTEND_ONLY" == true ]]; then
        confirm_rollback "$ENVIRONMENT" "フロントエンド"
        rollback_frontend "$ENVIRONMENT"
    elif [[ "$LAMBDA_ONLY" == true ]]; then
        confirm_rollback "$ENVIRONMENT" "Lambda関数"
        rollback_lambda "$ENVIRONMENT" "$TARGET_VERSION"
    else
        confirm_rollback "$ENVIRONMENT" "全コンポーネント"
        rollback_lambda "$ENVIRONMENT" "$TARGET_VERSION"
        rollback_frontend "$ENVIRONMENT"
    fi
    
    # 最終確認
    log_info "ロールバック完了後のシステム状態:"
    check_system_status "$ENVIRONMENT"
    
    log_success "=== 緊急ロールバックが完了しました ==="
}

# スクリプト実行
main "$@"