# 開発環境インフラストラクチャ

CSR Lambda API システムの開発環境用 AWS インフラストラクチャです。

## 概要

開発環境では以下のリソースがデプロイされます：

- **VPC**: 10.0.0.0/16 CIDR、パブリック/プライベートサブネット
- **Aurora MySQL**: t3.small インスタンス、暗号化有効
- **Lambda**: 128MB メモリ、VPC 内実行
- **API Gateway**: REST API、Lambda プロキシ統合
- **S3**: 静的ウェブサイトホスティング
- **CloudFront**: 無効（開発環境では直接 S3 アクセス）

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
- Secrets Manager: フルアクセス
- CloudWatch Logs: フルアクセス

## デプロイ手順

### 1. パラメータの確認

```bash
# 共通パラメータの確認
cat ../shared/parameters.json

# 開発環境パラメータの確認
cat parameters.json
```

### 2. インフラストラクチャのデプロイ

```bash
# 開発環境ディレクトリに移動
cd infrastructure/dev

# デプロイスクリプトの実行
./deploy.sh
```

### 3. デプロイメント確認

```bash
# スタックの状態確認
aws cloudformation describe-stacks --stack-name csr-lambda-api-dev-network
aws cloudformation describe-stacks --stack-name csr-lambda-api-dev-database
aws cloudformation describe-stacks --stack-name csr-lambda-api-dev-frontend
aws cloudformation describe-stacks --stack-name csr-lambda-api-dev-api

# リソースの確認
aws ec2 describe-vpcs --filters "Name=tag:Project,Values=csr-lambda-api"
aws rds describe-db-clusters --db-cluster-identifier csr-lambda-api-dev-aurora-cluster
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `csr-lambda-api-dev`)]'
```

## 設定ファイル

### parameters.json

開発環境固有のパラメータ：

```json
{
  "Environment": "dev",
  "DatabaseInstanceClass": "db.t3.small",
  "DatabaseMultiAZ": false,
  "LambdaMemorySize": 128,
  "LambdaProvisionedConcurrency": 0,
  "CloudFrontEnabled": false,
  "WAFEnabled": false,
  "DatabaseName": "csr_lambda_dev"
}
```

### ../shared/parameters.json

全環境共通のパラメータ：

```json
{
  "ProjectName": "csr-lambda-api",
  "Region": "ap-northeast-1",
  "VpcCidr": "10.0.0.0/16",
  "PublicSubnet1Cidr": "10.0.1.0/24",
  "PublicSubnet2Cidr": "10.0.2.0/24",
  "PrivateSubnet1Cidr": "10.0.3.0/24",
  "PrivateSubnet2Cidr": "10.0.4.0/24",
  "AvailabilityZone1": "ap-northeast-1a",
  "AvailabilityZone2": "ap-northeast-1c"
}
```

## CloudFormation テンプレート

### main.yaml

VPC、サブネット、ルートテーブル、NAT Gateway などのネットワークインフラストラクチャを定義。

### database.yaml

Aurora MySQL クラスター、セキュリティグループ、Secrets Manager を定義。

### api.yaml

Lambda 関数、API Gateway、IAM ロール、CloudWatch Logs を定義。

### frontend.yaml

S3 バケット、CloudFront ディストリビューション（オプション）、デプロイメント用 IAM ロールを定義。

## 接続情報

### データベース接続

```bash
# データベース認証情報の取得
aws secretsmanager get-secret-value \
  --secret-id csr-lambda-api-dev-db-credentials \
  --query SecretString --output text | jq -r '.password'

# データベースエンドポイントの取得
aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-dev-database \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseClusterEndpoint`].OutputValue' \
  --output text
```

### API エンドポイント

```bash
# API Gateway URL の取得
aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-dev-api \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text
```

### フロントエンド URL

```bash
# S3 Website URL の取得
aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-dev-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendS3BucketWebsiteURL`].OutputValue' \
  --output text
```

## トラブルシューティング

### よくある問題

#### 1. スタックの作成/更新に失敗

```bash
# エラーイベントの確認
aws cloudformation describe-stack-events \
  --stack-name <スタック名> \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`]'
```

#### 2. Lambda 関数のデプロイに失敗

```bash
# Lambda 関数のログ確認
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/csr-lambda-api-dev

# ログストリームの確認
aws logs describe-log-streams --log-group-name /aws/lambda/csr-lambda-api-dev-api
```

#### 3. データベース接続エラー

```bash
# セキュリティグループの確認
aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=csr-lambda-api-dev-*-sg"

# VPC エンドポイントの確認
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=<VPC-ID>"
```

### ログの確認

```bash
# CloudFormation スタックイベント
aws cloudformation describe-stack-events --stack-name <スタック名>

# Lambda 関数ログ
aws logs tail /aws/lambda/csr-lambda-api-dev-api --follow

# API Gateway ログ
aws logs tail API-Gateway-Execution-Logs_<API-ID>/v1 --follow
```

## クリーンアップ

開発環境のリソースを削除する場合：

```bash
# スタックの削除（依存関係の逆順）
aws cloudformation delete-stack --stack-name csr-lambda-api-dev-api
aws cloudformation delete-stack --stack-name csr-lambda-api-dev-frontend
aws cloudformation delete-stack --stack-name csr-lambda-api-dev-database
aws cloudformation delete-stack --stack-name csr-lambda-api-dev-network

# 削除完了の確認
aws cloudformation wait stack-delete-complete --stack-name csr-lambda-api-dev-api
aws cloudformation wait stack-delete-complete --stack-name csr-lambda-api-dev-frontend
aws cloudformation wait stack-delete-complete --stack-name csr-lambda-api-dev-database
aws cloudformation wait stack-delete-complete --stack-name csr-lambda-api-dev-network

# S3 バケットの手動削除（必要に応じて）
aws s3 rm s3://csr-lambda-api-dev-frontend-<ACCOUNT-ID> --recursive
aws s3 rb s3://csr-lambda-api-dev-frontend-<ACCOUNT-ID>
```

## セキュリティ考慮事項

### 開発環境での注意点

- データベースは暗号化されていますが、本番データは使用しないでください
- S3 バケットはパブリック読み取りアクセスが有効です
- CloudFront は無効化されており、直接 S3 アクセスとなります
- Lambda 関数は VPC 内で実行されますが、開発用の設定です

### 推奨事項

- 定期的にリソースの使用状況を確認
- 不要なリソースは削除してコストを削減
- 本番データは絶対に開発環境で使用しない
- アクセスキーやシークレットは適切に管理

## コスト見積もり

開発環境の月額コスト概算（東京リージョン）：

- Aurora MySQL (t3.small): ~$30
- Lambda (128MB, 軽微な使用): ~$1
- API Gateway (軽微な使用): ~$1
- S3 (数 GB): ~$1
- NAT Gateway: ~$45
- その他 (CloudWatch Logs 等): ~$5

**合計: 約 $83/月**

※実際のコストは使用量により変動します。
