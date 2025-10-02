# ステージング環境インフラストラクチャ

CSR Lambda API システムのステージング環境用 AWS インフラストラクチャです。

## 概要

ステージング環境では以下のリソースがデプロイされます：

- **VPC**: 10.1.0.0/16 CIDR、開発環境と完全分離
- **Aurora MySQL**: t3.small インスタンス、Multi-AZ 配置、暗号化有効
- **Lambda**: 512MB メモリ、VPC 内実行、X-Ray トレーシング有効
- **API Gateway**: REST API、Lambda プロキシ統合、リクエストバリデーション
- **S3**: 静的ウェブサイトホスティング、バージョニング有効
- **CloudFront**: 有効、WAF 統合、API プロキシ機能
- **WAF**: 基本的なセキュリティルール、レート制限
- **監視**: CloudWatch アラーム、SNS 通知

## 前提条件

### 必要なツール

- AWS CLI v2
- jq
- bash
- openssl

### AWS 設定

```bash
# AWS CLI の設定
aws configure set region ap-northeast-1
aws configure set output json

# 認証情報の確認
aws sts get-caller-identity
```

### 必要な権限

デプロイを実行するユーザー/ロールには以下の権限が必要です：

- CloudFormation: フルアクセス
- IAM: ロール/ポリシー作成権限
- VPC: フルアクセス
- RDS: フルアクセス
- Lambda: フルアクセス
- API Gateway: フルアクセス
- S3: フルアクセス
- CloudFront: フルアクセス
- WAF: フルアクセス
- Secrets Manager: フルアクセス
- CloudWatch: フルアクセス
- SNS: フルアクセス
- SQS: フルアクセス

## デプロイ手順

### 1. パラメータの確認

```bash
# 共通パラメータの確認
cat ../shared/parameters.json

# ステージング環境パラメータの確認
cat parameters.json
```

### 2. インフラストラクチャのデプロイ

```bash
# ステージング環境ディレクトリに移動
cd infrastructure/staging

# デプロイスクリプトの実行
./deploy.sh
```

### 3. デプロイメント確認

```bash
# スタックの状態確認
aws cloudformation describe-stacks --stack-name csr-lambda-api-staging-network
aws cloudformation describe-stacks --stack-name csr-lambda-api-staging-database
aws cloudformation describe-stacks --stack-name csr-lambda-api-staging-frontend
aws cloudformation describe-stacks --stack-name csr-lambda-api-staging-api

# リソースの確認
aws ec2 describe-vpcs --filters "Name=tag:Project,Values=csr-lambda-api" "Name=tag:Environment,Values=staging"
aws rds describe-db-clusters --db-cluster-identifier csr-lambda-api-staging-aurora-cluster
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `csr-lambda-api-staging`)]'
aws cloudfront list-distributions --query 'DistributionList.Items[?Comment==`csr-lambda-api staging CloudFront Distribution`]'
```

## 設定ファイル

### parameters.json

ステージング環境固有のパラメータ：

```json
{
  "Environment": "staging",
  "DatabaseInstanceClass": "db.t3.small",
  "DatabaseMultiAZ": true,
  "LambdaMemorySize": 512,
  "LambdaProvisionedConcurrency": 0,
  "CloudFrontEnabled": true,
  "WAFEnabled": true,
  "DatabaseName": "csr_lambda_staging",
  "VpcCidr": "10.1.0.0/16",
  "PublicSubnet1Cidr": "10.1.1.0/24",
  "PublicSubnet2Cidr": "10.1.2.0/24",
  "PrivateSubnet1Cidr": "10.1.3.0/24",
  "PrivateSubnet2Cidr": "10.1.4.0/24"
}
```

## CloudFormation テンプレート

### main.yaml

VPC、サブネット、ルートテーブル、NAT Gateway（2 つ）、VPC フローログなどのネットワークインフラストラクチャを定義。

### database.yaml

Aurora MySQL クラスター（Multi-AZ）、セキュリティグループ、Secrets Manager、CloudWatch アラーム、SNS 通知を定義。

