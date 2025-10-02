#!/bin/bash

# CSR Lambda API System - デプロイメント監視スクリプト
# デプロイメント後のシステム監視とヘルスチェック

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
    echo "  dev       開発環境"
    echo "  staging   ステージング環境"
    echo "  prod      本番環境"
    echo ""
    echo "オプション:"
    echo "  --duration <minutes>   監視時間（分）デフォルト: 10"
    echo "  --interval <seconds>   チェック間隔（秒）デフォルト: 30"
    echo "  --alert-threshold <n>  アラート閾値（連続失敗回数）デフォルト: 3"
    echo "  --continuous          継続監視モード"
    echo "  --help               このヘルプを表示"
    exit 1
}

# API ヘルスチェック
check_api_health() {
    local api_url="$1"
    local timeout="${2:-10}"
    
    if curl -f -s --max-time "$timeout" "${api_url}/health" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# フロントエンドヘルスチェック
check_frontend_health() {
    local frontend_url="$1"
    local timeout="${2:-10}"
    
    if curl -f -s --max-time "$timeout" "$frontend_url" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Lambda関数メトリクス取得
get_lambda_metrics() {
    local function_name="$1"
    local start_time="$2"
    local end_time="$3"
    
    # エラー率を取得
    ERROR_RATE=$(aws cloudwatch get-metric-statistics \
        --namespace "AWS/Lambda" \
        --metric-name "Errors" \
        --dimensions Name=FunctionName,Value="$function_name" \
        --start-time "$start_time" \
        --end-time "$end_time" \
        --period 300 \
        --statistics Sum \
        --region "$REGION" \
        --query 'Datapoints[0].Sum' \
        --output text 2>/dev/null || echo "0")
    
    # 実行回数を取得
    INVOCATION_COUNT=$(aws cloudwatch get-metric-statistics \
        --namespace "AWS/Lambda" \
        --metric-name "Invocations" \
        --dimensions Name=FunctionName,Value="$function_name" \
        --start-time "$start_time" \
        --end-time "$end_time" \
        --period 300 \
        --statistics Sum \
        --region "$REGION" \
        --query 'Datapoints[0].Sum' \
        --output text 2>/dev/null || echo "0")
    
    # 平均実行時間を取得
    AVG_DURATION=$(aws cloudwatch get-metric-statistics \
        --namespace "AWS/Lambda" \
        --metric-name "Duration" \
        --dimensions Name=FunctionName,Value="$function_name" \
        --start-time "$start_time" \
        --end-time "$end_time" \
        --period 300 \
        --statistics Average \
        --region "$REGION" \
        --query 'Datapoints[0].Average' \
        --output text 2>/dev/null || echo "0")
    
    echo "$ERROR_RATE,$INVOCATION_COUNT,$AVG_DURATION"
}

# CloudFrontメトリクス取得
get_cloudfront_metrics() {
    local distribution_id="$1"
    local start_time="$2"
    local end_time="$3"
    
    if [[ -z "$distribution_id" || "$distribution_id" == "None" ]]; then
        echo "0,0,0"
        return
    fi
    
    # 4xxエラー率を取得
    ERROR_4XX_RATE=$(aws cloudwatch get-metric-statistics \
        --namespace "AWS/CloudFront" \
        --metric-name "4xxErrorRate" \
        --dimensions Name=DistributionId,Value="$distribution_id" \
        --start-time "$start_time" \
        --end-time "$end_time" \
        --period 300 \
        --statistics Average \
        --region "us-east-1" \
        --query 'Datapoints[0].Average' \
        --output text 2>/dev/null || echo "0")
    
    # 5xxエラー率を取得
    ERROR_5XX_RATE=$(aws cloudwatch get-metric-statistics \
        --namespace "AWS/CloudFront" \
        --metric-name "5xxErrorRate" \
        --dimensions Name=DistributionId,Value="$distribution_id" \
        --start-time "$start_time" \
        --end-time "$end_time" \
        --period 300 \
        --statistics Average \
        --region "us-east-1" \
        --query 'Datapoints[0].Average' \
        --output text 2>/dev/null || echo "0")
    
    # リクエスト数を取得
    REQUEST_COUNT=$(aws cloudwatch get-metric-statistics \
        --namespace "AWS/CloudFront" \
        --metric-name "Requests" \
        --dimensions Name=DistributionId,Value="$distribution_id" \
        --start-time "$start_time" \
        --end-time "$end_time" \
        --period 300 \
        --statistics Sum \
        --region "us-east-1" \
        --query 'Datapoints[0].Sum' \
        --output text 2>/dev/null || echo "0")
    
    echo "$ERROR_4XX_RATE,$ERROR_5XX_RATE,$REQUEST_COUNT"
}

# システム情報取得
get_system_info() {
    local env="$1"
    local stack_prefix="${PROJECT_NAME}-${env}"
    
    # API Gateway URL
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name "${stack_prefix}-api" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    # フロントエンド URL
    if [[ "$env" == "dev" ]]; then
        FRONTEND_URL=$(aws cloudformation describe-stacks \
            --stack-name "${stack_prefix}-frontend" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`FrontendS3BucketWebsiteURL`].OutputValue' \
            --output text 2>/dev/null || echo "")
    else
        CLOUDFRONT_DOMAIN=$(aws cloudformation describe-stacks \
            --stack-name "${stack_prefix}-frontend" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionDomainName`].OutputValue' \
            --output text 2>/dev/null || echo "")
        FRONTEND_URL="https://$CLOUDFRONT_DOMAIN"
    fi
    
    # CloudFront Distribution ID
    CLOUDFRONT_DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
        --stack-name "${stack_prefix}-frontend" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    # Lambda関数名
    LAMBDA_FUNCTION_NAME="${stack_prefix}-api-function"
    
    echo "$API_URL|$FRONTEND_URL|$CLOUDFRONT_DISTRIBUTION_ID|$LAMBDA_FUNCTION_NAME"
}

# 監視レポート生成
generate_report() {
    local env="$1"
    local start_time="$2"
    local end_time="$3"
    local api_success_count="$4"
    local api_failure_count="$5"
    local frontend_success_count="$6"
    local frontend_failure_count="$7"
    
    local total_checks=$((api_success_count + api_failure_count))
    local api_success_rate=0
    local frontend_success_rate=0
    
    if [ $total_checks -gt 0 ]; then
        api_success_rate=$(echo "scale=2; $api_success_count * 100 / $total_checks" | bc -l)
        frontend_success_rate=$(echo "scale=2; $frontend_success_count * 100 / $total_checks" | bc -l)
    fi
    
    echo ""
    log_info "=== 監視レポート ==="
    echo "環境: $env"
    echo "監視期間: $(date -d "@$start_time" '+%Y-%m-%d %H:%M:%S') - $(date -d "@$end_time" '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "📊 ヘルスチェック結果:"
    echo "  API成功率: ${api_success_rate}% (${api_success_count}/${total_checks})"
    echo "  フロントエンド成功率: ${frontend_success_rate}% (${frontend_success_count}/${total_checks})"
    echo ""
    
    # Lambda メトリクス
    if [[ -n "$LAMBDA_FUNCTION_NAME" ]]; then
        LAMBDA_METRICS=$(get_lambda_metrics "$LAMBDA_FUNCTION_NAME" "$start_time" "$end_time")
        IFS=',' read -r error_count invocation_count avg_duration <<< "$LAMBDA_METRICS"
        
        echo "🔧 Lambda メトリクス:"
        echo "  エラー数: $error_count"
        echo "  実行回数: $invocation_count"
        echo "  平均実行時間: ${avg_duration}ms"
        echo ""
    fi
    
    # CloudFront メトリクス
    if [[ -n "$CLOUDFRONT_DISTRIBUTION_ID" && "$CLOUDFRONT_DISTRIBUTION_ID" != "None" ]]; then
        CF_METRICS=$(get_cloudfront_metrics "$CLOUDFRONT_DISTRIBUTION_ID" "$start_time" "$end_time")
        IFS=',' read -r error_4xx_rate error_5xx_rate request_count <<< "$CF_METRICS"
        
        echo "🌐 CloudFront メトリクス:"
        echo "  4xxエラー率: ${error_4xx_rate}%"
        echo "  5xxエラー率: ${error_5xx_rate}%"
        echo "  リクエスト数: $request_count"
        echo ""
    fi
    
    # 総合評価
    if [ "$api_success_rate" -ge 95 ] && [ "$frontend_success_rate" -ge 95 ]; then
        log_success "システム状態: 良好"
    elif [ "$api_success_rate" -ge 90 ] && [ "$frontend_success_rate" -ge 90 ]; then
        log_warning "システム状態: 注意"
    else
        log_error "システム状態: 異常"
    fi
}

# アラート送信（将来の拡張用）
send_alert() {
    local message="$1"
    local severity="$2"
    
    log_error "ALERT [$severity]: $message"
    
    # 将来的にはSlack、SNS、メールなどに送信
    # aws sns publish --topic-arn "$SNS_TOPIC_ARN" --message "$message"
}

# メイン監視ループ
monitor_system() {
    local env="$1"
    local duration_minutes="$2"
    local interval_seconds="$3"
    local alert_threshold="$4"
    local continuous="$5"
    
    local start_time=$(date +%s)
    local end_time=$((start_time + duration_minutes * 60))
    local api_success_count=0
    local api_failure_count=0
    local frontend_success_count=0
    local frontend_failure_count=0
    local consecutive_failures=0
    
    # システム情報取得
    SYSTEM_INFO=$(get_system_info "$env")
    IFS='|' read -r API_URL FRONTEND_URL CLOUDFRONT_DISTRIBUTION_ID LAMBDA_FUNCTION_NAME <<< "$SYSTEM_INFO"
    
    log_info "=== デプロイメント監視開始 ==="
    log_info "環境: $env"
    log_info "監視時間: ${duration_minutes}分"
    log_info "チェック間隔: ${interval_seconds}秒"
    log_info "API URL: $API_URL"
    log_info "Frontend URL: $FRONTEND_URL"
    echo ""
    
    while [[ "$continuous" == true ]] || [[ $(date +%s) -lt $end_time ]]; do
        local current_time=$(date '+%Y-%m-%d %H:%M:%S')
        local check_failed=false
        
        echo -n "[$current_time] チェック中... "
        
        # APIヘルスチェック
        if [[ -n "$API_URL" ]]; then
            if check_api_health "$API_URL"; then
                api_success_count=$((api_success_count + 1))
                echo -n "API:✅ "
            else
                api_failure_count=$((api_failure_count + 1))
                echo -n "API:❌ "
                check_failed=true
            fi
        fi
        
        # フロントエンドヘルスチェック
        if [[ -n "$FRONTEND_URL" ]]; then
            if check_frontend_health "$FRONTEND_URL"; then
                frontend_success_count=$((frontend_success_count + 1))
                echo -n "Frontend:✅ "
            else
                frontend_failure_count=$((frontend_failure_count + 1))
                echo -n "Frontend:❌ "
                check_failed=true
            fi
        fi
        
        # 連続失敗カウント
        if [[ "$check_failed" == true ]]; then
            consecutive_failures=$((consecutive_failures + 1))
            echo " (連続失敗: $consecutive_failures)"
            
            # アラート閾値チェック
            if [ $consecutive_failures -ge $alert_threshold ]; then
                send_alert "システムヘルスチェックが${consecutive_failures}回連続で失敗しました (環境: $env)" "HIGH"
            fi
        else
            consecutive_failures=0
            echo ""
        fi
        
        # 継続監視でない場合は終了時間をチェック
        if [[ "$continuous" != true ]] && [[ $(date +%s) -ge $end_time ]]; then
            break
        fi
        
        sleep "$interval_seconds"
    done
    
    # 監視終了
    local monitoring_end_time=$(date +%s)
    generate_report "$env" "$start_time" "$monitoring_end_time" "$api_success_count" "$api_failure_count" "$frontend_success_count" "$frontend_failure_count"
}

# メイン処理
main() {
    # 引数の解析
    if [[ $# -eq 0 ]]; then
        usage
    fi
    
    ENVIRONMENT=""
    DURATION_MINUTES=10
    INTERVAL_SECONDS=30
    ALERT_THRESHOLD=3
    CONTINUOUS=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            dev|staging|prod)
                ENVIRONMENT="$1"
                shift
                ;;
            --duration)
                DURATION_MINUTES="$2"
                shift 2
                ;;
            --interval)
                INTERVAL_SECONDS="$2"
                shift 2
                ;;
            --alert-threshold)
                ALERT_THRESHOLD="$2"
                shift 2
                ;;
            --continuous)
                CONTINUOUS=true
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
    
    # AWS CLI の設定確認
    if ! aws sts get-caller-identity --region "$REGION" >/dev/null 2>&1; then
        log_error "AWS CLI が正しく設定されていません。認証情報を確認してください。"
        exit 1
    fi
    
    # bc コマンドの確認
    if ! command -v bc >/dev/null 2>&1; then
        log_error "bc コマンドが見つかりません。インストールしてください。"
        exit 1
    fi
    
    # 監視開始
    monitor_system "$ENVIRONMENT" "$DURATION_MINUTES" "$INTERVAL_SECONDS" "$ALERT_THRESHOLD" "$CONTINUOUS"
}

# スクリプト実行
main "$@"