#!/bin/bash

# CSR Lambda API システム - 監視インフラストラクチャデプロイスクリプト
# 
# 使用方法:
#   ./deploy-monitoring.sh <environment> [options]
#
# 例:
#   ./deploy-monitoring.sh dev
#   ./deploy-monitoring.sh staging --notification-email admin@example.com
#   ./deploy-monitoring.sh prod --notification-email admin@example.com --slack-webhook-url https://hooks.slack.com/...

set -e

# 設定
PROJECT_NAME="csr-lambda-api"
AWS_REGION="ap-northeast-1"

# 色付きログ出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
show_usage() {
    echo "使用方法: $0 <environment> [options]"
    echo ""
    echo "環境:"
    echo "  dev       開発環境"
    echo "  staging   ステージング環境"
    echo "  prod      本番環境"
    echo ""
    echo "オプション:"
    echo "  --notification-email EMAIL    アラート通知用メールアドレス"
    echo "  --slack-webhook-url URL       Slack Webhook URL"
    echo "  --pagerduty-key KEY          PagerDuty Integration Key (本番環境のみ)"
    echo "  --dry-run                    実際のデプロイを行わずに設定を確認"
    echo "  --help                       このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0 dev"
    echo "  $0 staging --notification-email admin@example.com"
    echo "  $0 prod --notification-email admin@example.com --slack-webhook-url https://hooks.slack.com/..."
}

# パラメータ解析
ENVIRONMENT=""
NOTIFICATION_EMAIL=""
SLACK_WEBHOOK_URL=""
PAGERDUTY_KEY=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        dev|staging|prod)
            ENVIRONMENT="$1"
            shift
            ;;
        --notification-email)
            NOTIFICATION_EMAIL="$2"
            shift 2
            ;;
        --slack-webhook-url)
            SLACK_WEBHOOK_URL="$2"
            shift 2
            ;;
        --pagerduty-key)
            PAGERDUTY_KEY="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            log_error "不明なオプション: $1"
            show_usage
            exit 1
            ;;
    esac
done

# 環境パラメータの検証
if [[ -z "$ENVIRONMENT" ]]; then
    log_error "環境を指定してください (dev, staging, prod)"
    show_usage
    exit 1
fi

if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    log_error "無効な環境: $ENVIRONMENT"
    show_usage
    exit 1
fi

# 本番環境の場合は通知メールを必須とする
if [[ "$ENVIRONMENT" == "prod" && -z "$NOTIFICATION_EMAIL" ]]; then
    log_error "本番環境では --notification-email が必須です"
    exit 1
fi

# AWS CLI の確認
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI がインストールされていません"
    exit 1
fi

# AWS 認証情報の確認
if ! aws sts get-caller-identity &> /dev/null; then
    log_error "AWS 認証情報が設定されていません"
    exit 1
fi

# 設定情報を表示
log_info "=== 監視インフラストラクチャデプロイ設定 ==="
log_info "プロジェクト名: $PROJECT_NAME"
log_info "環境: $ENVIRONMENT"
log_info "リージョン: $AWS_REGION"
log_info "通知メール: ${NOTIFICATION_EMAIL:-'未設定'}"
log_info "Slack Webhook: ${SLACK_WEBHOOK_URL:+'設定済み'}"
log_info "PagerDuty Key: ${PAGERDUTY_KEY:+'設定済み'}"
log_info "ドライラン: $DRY_RUN"
log_info "=============================================="

# ドライランの場合はここで終了
if [[ "$DRY_RUN" == "true" ]]; then
    log_info "ドライランモードのため、実際のデプロイは行いません"
    exit 0
fi

# デプロイ確認
echo ""
read -p "上記の設定でデプロイを実行しますか？ (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "デプロイをキャンセルしました"
    exit 0
fi

# インフラストラクチャディレクトリに移動
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")/$ENVIRONMENT"

if [[ ! -d "$INFRA_DIR" ]]; then
    log_error "インフラストラクチャディレクトリが見つかりません: $INFRA_DIR"
    exit 1
fi

cd "$INFRA_DIR"

# CloudFormation パラメータファイルを準備
PARAMS_FILE="monitoring-parameters.json"
log_info "パラメータファイルを作成中: $PARAMS_FILE"

cat > "$PARAMS_FILE" << EOF
[
  {
    "ParameterKey": "ProjectName",
    "ParameterValue": "$PROJECT_NAME"
  },
  {
    "ParameterKey": "Environment",
    "ParameterValue": "$ENVIRONMENT"
  }
EOF

# 通知メールパラメータを追加
if [[ -n "$NOTIFICATION_EMAIL" ]]; then
    cat >> "$PARAMS_FILE" << EOF
  ,{
    "ParameterKey": "NotificationEmail",
    "ParameterValue": "$NOTIFICATION_EMAIL"
  }
EOF
fi

# Slack Webhook URL パラメータを追加
if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
    cat >> "$PARAMS_FILE" << EOF
  ,{
    "ParameterKey": "SlackWebhookUrl",
    "ParameterValue": "$SLACK_WEBHOOK_URL"
  }
EOF
fi

# PagerDuty Key パラメータを追加（本番環境のみ）
if [[ "$ENVIRONMENT" == "prod" && -n "$PAGERDUTY_KEY" ]]; then
    cat >> "$PARAMS_FILE" << EOF
  ,{
    "ParameterKey": "PagerDutyIntegrationKey",
    "ParameterValue": "$PAGERDUTY_KEY"
  }
EOF
fi

cat >> "$PARAMS_FILE" << EOF
]
EOF

