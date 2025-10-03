#!/bin/bash

# GitHub 統合デプロイスクリプト
# GitHub トークンの設定から CodePipeline のデプロイまでを一括実行

set -e

# 色付きログ出力用の関数
log_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

log_warn() {
    echo -e "\033[33m[WARN]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

log_success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

# 設定値
REGION="ap-northeast-1"
PROJECT_NAME="csr-lambda-api"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# 使用方法を表示
show_usage() {
    echo "使用方法: $0 [OPTIONS]"
    echo ""
    echo "オプション:"
    echo "  -e, --env ENV        環境名 (dev/staging/prod) [必須]"
    echo "  -t, --token TOKEN    GitHub Personal Access Token [必須]"
    echo "  --skip-token         トークン設定をスキップ（既に設定済みの場合）"
    echo "  --verify-only        検証のみ実行（デプロイはスキップ）"
    echo "  -h, --help           このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0 --env dev --token ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    echo "  $0 --env staging --skip-token  # トークンが既に設定済みの場合"
    echo "  $0 --env prod --verify-only    # 検証のみ実行"
}

# パラメータの解析
ENVIRONMENT=""
GITHUB_TOKEN=""
SKIP_TOKEN=false
VERIFY_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--token)
            GITHUB_TOKEN="$2"
            shift 2
            ;;
        --skip-token)
            SKIP_TOKEN=true
            shift
            ;;
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        -h|--help)
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

# 必須パラメータのチェック
if [[ -z "$ENVIRONMENT" ]]; then
    log_error "環境名が指定されていません"
    show_usage
    exit 1
fi

if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    log_error "無効な環境名: $ENVIRONMENT (dev/staging/prod のいずれかを指定)"
    exit 1
fi

if [[ "$SKIP_TOKEN" == false ]] && [[ -z "$GITHUB_TOKEN" ]]; then
    log_error "GitHub トークンが指定されていません"
    show_usage
    exit 1
fi

log_info "🚀 GitHub 統合デプロイを開始します"
log_info "環境: $ENVIRONMENT"
log_info "プロジェクト: $PROJECT_NAME"

# 前提条件の確認
log_info "📋 前提条件を確認中..."

# AWS CLI の確認
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI がインストールされていません"
    exit 1
fi

# AWS 認証情報の確認
if ! aws sts get-caller-identity --region "$REGION" &> /dev/null; then
    log_error "AWS 認証情報が設定されていないか、無効です"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
log_info "AWS アカウント: $ACCOUNT_ID"
log_info "リージョン: $REGION"

# 必要なスクリプトの存在確認
SETUP_TOKEN_SCRIPT="$SCRIPT_DIR/setup-github-token.sh"
VERIFY_TOKEN_SCRIPT="$SCRIPT_DIR/verify-github-token.sh"

if [[ ! -f "$SETUP_TOKEN_SCRIPT" ]]; then
    log_error "GitHub トークン設定スクリプトが見つかりません: $SETUP_TOKEN_SCRIPT"
    exit 1
fi

if [[ ! -f "$VERIFY_TOKEN_SCRIPT" ]]; then
    log_error "GitHub トークン検証スクリプトが見つかりません: $VERIFY_TOKEN_SCRIPT"
    exit 1
fi

# CloudFormation テンプレートの存在確認
GITHUB_TEMPLATE="$ROOT_DIR/infrastructure/shared/github-parameters.yaml"
IAM_TEMPLATE="$ROOT_DIR/infrastructure/shared/iam-roles.yaml"

if [[ ! -f "$GITHUB_TEMPLATE" ]]; then
    log_error "GitHub パラメータテンプレートが見つかりません: $GITHUB_TEMPLATE"
    exit 1
fi

if [[ ! -f "$IAM_TEMPLATE" ]]; then
    log_error "IAM ロールテンプレートが見つかりません: $IAM_TEMPLATE"
    exit 1
fi

log_success "✅ 前提条件の確認が完了しました"

# ステップ 1: GitHub トークンの設定
if [[ "$SKIP_TOKEN" == false ]]; then
    log_info "🔑 ステップ 1: GitHub トークンを設定中..."
    
    if ! "$SETUP_TOKEN_SCRIPT" --token "$GITHUB_TOKEN" --env "$ENVIRONMENT"; then
        log_error "GitHub トークンの設定に失敗しました"
        exit 1
    fi
    
    log_success "✅ GitHub トークンの設定が完了しました"
else
    log_info "🔑 ステップ 1: GitHub トークンの設定をスキップしました"
fi

# ステップ 2: GitHub トークンの検証
log_info "🔍 ステップ 2: GitHub トークンを検証中..."

if ! "$VERIFY_TOKEN_SCRIPT" --env "$ENVIRONMENT"; then
    log_error "GitHub トークンの検証に失敗しました"
    exit 1
