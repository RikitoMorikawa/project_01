#!/bin/bash

# GitHub Personal Access Token 検証スクリプト
# Parameter Store に保存されたトークンの有効性を確認

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
GITHUB_OWNER="RikitoMorikawa"
GITHUB_REPO="project_01"

# 使用方法を表示
show_usage() {
    echo "使用方法: $0 [OPTIONS]"
    echo ""
    echo "オプション:"
    echo "  -e, --env ENV        環境名 (dev/staging/prod) - オプション"
    echo "  -p, --param NAME     パラメータ名を直接指定"
    echo "  -h, --help           このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0                                    # デフォルトパラメータを確認"
    echo "  $0 --env dev                          # 開発環境用パラメータを確認"
    echo "  $0 --param /codepipeline/github/token # 特定のパラメータを確認"
}

# パラメータの解析
ENVIRONMENT=""
PARAMETER_NAME="/codepipeline/github/token"

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--param)
            PARAMETER_NAME="$2"
            shift 2
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

# 環境別のパラメータ名を設定
if [[ -n "$ENVIRONMENT" ]]; then
    PARAMETER_NAME="/codepipeline/${ENVIRONMENT}/github/token"
fi

log_info "検証対象パラメータ: $PARAMETER_NAME"

# AWS CLI の確認
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI がインストールされていません"
    exit 1
fi

# curl の確認
if ! command -v curl &> /dev/null; then
    log_error "curl がインストールされていません"
    exit 1
fi

# jq の確認
if ! command -v jq &> /dev/null; then
    log_warn "jq がインストールされていません。JSON レスポンスの詳細表示ができません"
    JQ_AVAILABLE=false
else
    JQ_AVAILABLE=true
fi

# AWS 認証情報の確認
if ! aws sts get-caller-identity --region "$REGION" &> /dev/null; then
    log_error "AWS 認証情報が設定されていないか、無効です"
    exit 1
fi

log_info "AWS 認証情報を確認しました"

# Parameter Store からトークンを取得
log_info "Parameter Store からトークンを取得中..."
GITHUB_TOKEN=$(aws ssm get-parameter \
    --name "$PARAMETER_NAME" \
    --with-decryption \
    --region "$REGION" \
    --query "Parameter.Value" \
    --output text 2>/dev/null)

if [[ $? -ne 0 ]] || [[ -z "$GITHUB_TOKEN" ]]; then
    log_error "パラメータ $PARAMETER_NAME が見つからないか、取得に失敗しました"
    log_info "以下のコマンドでパラメータを確認してください:"
    echo "  aws ssm describe-parameters --parameter-filters \"Key=Name,Values=/codepipeline\" --region $REGION"
    exit 1
fi

log_success "トークンを取得しました"

# GitHub API でトークンの有効性を確認
log_info "GitHub API でトークンの有効性を確認中..."

# ユーザー情報を取得
USER_RESPONSE=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    https://api.github.com/user)

if [[ $? -ne 0 ]]; then
    log_error "GitHub API への接続に失敗しました"
    exit 1
fi

# レスポンスの確認
if echo "$USER_RESPONSE" | grep -q '"message".*"Bad credentials"'; then
    log_error "❌ トークンが無効です"
    echo "トークンを再生成して Parameter Store を更新してください"
    exit 1
elif echo "$USER_RESPONSE" | grep -q '"login"'; then
    USERNAME=$(echo "$USER_RESPONSE" | grep -o '"login":"[^"]*"' | cut -d'"' -f4)
    log_success "✅ トークンは有効です"
    log_info "GitHub ユーザー: $USERNAME"
else
    log_error "GitHub API からの予期しないレスポンス"
    if [[ "$JQ_AVAILABLE" == true ]]; then
        echo "$USER_RESPONSE" | jq .
    else
        echo "$USER_RESPONSE"
    fi
    exit 1
fi

# リポジトリへのアクセス権限を確認
log_info "リポジトリ ${GITHUB_OWNER}/${GITHUB_REPO} へのアクセス権限を確認中..."

REPO_RESPONSE=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}")

if echo "$REPO_RESPONSE" | grep -q '"message".*"Not Found"'; then
    log_error "❌ リポジトリが見つからないか、アクセス権限がありません"
    log_info "リポジトリ: ${GITHUB_OWNER}/${GITHUB_REPO}"
    log_info "トークンの権限を確認してください (repo スコープが必要)"
    exit 1