# 監視スタックをデプロイ
MONITORING_STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}-monitoring"
log_info "監視スタックをデプロイ中: $MONITORING_STACK_NAME"

aws cloudformation deploy \
    --template-file monitoring.yaml \
    --stack-name "$MONITORING_STACK_NAME" \
    --parameter-overrides file://"$PARAMS_FILE" \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --region "$AWS_REGION" \
    --tags \
        Project="$PROJECT_NAME" \
        Environment="$ENVIRONMENT" \
        Component="monitoring" \
        ManagedBy="cloudformation"

if [[ $? -eq 0 ]]; then
    log_success "監視スタックのデプロイが完了しました"
else
    log_error "監視スタックのデプロイに失敗しました"
    exit 1
fi

# ダッシュボードスタックをデプロイ
DASHBOARD_STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}-dashboard"
log_info "ダッシュボードスタックをデプロイ中: $DASHBOARD_STACK_NAME"

aws cloudformation deploy \
    --template-file dashboard.yaml \
    --stack-name "$DASHBOARD_STACK_NAME" \
    --parameter-overrides \
        ProjectName="$PROJECT_NAME" \
        Environment="$ENVIRONMENT" \
    --region "$AWS_REGION" \
    --tags \
        Project="$PROJECT_NAME" \
        Environment="$ENVIRONMENT" \
        Component="dashboard" \
        ManagedBy="cloudformation"

if [[ $? -eq 0 ]]; then
    log_success "ダッシュボードスタックのデプロイが完了しました"
else
    log_error "ダッシュボードスタックのデプロイに失敗しました"
    exit 1
fi

# デプロイ結果を取得
log_info "デプロイ結果を取得中..."

# 監視スタックの出力を取得
MONITORING_OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name "$MONITORING_STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs' \
    --output json)

# ダッシュボードスタックの出力を取得
DASHBOARD_OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name "$DASHBOARD_STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs' \
    --output json)

# 結果を表示
echo ""
log_success "=== デプロイ完了 ==="
log_info "監視スタック: $MONITORING_STACK_NAME"
log_info "ダッシュボードスタック: $DASHBOARD_STACK_NAME"

# ダッシュボード URL を表示
SYSTEM_DASHBOARD_URL=$(echo "$DASHBOARD_OUTPUTS" | jq -r '.[] | select(.OutputKey=="SystemDashboardUrl") | .OutputValue')
if [[ -n "$SYSTEM_DASHBOARD_URL" && "$SYSTEM_DASHBOARD_URL" != "null" ]]; then
    log_info "システム監視ダッシュボード: $SYSTEM_DASHBOARD_URL"
fi

if [[ "$ENVIRONMENT" == "prod" ]]; then
    BUSINESS_DASHBOARD_URL=$(echo "$DASHBOARD_OUTPUTS" | jq -r '.[] | select(.OutputKey=="BusinessDashboardUrl") | .OutputValue')
    SECURITY_DASHBOARD_URL=$(echo "$DASHBOARD_OUTPUTS" | jq -r '.[] | select(.OutputKey=="SecurityDashboardUrl") | .OutputValue')
    
    if [[ -n "$BUSINESS_DASHBOARD_URL" && "$BUSINESS_DASHBOARD_URL" != "null" ]]; then
        log_info "ビジネスメトリクスダッシュボード: $BUSINESS_DASHBOARD_URL"
    fi
    
    if [[ -n "$SECURITY_DASHBOARD_URL" && "$SECURITY_DASHBOARD_URL" != "null" ]]; then
        log_info "セキュリティ監視ダッシュボード: $SECURITY_DASHBOARD_URL"
    fi
elif [[ "$ENVIRONMENT" == "staging" ]]; then
    PERFORMANCE_DASHBOARD_URL=$(echo "$DASHBOARD_OUTPUTS" | jq -r '.[] | select(.OutputKey=="PerformanceDashboardUrl") | .OutputValue')
    
    if [[ -n "$PERFORMANCE_DASHBOARD_URL" && "$PERFORMANCE_DASHBOARD_URL" != "null" ]]; then
        log_info "パフォーマンステストダッシュボード: $PERFORMANCE_DASHBOARD_URL"
    fi
fi

# SNS トピック ARN を表示
ALERT_TOPIC_ARN=$(echo "$MONITORING_OUTPUTS" | jq -r '.[] | select(.OutputKey=="AlertTopicArn") | .OutputValue')
if [[ -n "$ALERT_TOPIC_ARN" && "$ALERT_TOPIC_ARN" != "null" ]]; then
    log_info "アラート通知トピック: $ALERT_TOPIC_ARN"
fi

# 次のステップを表示
echo ""
log_info "=== 次のステップ ==="
log_info "1. CloudWatch ダッシュボードにアクセスしてメトリクスを確認"
log_info "2. アラート通知のテストを実行"
log_info "3. 必要に応じてアラート閾値を調整"

if [[ -n "$NOTIFICATION_EMAIL" ]]; then
    log_info "4. メール通知の購読確認を完了"
fi

if [[ "$ENVIRONMENT" == "prod" ]]; then
    log_info "5. 本番環境監視の24/7体制を確立"
fi

# 一時ファイルをクリーンアップ
rm -f "$PARAMS_FILE"

log_success "監視インフラストラクチャのデプロイが正常に完了しました！"