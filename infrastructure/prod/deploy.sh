#!/bin/bash

# CSR Lambda API System - Production Environment Deployment Script
# 本番環境のインフラストラクチャをデプロイするスクリプト

set -e

# 設定
PROJECT_NAME="csr-lambda-api"
ENVIRONMENT="prod"
REGION="ap-northeast-1"
STACK_PREFIX="${PROJECT_NAME}-${ENVIRONMENT}"

# カラー出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

log_critical() {
    echo -e "${PURPLE}[CRITICAL]${NC} $1"
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
        
        # 本番環境では変更セットを作成して確認
        CHANGESET_NAME="${stack_name}-changeset-$(date +%Y%m%d-%H%M%S)"
        log_info "変更セットを作成中: $CHANGESET_NAME"
        
        aws cloudformation create-change-set \
            --stack-name "$stack_name" \
            --change-set-name "$CHANGESET_NAME" \
            --template-body "file://$template_file" \
            --parameters $parameters \
            --capabilities $capabilities \
            --region "$REGION" \
            --tags Key=Project,Value="$PROJECT_NAME" Key=Environment,Value="$ENVIRONMENT" \
            || {
                log_error "変更セットの作成に失敗しました: $stack_name"
                exit 1
            }
        
        # 変更セットの内容を表示
        log_info "変更セットの内容を確認中..."
        aws cloudformation describe-change-set \
            --stack-name "$stack_name" \
            --change-set-name "$CHANGESET_NAME" \
            --region "$REGION" \
            --query 'Changes[].{Action:Action,ResourceType:ResourceChange.ResourceType,LogicalId:ResourceChange.LogicalResourceId,Replacement:ResourceChange.Replacement}' \
            --output table
        
        # 本番環境では手動確認を求める
        echo ""
        log_warning "本番環境への変更を実行しようとしています。"
        log_warning "上記の変更内容を確認してください。"
        read -p "変更を実行しますか？ (yes/no): " -r
        echo ""
        
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            log_info "デプロイメントがキャンセルされました。"
            aws cloudformation delete-change-set \
                --stack-name "$stack_name" \
                --change-set-name "$CHANGESET_NAME" \
                --region "$REGION"
            exit 0
        fi
        
        # 変更セットを実行
        aws cloudformation execute-change-set \
            --stack-name "$stack_name" \
            --change-set-name "$CHANGESET_NAME" \
            --region "$REGION" \
            || {
                log_error "変更セットの実行に失敗しました: $stack_name"
                exit 1
            }
    else
        log_info "新しいスタックを作成中: $stack_name"
        
        # 本番環境では新規作成時も確認
        log_warning "本番環境に新しいスタックを作成しようとしています: $stack_name"
        read -p "作成を実行しますか？ (yes/no): " -r
        echo ""
        
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            log_info "デプロイメントがキャンセルされました。"
            exit 0
        fi
        
        aws cloudformation create-stack \
            --stack-name "$stack_name" \
            --template-body "file://$template_file" \
            --parameters $parameters \
            --capabilities $capabilities \
            --region "$REGION" \
            --enable-termination-protection \
            --tags Key=Project,Value="$PROJECT_NAME" Key=Environment,Value="$ENVIRONMENT" Key=CostCenter,Value="Production" \
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

# 事前チェック
pre_deployment_checks() {
    log_info "=== 本番環境デプロイメント事前チェック開始 ==="
    
    # AWS CLI の設定確認
    if ! aws sts get-caller-identity --region "$REGION" >/dev/null 2>&1; then
        log_error "AWS CLI が正しく設定されていません。認証情報を確認してください。"
        exit 1
    fi
    
    # 必要なツールの確認
    for tool in jq openssl; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool がインストールされていません。"
            exit 1
        fi
    done
    
    # 本番環境の権限確認
    CALLER_IDENTITY=$(aws sts get-caller-identity --region "$REGION")
    USER_ARN=$(echo "$CALLER_IDENTITY" | jq -r '.Arn')
    ACCOUNT_ID=$(echo "$CALLER_IDENTITY" | jq -r '.Account')
    
    log_info "デプロイメント実行者: $USER_ARN"
    log_info "AWS アカウント ID: $ACCOUNT_ID"
    
    # 他の環境との重複チェック
    for env in dev staging; do
        VPC_ID=$(aws cloudformation describe-stacks \
            --stack-name "${PROJECT_NAME}-${env}-network" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`VPCId`].OutputValue' \
            --output text 2>/dev/null || echo "")
        
        if [[ -n "$VPC_ID" ]]; then
            log_info "${env} 環境のVPCが検出されました: $VPC_ID"
        fi
    done
    
    log_info "本番環境は異なるCIDRブロック（10.2.0.0/16）を使用します"
    
    # 本番環境デプロイメントの最終確認
    log_critical "本番環境へのデプロイメントを実行しようとしています。"
    log_critical "この操作は本番システムに影響を与える可能性があります。"
    echo ""
    read -p "本番環境デプロイメントを続行しますか？ (I-UNDERSTAND-THE-RISKS): " -r
    echo ""
    
    if [[ "$REPLY" != "I-UNDERSTAND-THE-RISKS" ]]; then
        log_info "デプロイメントがキャンセルされました。"
        exit 0
    fi
    
    log_success "事前チェック完了"
}

# バックアップ作成
create_backup() {
    log_info "=== 本番環境バックアップ作成 ==="
    
    # 既存のデータベースのスナップショット作成
    DB_CLUSTER_ID="${PROJECT_NAME}-${ENVIRONMENT}-aurora-cluster"
    if aws rds describe-db-clusters --db-cluster-identifier "$DB_CLUSTER_ID" --region "$REGION" >/dev/null 2>&1; then
        SNAPSHOT_ID="${DB_CLUSTER_ID}-backup-$(date +%Y%m%d-%H%M%S)"
        log_info "データベースのスナップショットを作成中: $SNAPSHOT_ID"
        
        aws rds create-db-cluster-snapshot \
            --db-cluster-identifier "$DB_CLUSTER_ID" \
            --db-cluster-snapshot-identifier "$SNAPSHOT_ID" \
            --region "$REGION" \
            --tags Key=Environment,Value="$ENVIRONMENT" Key=BackupType,Value="PreDeployment" \
            || log_warning "スナップショットの作成に失敗しました（データベースが存在しない可能性があります）"
    fi
    
    log_success "バックアップ作成完了"
}

# メイン処理
main() {
    log_info "=== CSR Lambda API System - 本番環境デプロイメント開始 ==="
    
    # 現在のディレクトリを確認
    if [[ ! -f "main.yaml" ]]; then
        log_error "main.yaml が見つかりません。infrastructure/prod ディレクトリで実行してください。"
        exit 1
    fi
    
    # 事前チェック
    pre_deployment_checks
    
    # バックアップ作成
    create_backup
    
    # パラメータの読み込み
    SHARED_PARAMS=$(load_parameters "../shared/parameters.json")
    PROD_PARAMS=$(load_parameters "parameters.json")
    ALL_PARAMS="$SHARED_PARAMS $PROD_PARAMS"
    
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
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    LAMBDA_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-lambda-deployments-${AWS_ACCOUNT_ID}"
    LAMBDA_KEY="lambda-deployment-package.zip"
    
    # S3バケットが存在しない場合は作成
    if ! aws s3 ls "s3://$LAMBDA_BUCKET" --region "$REGION" >/dev/null 2>&1; then
        log_info "Lambda デプロイメント用 S3 バケットを作成中: $LAMBDA_BUCKET"
        aws s3 mb "s3://$LAMBDA_BUCKET" --region "$REGION"
        aws s3api put-bucket-versioning --bucket "$LAMBDA_BUCKET" --versioning-configuration Status=Enabled --region "$REGION"
        aws s3api put-bucket-encryption --bucket "$LAMBDA_BUCKET" --server-side-encryption-configuration '{
            "Rules": [{
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }]
        }' --region "$REGION"
        aws s3api put-public-access-block --bucket "$LAMBDA_BUCKET" --public-access-block-configuration '{
            "BlockPublicAcls": true,
            "IgnorePublicAcls": true,
            "BlockPublicPolicy": true,
            "RestrictPublicBuckets": true
        }' --region "$REGION"
    fi
    
    # 本番環境では実際のLambdaコードが必要
    if ! aws s3 ls "s3://$LAMBDA_BUCKET/$LAMBDA_KEY" --region "$REGION" >/dev/null 2>&1; then
        log_error "本番環境用のLambdaデプロイメントパッケージが見つかりません: s3://$LAMBDA_BUCKET/$LAMBDA_KEY"
        log_error "実際のアプリケーションコードをビルドしてS3にアップロードしてください。"
        
        read -p "ダミーパッケージで続行しますか？ (yes/no): " -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            log_warning "ダミーのLambdaパッケージを作成します。"
            
            # 一時ディレクトリでダミーパッケージを作成
            TEMP_DIR=$(mktemp -d)
            cat > "$TEMP_DIR/lambda_handler.py" << 'EOF'