### api.yaml

Lambda 関数（512MB）、API Gateway、IAM ロール、CloudWatch Logs、X-Ray トレーシング、Dead Letter Queue、アラームを定義。

### frontend.yaml

S3 バケット、CloudFront ディストリビューション、WAF、デプロイメント用 IAM ロール、アラームを定義。

## 接続情報

### データベース接続

```bash
# データベース認証情報の取得
aws secretsmanager get-secret-value \
  --secret-id csr-lambda-api-staging-db-credentials \
  --query SecretString --output text | jq -r '.password'

# データベースエンドポイントの取得
aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-staging-database \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseClusterEndpoint`].OutputValue' \
  --output text

# 読み取り専用エンドポイントの取得
aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-staging-database \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseClusterReadEndpoint`].OutputValue' \
  --output text
```

### API エンドポイント

```bash
# API Gateway URL の取得
aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-staging-api \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text
```

### フロントエンド URL

```bash
# CloudFront URL の取得
aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-staging-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionURL`].OutputValue' \
  --output text

# S3 Website URL の取得
aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-staging-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendS3BucketWebsiteURL`].OutputValue' \
  --output text
```

## 監視とアラーム

### 設定されているアラーム

#### データベース

- CPU 使用率が 80% を超過
- 接続数が 80 を超過

#### Lambda

- エラー数が 5 を超過（5 分間で 2 回）
- 実行時間が 25 秒 を超過

#### API Gateway

- 4XX エラー数が 10 を超過（5 分間で 2 回）

#### CloudFront

- 4XX エラー率が 5% を超過

### アラーム通知の設定

```bash
# データベースアラーム SNS トピックの取得
DB_TOPIC_ARN=$(aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-staging-database \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseAlarmTopicArn`].OutputValue' \
  --output text)

# API アラーム SNS トピックの取得
API_TOPIC_ARN=$(aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-staging-api \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiAlarmTopicArn`].OutputValue' \
  --output text)

# フロントエンドアラーム SNS トピックの取得
FRONTEND_TOPIC_ARN=$(aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-staging-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendAlarmTopicArn`].OutputValue' \
  --output text)

# メール通知の購読
aws sns subscribe --topic-arn $DB_TOPIC_ARN --protocol email --notification-endpoint your-email@example.com
aws sns subscribe --topic-arn $API_TOPIC_ARN --protocol email --notification-endpoint your-email@example.com
aws sns subscribe --topic-arn $FRONTEND_TOPIC_ARN --protocol email --notification-endpoint your-email@example.com
```

## セキュリティ機能

### WAF ルール

- **AWSManagedRulesCommonRuleSet**: 一般的な攻撃パターンをブロック
- **AWSManagedRulesKnownBadInputsRuleSet**: 既知の悪意のある入力をブロック
- **レート制限**: IP あたり 2000 リクエスト/5 分

### ネットワークセキュリティ

- VPC フローログ有効
- プライベートサブネットでのデータベース配置
- セキュリティグループによる最小権限アクセス
- NAT Gateway による安全なアウトバウンド通信

### データ保護

- Aurora 暗号化有効（AWS KMS）
- S3 バケット暗号化
- CloudFront HTTPS 強制
- Secrets Manager による認証情報管理

## パフォーマンス最適化

### Lambda 設定

- メモリ: 512MB（開発環境の 4 倍）
- タイムアウト: 30 秒
- 予約済み同時実行数: 100
- X-Ray トレーシング有効
- Dead Letter Queue 設定

### CloudFront 設定

- 静的アセット長期キャッシュ（1 年）
- API リクエスト キャッシュ無効
- Gzip 圧縮有効
- HTTP/2 サポート

### データベース設定

- Multi-AZ 配置による高可用性
- Enhanced Monitoring 有効
- Performance Insights 有効
- 自動バックアップ（14 日間保持）

## トラブルシューティング

### よくある問題

#### 1. CloudFront デプロイメントの遅延

CloudFront ディストリビューションの作成には 15-20 分 かかります。

```bash
# デプロイメント状況の確認
aws cloudfront get-distribution --id <DISTRIBUTION-ID>
```

#### 2. WAF ルールによるブロック

```bash
# WAF ログの確認
aws logs describe-log-groups --log-group-name-prefix aws-waf-logs