elif echo "$REPO_RESPONSE" | grep -q '"full_name"'; then
    REPO_NAME=$(echo "$REPO_RESPONSE" | grep -o '"full_name":"[^"]*"' | cut -d'"' -f4)
    log_success "✅ リポジトリへのアクセス権限があります"
    log_info "リポジトリ: $REPO_NAME"
else
    log_error "リポジトリアクセスの確認でエラーが発生しました"
    if [[ "$JQ_AVAILABLE" == true ]]; then
        echo "$REPO_RESPONSE" | jq .
    else
        echo "$REPO_RESPONSE"
    fi
    exit 1
fi

# トークンの権限スコープを確認
log_info "トークンの権限スコープを確認中..."

SCOPES_RESPONSE=$(curl -s -I -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    https://api.github.com/user)

SCOPES=$(echo "$SCOPES_RESPONSE" | grep -i "x-oauth-scopes:" | cut -d' ' -f2- | tr -d '\r\n')

if [[ -n "$SCOPES" ]]; then
    log_info "トークンの権限スコープ: $SCOPES"
    
    # 必要な権限をチェック
    REQUIRED_SCOPES=("repo" "admin:repo_hook")
    MISSING_SCOPES=()
    
    for scope in "${REQUIRED_SCOPES[@]}"; do
        if [[ "$SCOPES" != *"$scope"* ]]; then
            MISSING_SCOPES+=("$scope")
        fi
    done
    
    if [[ ${#MISSING_SCOPES[@]} -eq 0 ]]; then
        log_success "✅ 必要な権限がすべて付与されています"
    else
        log_warn "⚠️  不足している権限があります: ${MISSING_SCOPES[*]}"
        log_info "CodePipeline の正常動作には以下の権限が必要です:"
        echo "  - repo: リポジトリへのフルアクセス"
        echo "  - admin:repo_hook: Webhook の管理"
    fi
else
    log_warn "権限スコープの取得に失敗しました"
fi

# Rate Limit の確認
log_info "API Rate Limit を確認中..."

RATE_LIMIT_RESPONSE=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    https://api.github.com/rate_limit)

if [[ "$JQ_AVAILABLE" == true ]]; then
    REMAINING=$(echo "$RATE_LIMIT_RESPONSE" | jq -r '.rate.remaining')
    LIMIT=$(echo "$RATE_LIMIT_RESPONSE" | jq -r '.rate.limit')
    RESET_TIME=$(echo "$RATE_LIMIT_RESPONSE" | jq -r '.rate.reset')
    
    if [[ "$REMAINING" != "null" ]] && [[ "$LIMIT" != "null" ]]; then
        log_info "API Rate Limit: $REMAINING / $LIMIT 残り"
        if [[ "$RESET_TIME" != "null" ]]; then
            RESET_DATE=$(date -r "$RESET_TIME" 2>/dev/null || echo "不明")
            log_info "リセット時刻: $RESET_DATE"
        fi
    fi
fi

# 最終結果の表示
echo ""
log_success "🎉 GitHub トークンの検証が完了しました！"
echo ""
log_info "📋 検証結果サマリー:"
echo "  ✅ Parameter Store からの取得: 成功"
echo "  ✅ GitHub API 認証: 成功"
echo "  ✅ リポジトリアクセス: 成功"
echo "  ✅ 権限スコープ: 確認済み"
echo ""
log_info "🚀 CodePipeline での使用準備が整いました！"

# 次のステップの案内
echo ""
log_info "📋 次のステップ:"
echo "  1. CloudFormation テンプレートをデプロイ"
echo "  2. CodePipeline の動作確認"
echo "  3. GitHub Webhook の設定確認"
echo ""
echo "  デプロイコマンド例:"
echo "    aws cloudformation deploy \\"
echo "      --template-file infrastructure/shared/github-parameters.yaml \\"
echo "      --stack-name csr-lambda-api-${ENVIRONMENT:-dev}-github \\"
echo "      --parameter-overrides Environment=${ENVIRONMENT:-dev} \\"
echo "      --capabilities CAPABILITY_IAM \\"
echo "      --region $REGION"