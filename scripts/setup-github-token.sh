#!/bin/bash

# GitHub Personal Access Token 設定スクリプト
# CodePipeline 用の GitHub トークンを AWS Systems Manager Parameter Store に保存

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

# 設定値
REGION="ap-northeast-1"
PARAMETER_NAME="/codepipeline/github/token"

# 使用方法を表示
show_usage() {
    echo "使用方法: $0 [OPTIONS]"
    echo ""
    echo "オプション:"
    echo "  -t, --token TOKEN    GitHub Personal Access Token"
    echo "  -e, --env ENV        環境名 (dev/staging/prod) - オプション"
    echo "  -h, --help           このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0 --token ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    echo "  $0 --token ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx --env dev"
    echo ""
    echo "注意:"
    echo "  - トークンは GitHub Settings > Developer settings > Personal access tokens で作成"
    echo "  - 必要な権限: repo, admin:repo_hook"
    echo "  - AWS CLI が設定済みであることを確認してください"
}

# パラメータの解析
GITHUB_TOKEN=""
ENVIRONMENT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--token)
            GITHUB_TOKEN="$2"
            shift 2
            ;;
        -e|--env)
            ENVIRONMENT="$2"
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

# 必須パラメータのチェック
if [[ -z "$GITHUB_TOKEN" ]]; then
    log_error "GitHub トークンが指定されていません"
    show_usage
    exit 1
fi

# トークンの形式チェック
if [[ ! "$GITHUB_TOKEN" =~ ^ghp_[a-zA-Z0-9]{36}$ ]]; then
    log_warn "トークンの形式が正しくない可能性があります (ghp_で始まる40文字)"
    read -p "続行しますか？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "処理を中止しました"
        exit 0
    fi
fi

# 環境別のパラメータ名を設定
if [[ -n "$ENVIRONMENT" ]]; then
    PARAMETER_NAME="/codepipeline/${ENVIRONMENT}/github/token"
    log_info "環境別設定: $ENVIRONMENT"
fi

log_info "パラメータ名: $PARAMETER_NAME"

# AWS CLI の確認
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI がインストールされていません"
    exit 1
fi

# AWS 認証情報の確認
if ! aws sts get-caller-identity --region "$REGION" &> /dev/null; then
    log_error "AWS 認証情報が設定されていないか、無効です"
    log_info "aws configure を実行して認証情報を設定してください"
    exit 1
fi

log_info "AWS 認証情報を確認しました"

# 既存のパラメータをチェック
if aws ssm get-parameter --name "$PARAMETER_NAME" --region "$REGION" &> /dev/null; then
    log_warn "パラメータ $PARAMETER_NAME は既に存在します"
    read -p "上書きしますか？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "処理を中止しました"
        exit 0
    fi
    
    # 既存パラメータを更新
    log_info "既存のパラメータを更新中..."
    aws ssm put-parameter \
        --name "$PARAMETER_NAME" \
        --value "$GITHUB_TOKEN" \
        --type "SecureString" \
        --description "GitHub Personal Access Token for CodePipeline" \
        --region "$REGION" \
        --overwrite
else
    # 新規パラメータを作成
    log_info "新しいパラメータを作成中..."
    aws ssm put-parameter \
        --name "$PARAMETER_NAME" \
        --value "$GITHUB_TOKEN" \
        --type "SecureString" \
        --description "GitHub Personal Access Token for CodePipeline" \
        --region "$REGION"
fi

if [[ $? -eq 0 ]]; then
    log_info "✅ GitHub トークンの保存が完了しました"
    log_info "パラメータ名: $PARAMETER_NAME"
    log_info "リージョン: $REGION"
else
    log_error "❌ GitHub トークンの保存に失敗しました"
    exit 1
fi

# 保存確認
log_info "保存されたパラメータを確認中..."
STORED_TOKEN=$(aws ssm get-parameter \
    --name "$PARAMETER_NAME" \
    --with-decryption \
    --region "$REGION" \
    --query "Parameter.Value" \
    --output text 2>/dev/null)

if [[ "$STORED_TOKEN" == "$GITHUB_TOKEN" ]]; then
    log_info "✅ パラメータの保存を確認しました"
else
    log_error "❌ パラメータの保存確認に失敗しました"
    exit 1
fi

# セキュリティ情報の表示
echo ""
log_info "🔒 セキュリティ情報:"
echo "  - トークンは暗号化されて保存されました"
echo "  - Parameter Store へのアクセスは IAM で制御されます"
echo "  - トークンは定期的に更新することを推奨します"

# 次のステップの案内
echo ""
log_info "📋 次のステップ:"
echo "  1. CloudFormation テンプレートでパラメータを参照"
echo "  2. CodePipeline の作成・更新を実行"
echo "  3. GitHub Webhook の動作確認"
echo ""
echo "  CloudFormation での参照例:"
echo "    GitHubToken: !Ref GitHubTokenParameter"
echo "    GitHubTokenParameter:"
echo "      Type: AWS::SSM::Parameter::Value<String>"
echo "      Default: $PARAMETER_NAME"

log_info "🎉 GitHub トークンの設定が完了しました！"