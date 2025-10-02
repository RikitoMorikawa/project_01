#!/bin/bash

# CSR Lambda API System - Development Environment Deployment Script
# 開発環境のインフラストラクチャをデプロイするスクリプト

set -e

# 設定
PROJECT_NAME="csr-lambda-api"
ENVIRONMENT="dev"
REGION="ap-northeast-1"
STACK_PREFIX="${PROJECT_NAME}-${ENVIRONMENT}"

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

# パラメータファイルの読み込み
load_parameters() {
    local param_file="$1"
    if [[ -f "$param_file" ]]; then
        log_info "パラメータファイルを読み込み中: $param_file"
        # JSONファイルからCloudFormationパラメータ形式に変換
        jq -r 'to_entries | map("ParameterKey=\(.key),ParameterValue=\(.value)") | join(" ")' "$param_file"
    else
        log_error "パラメータファイルが見つかりません: $param_file"
        exit 1
    fi
}

# CloudFormationスタックのデプロイ
deploy_stack() {
    local stack_name="$1"
    local template_file="$2"
    local parameters="$3"
    local capabilities="$4"
    
    log_info "スタックをデプロイ中: $stack_name"
    
    # スタックが存在するかチェック
    if aws cloudformation describe-stacks --stack-name "$stack_name" --region "$REGION" >/dev/null 2>&1; then
        log_info "既存のスタックを更新中: $stack_name"
        aws cloudformation update-stack \
            --stack-name "$stack_name" \
            --template-body "file://$template_file" \
            --parameters $parameters \
            --capabilities $capabilities \
            --region "$REGION" \
            --tags Key=Project,Value="$PROJECT_NAME" Key=Environment,Value="$ENVIRONMENT" \
            || {
                if [[ $? -eq 255 ]]; then
                    log_warning "スタックに変更がありません: $stack_name"
                else
                    log_error "スタックの更新に失敗しました: $stack_name"
                    exit 1
                fi
            }
    else
        log_info "新しいスタックを作成中: $stack_name"
        aws cloudformation create-stack \
            --stack-name "$stack_name" \
            --template-body "file://$template_file" \
            --parameters $parameters \
            --capabilities $capabilities \
            --region "$REGION" \
            --tags Key=Project,Value="$PROJECT_NAME" Key=Environment,Value="$ENVIRONMENT" \
            || {
                log_error "スタックの作成に失敗しました: $stack_name"
                exit 1
            }
    fi
    
    # デプロイメント完了を待機
    log_info "デプロイメント完了を待機中: $stack_name"
    aws cloudformation wait stack-create-complete --stack-name "$stack_name" --region "$REGION" 2>/dev/null || \
    aws cloudformation wait stack-update-complete --stack-name "$stack_name" --region "$REGION" || {
        log_error "スタックのデプロイメントに失敗しました: $stack_name"
        aws cloudformation describe-stack-events --stack-name "$stack_name" --region "$REGION" --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`]'
        exit 1
    }
    
    log_success "スタックのデプロイメントが完了しました: $stack_name"
}

# メイン処理
main() {
    log_info "=== CSR Lambda API System - 開発環境デプロイメント開始 ==="
    
    # 現在のディレクトリを確認
    if [[ ! -f "main.yaml" ]]; then
        log_error "main.yaml が見つかりません。infrastructure/dev ディレクトリで実行してください。"
        exit 1
    fi
    
    # AWS CLI の設定確認
    if ! aws sts get-caller-identity --region "$REGION" >/dev/null 2>&1; then
        log_error "AWS CLI が正しく設定されていません。認証情報を確認してください。"
        exit 1
    fi
    
    # パラメータの読み込み
    SHARED_PARAMS=$(load_parameters "../shared/parameters.json")
    DEV_PARAMS=$(load_parameters "parameters.json")
    ALL_PARAMS="$SHARED_PARAMS $DEV_PARAMS"
    
    # 1. ネットワークインフラストラクチャのデプロイ
    log_info "--- ステップ 1: ネットワークインフラストラクチャ ---"
    deploy_stack "${STACK_PREFIX}-network" "main.yaml" "$ALL_PARAMS" "CAPABILITY_NAMED_IAM"
    
    # 2. データベースのデプロイ
    log_info "--- ステップ 2: データベースインフラストラクチャ ---"
    # データベースパスワードの生成（初回のみ）
    DB_PASSWORD_PARAM=""
    if ! aws secretsmanager describe-secret --secret-id "${STACK_PREFIX}-db-credentials" --region "$REGION" >/dev/null 2>&1; then
        DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        DB_PASSWORD_PARAM="ParameterKey=DatabasePassword,ParameterValue=$DB_PASSWORD"
        log_info "新しいデータベースパスワードを生成しました"
    else
        log_info "既存のデータベース認証情報を使用します"
    fi
    
    deploy_stack "${STACK_PREFIX}-database" "database.yaml" "$ALL_PARAMS $DB_PASSWORD_PARAM" "CAPABILITY_NAMED_IAM"
    
    # 3. フロントエンドインフラストラクチャのデプロイ
    log_info "--- ステップ 3: フロントエンドインフラストラクチャ ---"
    deploy_stack "${STACK_PREFIX}-frontend" "frontend.yaml" "$ALL_PARAMS" "CAPABILITY_NAMED_IAM"
    
    # 4. API インフラストラクチャのデプロイ（Lambda コードが必要）
    log_info "--- ステップ 4: API インフラストラクチャ ---"
    
    # Lambda デプロイメントパッケージの確認
    LAMBDA_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-lambda-deployments-${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
    LAMBDA_KEY="lambda-deployment-package.zip"
    
    # S3バケットが存在しない場合は作成
    if ! aws s3 ls "s3://$LAMBDA_BUCKET" --region "$REGION" >/dev/null 2>&1; then
        log_info "Lambda デプロイメント用 S3 バケットを作成中: $LAMBDA_BUCKET"
        aws s3 mb "s3://$LAMBDA_BUCKET" --region "$REGION"
        aws s3api put-bucket-versioning --bucket "$LAMBDA_BUCKET" --versioning-configuration Status=Enabled --region "$REGION"
    fi
    
    # ダミーのLambdaパッケージを作成（実際のコードがない場合）
    if ! aws s3 ls "s3://$LAMBDA_BUCKET/$LAMBDA_KEY" --region "$REGION" >/dev/null 2>&1; then
        log_warning "Lambda デプロイメントパッケージが見つかりません。ダミーパッケージを作成します。"
        
        # 一時ディレクトリでダミーパッケージを作成
        TEMP_DIR=$(mktemp -d)
        cat > "$TEMP_DIR/lambda_handler.py" << 'EOF'
import json

def handler(event, context):
    """
    ダミーのLambda関数
    実際のアプリケーションコードに置き換える必要があります
    """
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': 'Hello from Lambda! Please deploy the actual application code.',
            'environment': 'dev'
        })
    }
EOF
        
        cd "$TEMP_DIR"
        zip -r lambda-deployment-package.zip .
        aws s3 cp lambda-deployment-package.zip "s3://$LAMBDA_BUCKET/$LAMBDA_KEY" --region "$REGION"
        cd - >/dev/null
        rm -rf "$TEMP_DIR"
        
        log_info "ダミーのLambdaパッケージをアップロードしました"
    fi
    
    # API スタックのデプロイ
    API_PARAMS="$ALL_PARAMS ParameterKey=LambdaCodeS3Bucket,ParameterValue=$LAMBDA_BUCKET ParameterKey=LambdaCodeS3Key,ParameterValue=$LAMBDA_KEY"
    deploy_stack "${STACK_PREFIX}-api" "api.yaml" "$API_PARAMS" "CAPABILITY_NAMED_IAM"
    
    # デプロイメント完了の確認
    log_success "=== 開発環境のデプロイメントが完了しました ==="
    
    # 重要な出力情報を表示
    log_info "--- デプロイメント情報 ---"
    
    # API Gateway URL
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_PREFIX}-api" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text 2>/dev/null || echo "取得できませんでした")
    echo "API Gateway URL: $API_URL"
    
    # S3 Website URL
    S3_URL=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_PREFIX}-frontend" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`FrontendS3BucketWebsiteURL`].OutputValue' \
        --output text 2>/dev/null || echo "取得できませんでした")
    echo "S3 Website URL: $S3_URL"
    
    # データベースエンドポイント
    DB_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_PREFIX}-database" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`DatabaseClusterEndpoint`].OutputValue' \
        --output text 2>/dev/null || echo "取得できませんでした")
    echo "Database Endpoint: $DB_ENDPOINT"
    
    log_info "--- 次のステップ ---"
    echo "1. 実際のLambdaアプリケーションコードをビルドして S3 にアップロード"
    echo "2. フロントエンドアプリケーションをビルドして S3 にデプロイ"
    echo "3. データベースの初期化とマイグレーション実行"
    echo "4. API とフロントエンドの動作確認"
}

# スクリプト実行
main "$@"