import json
import logging
import os

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    本番環境用ダミーのLambda関数
    実際のアプリケーションコードに置き換える必要があります
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # 本番環境であることを明示
    environment = os.environ.get('ENVIRONMENT', 'unknown')
    
    # CORS ヘッダーを含むレスポンス
    response = {
        'statusCode': 503,  # Service Unavailable
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps({
            'error': 'Service Unavailable',
            'message': 'Production Lambda function is not yet deployed. Please deploy the actual application code.',
            'environment': environment,
            'timestamp': context.aws_request_id,
            'path': event.get('path', '/'),
            'method': event.get('httpMethod', 'GET')
        })
    }
    
    logger.warning(f"Dummy Lambda function called in production environment: {environment}")
    return response
EOF
            
            cd "$TEMP_DIR"
            zip -r lambda-deployment-package.zip .
            aws s3 cp lambda-deployment-package.zip "s3://$LAMBDA_BUCKET/$LAMBDA_KEY" --region "$REGION"
            cd - >/dev/null
            rm -rf "$TEMP_DIR"
            
            log_warning "ダミーのLambdaパッケージをアップロードしました"
        else
            log_info "デプロイメントがキャンセルされました。"
            exit 0
        fi
    fi
    
    # API スタックのデプロイ
    API_PARAMS="$ALL_PARAMS ParameterKey=LambdaCodeS3Bucket,ParameterValue=$LAMBDA_BUCKET ParameterKey=LambdaCodeS3Key,ParameterValue=$LAMBDA_KEY"
    deploy_stack "${STACK_PREFIX}-api" "api.yaml" "$API_PARAMS" "CAPABILITY_NAMED_IAM"
    
    # デプロイメント完了の確認
    log_success "=== 本番環境のデプロイメントが完了しました ==="
    
    # 重要な出力情報を表示
    log_info "--- 本番環境デプロイメント情報 ---"
    
    # API Gateway URL
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_PREFIX}-api" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text 2>/dev/null || echo "取得できませんでした")
    echo "API Gateway URL: $API_URL"
    
    # CloudFront URL
    CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_PREFIX}-frontend" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionURL`].OutputValue' \
        --output text 2>/dev/null || echo "取得できませんでした")
    echo "CloudFront URL: $CLOUDFRONT_URL"
    
    # データベースエンドポイント
    DB_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_PREFIX}-database" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`DatabaseClusterEndpoint`].OutputValue' \
        --output text 2>/dev/null || echo "取得できませんでした")
    echo "Database Endpoint: $DB_ENDPOINT"
    
    # WAF Web ACL
    WAF_ACL=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_PREFIX}-frontend" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`WebACLArn`].OutputValue' \
        --output text 2>/dev/null || echo "取得できませんでした")
    echo "WAF Web ACL ARN: $WAF_ACL"
    
    log_info "--- 本番環境運用に向けた次のステップ ---"
    echo "1. 実際のLambdaアプリケーションコードをビルドして S3 にアップロード"
    echo "2. フロントエンドアプリケーションをビルドして S3 にデプロイ"
    echo "3. CloudFront キャッシュの無効化"
    echo "4. データベースの初期化とマイグレーション実行"
    echo "5. SSL証明書の設定（カスタムドメイン使用時）"
    echo "6. DNS設定の更新"
    echo "7. 監視アラームの通知先設定"
    echo "8. セキュリティテストの実行"
    echo "9. パフォーマンステストの実行"
    echo "10. 災害復旧手順の確認"
    
    log_info "--- 監視とアラーム設定 ---"
    echo "以下のSNSトピックにアラーム通知の購読者を追加してください："
    
    # アラームトピックの取得と表示
    for topic_type in "db-alarm-topic-arn" "db-critical-alarm-topic-arn" "api-alarm-topic-arn" "api-critical-alarm-topic-arn" "frontend-alarm-topic-arn" "frontend-critical-alarm-topic-arn"; do
        TOPIC_ARN=$(aws cloudformation describe-stacks \
            --region "$REGION" \
            --query "Stacks[?StackName==\`${STACK_PREFIX}-database\` || StackName==\`${STACK_PREFIX}-api\` || StackName==\`${STACK_PREFIX}-frontend\`].Outputs[?contains(OutputKey, \`$(echo $topic_type | sed 's/-/_/g' | tr '[:lower:]' '[:upper:]')\`)].OutputValue" \
            --output text 2>/dev/null || echo "")
        
        if [[ -n "$TOPIC_ARN" && "$TOPIC_ARN" != "None" ]]; then
            echo "  - $topic_type: $TOPIC_ARN"
        fi
    done
    
    log_critical "本番環境のデプロイメントが完了しました。"
    log_critical "運用開始前に必ず上記の手順を完了してください。"
}

# スクリプト実行
main "$@"