# ブロックされたリクエストの確認
aws logs filter-log-events \
  --log-group-name aws-waf-logs-cloudfront \
  --filter-pattern "{ $.action = \"BLOCK\" }"
```

#### 3. Lambda コールドスタート

```bash
# Lambda メトリクスの確認
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=csr-lambda-api-staging-api \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 300 \
  --statistics Average,Maximum
```

### ログの確認

```bash
# Lambda 関数ログ
aws logs tail /aws/lambda/csr-lambda-api-staging-api --follow

# API Gateway ログ
aws logs tail API-Gateway-Execution-Logs_<API-ID>/v1 --follow

# VPC フローログ
aws logs tail /aws/vpc/flowlogs/csr-lambda-api-staging --follow

# CloudFront アクセスログ（S3）
aws s3 ls s3://csr-lambda-api-staging-cloudfront-logs-<ACCOUNT-ID>/cloudfront-logs/
```

## デプロイメント自動化

### CI/CD パイプライン連携

```bash
# デプロイメント用 IAM ロール ARN の取得
DEPLOYMENT_ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-staging-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`DeploymentRoleArn`].OutputValue' \
  --output text)

echo "CI/CD パイプラインで使用するロール ARN: $DEPLOYMENT_ROLE_ARN"
```

### フロントエンドデプロイメント

```bash
# S3 バケット名の取得
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-staging-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendS3BucketName`].OutputValue' \
  --output text)

# CloudFront ディストリビューション ID の取得
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-staging-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
  --output text)

# フロントエンドファイルのアップロード
aws s3 sync ./frontend/build/ s3://$BUCKET_NAME/ --delete

# CloudFront キャッシュの無効化
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"
```

## クリーンアップ

ステージング環境のリソースを削除する場合：

```bash
# 削除保護の無効化（必要に応じて）
aws cloudformation update-termination-protection \
  --stack-name csr-lambda-api-staging-network \
  --no-enable-termination-protection

# スタックの削除（依存関係の逆順）
aws cloudformation delete-stack --stack-name csr-lambda-api-staging-api
aws cloudformation delete-stack --stack-name csr-lambda-api-staging-frontend
aws cloudformation delete-stack --stack-name csr-lambda-api-staging-database
aws cloudformation delete-stack --stack-name csr-lambda-api-staging-network

# 削除完了の確認
aws cloudformation wait stack-delete-complete --stack-name csr-lambda-api-staging-api
aws cloudformation wait stack-delete-complete --stack-name csr-lambda-api-staging-frontend
aws cloudformation wait stack-delete-complete --stack-name csr-lambda-api-staging-database
aws cloudformation wait stack-delete-complete --stack-name csr-lambda-api-staging-network

# S3 バケットの手動削除
aws s3 rm s3://csr-lambda-api-staging-frontend-<ACCOUNT-ID> --recursive
aws s3 rb s3://csr-lambda-api-staging-frontend-<ACCOUNT-ID>
aws s3 rm s3://csr-lambda-api-staging-cloudfront-logs-<ACCOUNT-ID> --recursive
aws s3 rb s3://csr-lambda-api-staging-cloudfront-logs-<ACCOUNT-ID>
```

## コスト見積もり

ステージング環境の月額コスト概算（東京リージョン）：

- Aurora MySQL (t3.small, Multi-AZ): ~$60
- Lambda (512MB, 中程度の使用): ~$5
- API Gateway (中程度の使用): ~$5
- S3 (数十 GB): ~$3
- CloudFront (中程度のトラフィック): ~$10
- NAT Gateway (2 つ): ~$90
- WAF (リクエスト数による): ~$5
- その他 (CloudWatch, SNS 等): ~$10

**合計: 約 $188/月**

※実際のコストは使用量により変動します。本番環境に近い設定のため、開発環境より高コストになります。