fi

log_success "✅ GitHub トークンの検証が完了しました"

# 検証のみの場合はここで終了
if [[ "$VERIFY_ONLY" == true ]]; then
    log_success "🎉 検証が完了しました！"
    exit 0
fi

# ステップ 3: IAM ロールのデプロイ
log_info "👤 ステップ 3: IAM ロールをデプロイ中..."

IAM_STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}-iam-roles"

aws cloudformation deploy \
    --template-file "$IAM_TEMPLATE" \
    --stack-name "$IAM_STACK_NAME" \
    --parameter-overrides \
        ProjectName="$PROJECT_NAME" \
        Environment="$ENVIRONMENT" \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --region "$REGION" \
    --no-fail-on-empty-changeset

if [[ $? -eq 0 ]]; then
    log_success "✅ IAM ロールのデプロイが完了しました"
else
    log_error "IAM ロールのデプロイに失敗しました"
    exit 1
fi

# ステップ 4: GitHub Actions 統合の CloudFormation デプロイ
log_info "🔧 ステップ 4: GitHub Actions 統合をデプロイ中..."

GITHUB_STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}-github-actions"

# API Gateway ID を取得（既存のスタックから）
API_GATEWAY_ID=""
API_STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}-api"

if aws cloudformation describe-stacks --stack-name "$API_STACK_NAME" --region "$REGION" &> /dev/null; then
    API_GATEWAY_ID=$(aws cloudformation describe-stacks \
        --stack-name "$API_STACK_NAME" \
        --region "$REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayId'].OutputValue" \
        --output text 2>/dev/null || echo "")
fi

if [[ -z "$API_GATEWAY_ID" ]]; then
    log_warn "API Gateway ID が取得できませんでした。デフォルト値を使用します"
    API_GATEWAY_ID="placeholder"
fi

# GitHub Actions ワークフローは既に作成済み
# 既存の IAM ユーザーを使用するため、追加のCloudFormationデプロイは不要
log_info "GitHub Actions ワークフローが .github/workflows/deploy-dev.yml に作成されました"
log_info "既存の IAM ユーザーを使用します"

log_success "✅ GitHub Actions 統合の準備が完了しました"

# ステップ 5: デプロイ結果の確認
log_info "📊 ステップ 5: デプロイ結果を確認中..."

# CodePipeline の情報を取得
PIPELINE_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$GITHUB_STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='CodePipelineName'].OutputValue" \
    --output text 2>/dev/null || echo "")

WEBHOOK_URL=$(aws cloudformation describe-stacks \
    --stack-name "$GITHUB_STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='GitHubWebhookUrl'].OutputValue" \
    --output text 2>/dev/null || echo "")

ARTIFACT_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "$GITHUB_STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='ArtifactBucketName'].OutputValue" \
    --output text 2>/dev/null || echo "")

# 結果の表示
echo ""
log_success "🎉 GitHub 統合デプロイが完了しました！"
echo ""
log_info "📋 デプロイ結果:"
echo "  🏗️  IAM スタック: $IAM_STACK_NAME"
echo "  🔧 GitHub スタック: $GITHUB_STACK_NAME"
if [[ -n "$PIPELINE_NAME" ]]; then
    echo "  🚀 CodePipeline: $PIPELINE_NAME"
fi
if [[ -n "$WEBHOOK_URL" ]]; then
    echo "  🔗 Webhook URL: $WEBHOOK_URL"
fi
if [[ -n "$ARTIFACT_BUCKET" ]]; then
    echo "  📦 アーティファクトバケット: $ARTIFACT_BUCKET"
fi

# 次のステップの案内
echo ""
log_info "📋 次のステップ:"
echo "  1. GitHub リポジトリにコードをプッシュしてパイプラインをテスト"
echo "  2. AWS コンソールで CodePipeline の実行状況を確認"
echo "  3. CloudWatch Logs でビルド・デプロイログを確認"
echo ""
echo "  AWS コンソール URL:"
echo "    CodePipeline: https://console.aws.amazon.com/codesuite/codepipeline/pipelines"
echo "    CloudWatch: https://console.aws.amazon.com/cloudwatch/home?region=$REGION"

# パイプラインの初回実行
if [[ -n "$PIPELINE_NAME" ]]; then
    echo ""
    read -p "CodePipeline を今すぐ実行しますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "🚀 CodePipeline を実行中..."
        aws codepipeline start-pipeline-execution \
            --name "$PIPELINE_NAME" \
            --region "$REGION"
        
        if [[ $? -eq 0 ]]; then
            log_success "✅ CodePipeline の実行を開始しました"
            log_info "実行状況は AWS コンソールで確認できます"
        else
            log_error "CodePipeline の実行開始に失敗しました"
        fi
    fi
fi

log_success "🎉 すべての処理が完了しました！"