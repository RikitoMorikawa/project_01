# 本番環境インフラストラクチャ

CSR Lambda API システムの本番環境用 AWS インフラストラクチャです。

## 概要

本番環境では以下のリソースがデプロイされます：

- **VPC**: 10.2.0.0/16 CIDR、完全分離されたネットワーク
- **Aurora MySQL**: t3.medium インスタンス + Read Replica、Multi-AZ 配置、暗号化有効
- **Lambda**: 1024MB メモリ、Provisioned Concurrency、VPC 内実行、X-Ray トレーシング
- **API Gateway**: REST API、使用量プラン、キャッシング、スロットリング
- **S3**: 静的ウェブサイトホスティング、バージョニング、ライフサイクル管理
- **CloudFront**: 有効、WAF 統合、セキュリティヘッダー、API プロキシ機能
- **WAF**: 強化されたセキュリティルール、地理的ブロック、レート制限
- **監視**: 詳細な CloudWatch アラーム、ダッシュボード、SNS 通知
- **セキュリティ**: KMS 暗号化、VPC エンドポイント、Network ACL

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

本番環境デプロイを実行するユーザー/ロールには以下の権限が必要です：

- CloudFormation: フルアクセス
- IAM: ロール/ポリシー作成権限
- VPC: フルアクセス
- RDS: フルアクセス
- Lambda: フルアクセス
- API Gateway: フルアクセス
- S3: フルアクセス
- CloudFront: フルアクセス
- WAF: フルアクセス
- KMS: キー作成・管理権限
- Secrets Manager: フルアクセス
- CloudWatch: フルアクセス
- SNS: フルアクセス
- SQS: フルアクセス

## デプロイ手順

### 1. 事前準備

```bash
# 本番環境パラメータの確認
cat parameters.json

# 共通パラメータの確認
cat ../shared/parameters.json

# デプロイメント権限の確認
aws sts get-caller-identity
```

### 2. 本番環境デプロイメント

⚠️ **重要**: 本番環境デプロイメントは慎重に実行してください。

```bash
# 本番環境ディレクトリに移動
cd infrastructure/prod

# デプロイスクリプトの実行
./deploy.sh
```

デプロイスクリプトは以下の安全機能を含みます：

- 事前チェックと確認プロンプト
- 変更セットによる変更内容の事前確認
- 既存データベースの自動バックアップ
- 削除保護の自動有効化

### 3. デプロイメント確認

```bash
# スタックの状態確認
aws cloudformation describe-stacks --stack-name csr-lambda-api-prod-network
aws cloudformation describe-stacks --stack-name csr-lambda-api-prod-database
aws cloudformation describe-stacks --stack-name csr-lambda-api-prod-frontend
aws cloudformation describe-stacks --stack-name csr-lambda-api-prod-api

# リソースの確認
aws ec2 describe-vpcs --filters "Name=tag:Project,Values=csr-lambda-api" "Name=tag:Environment,Values=prod"
aws rds describe-db-clusters --db-cluster-identifier csr-lambda-api-prod-aurora-cluster
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `csr-lambda-api-prod`)]'
aws cloudfront list-distributions --query 'DistributionList.Items[?Comment==`csr-lambda-api prod CloudFront Distribution`]'
```

## 設定ファイル

### parameters.json

本番環境固有のパラメータ：

```json
{
  "Environment": "prod",
  "DatabaseInstanceClass": "db.t3.medium",
  "DatabaseMultiAZ": true,
  "LambdaMemorySize": 1024,
  "LambdaProvisionedConcurrency": 10,
  "CloudFrontEnabled": true,
  "WAFEnabled": true,
  "DatabaseName": "csr_lambda_prod",
  "DatabaseReadReplica": true,
  "VpcCidr": "10.2.0.0/16",
  "PublicSubnet1Cidr": "10.2.1.0/24",
  "PublicSubnet2Cidr": "10.2.2.0/24",
  "PrivateSubnet1Cidr": "10.2.3.0/24",
  "PrivateSubnet2Cidr": "10.2.4.0/24"
}
```

## CloudFormation テンプレート

### main.yaml

- VPC、サブネット、ルートテーブル、NAT Gateway（2 つ）
- VPC エンドポイント（S3、Secrets Manager）
- VPC フローログ（KMS 暗号化）
- Network ACL（追加セキュリティ）
- KMS キー（CloudWatch Logs 用）

### database.yaml

- Aurora MySQL クラスター（Multi-AZ + Read Replica）
- KMS 暗号化（専用キー）
- Enhanced Monitoring、Performance Insights
- 詳細な CloudWatch アラーム
- CloudWatch ダッシュボード
- SNS 通知（通常・クリティカル）

### api.yaml

- Lambda 関数（1024MB、Provisioned Concurrency）
- API Gateway（使用量プラン、キャッシング）
- X-Ray トレーシング、Dead Letter Queue
- 詳細な CloudWatch アラーム
- CloudWatch ダッシュボード
- KMS 暗号化（ログ・環境変数）

### frontend.yaml

- S3 バケット（暗号化、ライフサイクル管理）
- CloudFront（HTTP/3、セキュリティヘッダー）
- WAF（強化されたルール、地理的ブロック）
- CloudWatch ダッシュボード
- 詳細なアラーム設定

## 接続情報

### データベース接続

```bash
# データベース認証情報の取得
aws secretsmanager get-secret-value \
  --secret-id csr-lambda-api-prod-db-credentials \
  --query SecretString --output text | jq -r '.password'

# ライターエンドポイントの取得
aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-prod-database \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseClusterEndpoint`].OutputValue' \
  --output text

# リーダーエンドポイントの取得
aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-prod-database \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseClusterReadEndpoint`].OutputValue' \
  --output text
```

### API エンドポイント

```bash
# API Gateway URL の取得
aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-prod-api \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
  --output text
```

### フロントエンド URL

```bash
# CloudFront URL の取得
aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-prod-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionURL`].OutputValue' \
  --output text
```

## 監視とアラーム

### 設定されているアラーム

#### データベース

- CPU 使用率が 70% を超過（クリティカル）
- 接続数が 100 を超過（クリティカル）
- 読み取りレイテンシが 0.2 秒 を超過
- 書き込みレイテンシが 0.2 秒 を超過（クリティカル）

#### Lambda

- エラー数が 3 を超過（クリティカル）
- 実行時間が 20 秒 を超過
- スロットル数が 1 を超過（クリティカル）

#### API Gateway

- 4XX エラー数が 5 を超過
- 5XX エラー数が 1 を超過（クリティカル）
- レイテンシが 5 秒 を超過

#### CloudFront

- 4XX エラー率が 2% を超過
- 5XX エラー率が 1% を超過（クリティカル）
- オリジンレイテンシが 3 秒 を超過

#### WAF

- ブロックされたリクエスト数が 100 を超過

### アラーム通知の設定

```bash
# 通常アラーム SNS トピック
DB_TOPIC=$(aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-prod-database \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseAlarmTopicArn`].OutputValue' \
  --output text)

API_TOPIC=$(aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-prod-api \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiAlarmTopicArn`].OutputValue' \
  --output text)

FRONTEND_TOPIC=$(aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-prod-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendAlarmTopicArn`].OutputValue' \
  --output text)

# クリティカルアラーム SNS トピック
DB_CRITICAL_TOPIC=$(aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-prod-database \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseCriticalAlarmTopicArn`].OutputValue' \
  --output text)

API_CRITICAL_TOPIC=$(aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-prod-api \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiCriticalAlarmTopicArn`].OutputValue' \
  --output text)

FRONTEND_CRITICAL_TOPIC=$(aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-prod-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendCriticalAlarmTopicArn`].OutputValue' \
  --output text)

# メール通知の購読（例）
aws sns subscribe --topic-arn $DB_TOPIC --protocol email --notification-endpoint ops-team@company.com
aws sns subscribe --topic-arn $DB_CRITICAL_TOPIC --protocol email --notification-endpoint oncall@company.com
aws sns subscribe --topic-arn $API_TOPIC --protocol email --notification-endpoint dev-team@company.com
aws sns subscribe --topic-arn $API_CRITICAL_TOPIC --protocol email --notification-endpoint oncall@company.com
```

## セキュリティ機能

### 暗号化

- **データベース**: 専用 KMS キーによる暗号化
- **S3**: AES-256 暗号化
- **CloudWatch Logs**: 専用 KMS キーによる暗号化
- **Secrets Manager**: KMS 暗号化
- **SNS**: AWS 管理キーによる暗号化
- **SQS**: AWS 管理キーによる暗号化

### ネットワークセキュリティ

- **VPC エンドポイント**: S3、Secrets Manager への安全なアクセス
- **Network ACL**: プライベートサブネット用の追加セキュリティレイヤー
- **セキュリティグループ**: 最小権限の原則に基づく設定
- **VPC フローログ**: 全ネットワークトラフィックの監視

### WAF ルール

- **AWSManagedRulesCommonRuleSet**: 一般的な攻撃パターン
- **AWSManagedRulesKnownBadInputsRuleSet**: 既知の悪意のある入力
- **AWSManagedRulesAmazonIpReputationList**: 悪意のある IP アドレス
- **AWSManagedRulesLinuxRuleSet**: Linux 固有の攻撃パターン
- **レート制限**: IP あたり 5000 リクエスト/5 分
- **地理的ブロック**: 中国、ロシア、北朝鮮からのアクセスをブロック

### セキュリティヘッダー

CloudFront で以下のセキュリティヘッダーを自動付与：

- **Strict-Transport-Security**: HTTPS 強制
- **X-Content-Type-Options**: MIME タイプスニッフィング防止
- **X-Frame-Options**: クリックジャッキング防止
- **Referrer-Policy**: リファラー情報の制御
- **Content-Security-Policy**: XSS 攻撃防止
- **Permissions-Policy**: ブラウザ機能の制限

## パフォーマンス最適化

### Lambda 設定

- **メモリ**: 1024MB（高性能）
- **Provisioned Concurrency**: 10（コールドスタート回避）
- **予約済み同時実行数**: 500
- **接続プール**: 最適化された設定
- **X-Ray トレーシング**: パフォーマンス分析

### CloudFront 設定

- **HTTP/3 サポート**: 最新プロトコル
- **静的アセット**: 1 年間の長期キャッシュ
- **API リクエスト**: キャッシュ無効
- **Gzip 圧縮**: 有効
- **Price Class**: All（全世界配信）

### データベース設定

- **Multi-AZ + Read Replica**: 高可用性と読み取り性能向上
- **Enhanced Monitoring**: 詳細なパフォーマンス監視
- **Performance Insights**: クエリレベルの分析
- **自動バックアップ**: 30 日間保持

### API Gateway 設定

- **キャッシング**: 有効（5 分間）
- **スロットリング**: 500 RPS、1000 バースト
- **使用量プラン**: 1 日 100 万リクエスト制限

## 運用手順

### デプロイメント

```bash
# フロントエンドデプロイメント
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-prod-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendS3BucketName`].OutputValue' \
  --output text)

DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name csr-lambda-api-prod-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
  --output text)

# ファイルのアップロード
aws s3 sync ./frontend/build/ s3://$BUCKET_NAME/ --delete

# CloudFront キャッシュの無効化
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"
```

### バックアップ・復旧

```bash
# 手動スナップショット作成
aws rds create-db-cluster-snapshot \
  --db-cluster-identifier csr-lambda-api-prod-aurora-cluster \
  --db-cluster-snapshot-identifier manual-backup-$(date +%Y%m%d-%H%M%S)

# スナップショットからの復旧
aws rds restore-db-cluster-from-snapshot \
  --db-cluster-identifier csr-lambda-api-prod-aurora-cluster-restored \
  --snapshot-identifier <snapshot-id>
```

### ログ確認

```bash
# Lambda 関数ログ
aws logs tail /aws/lambda/csr-lambda-api-prod-api --follow

# API Gateway ログ
aws logs tail API-Gateway-Execution-Logs_<API-ID>/v1 --follow

# VPC フローログ
aws logs tail /aws/vpc/flowlogs/csr-lambda-api-prod --follow

# WAF ログ
aws logs tail /aws/wafv2/csr-lambda-api-prod --follow
```

### パフォーマンス監視

```bash
# CloudWatch ダッシュボードの確認
aws cloudwatch list-dashboards --dashboard-name-prefix csr-lambda-api-prod

# カスタムメトリクスの確認
aws cloudwatch list-metrics --namespace CSR-Lambda-API
```

## トラブルシューティング

### よくある問題

#### 1. CloudFront デプロイメントの遅延

CloudFront ディストリビューションの作成・更新には 15-30 分 かかります。

```bash
# デプロイメント状況の確認
aws cloudfront get-distribution --id <DISTRIBUTION-ID>
```

#### 2. WAF ルールによる正当なリクエストのブロック

```bash
# WAF ログの確認
aws logs filter-log-events \
  --log-group-name /aws/wafv2/csr-lambda-api-prod \
  --filter-pattern "{ $.action = \"BLOCK\" }"

# 特定のルールを一時的に無効化（緊急時のみ）
aws wafv2 update-web-acl \
  --scope CLOUDFRONT \
  --id <WEB-ACL-ID> \
  --name csr-lambda-api-prod-cloudfront-waf \
  --default-action Allow={} \
  --rules file://updated-rules.json
```

#### 3. Lambda Provisioned Concurrency の不足

```bash
# 同時実行数の監視
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name ConcurrentExecutions \
  --dimensions Name=FunctionName,Value=csr-lambda-api-prod-api \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 300 \
  --statistics Maximum

# Provisioned Concurrency の調整
aws lambda put-provisioned-concurrency-config \
  --function-name csr-lambda-api-prod-api \
  --qualifier prod \
  --provisioned-concurrency-limit 20
```

#### 4. データベース接続エラー

```bash
# データベース接続状況の確認
aws rds describe-db-clusters \
  --db-cluster-identifier csr-lambda-api-prod-aurora-cluster

# セキュリティグループの確認
aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=csr-lambda-api-prod-*-sg"
```

## 災害復旧

### RTO/RPO 目標

- **RTO (Recovery Time Objective)**: 4 時間
- **RPO (Recovery Point Objective)**: 1 時間

### 復旧手順

1. **データベース復旧**

   ```bash
   # 最新の自動バックアップから復旧
   aws rds restore-db-cluster-to-point-in-time \
     --source-db-cluster-identifier csr-lambda-api-prod-aurora-cluster \
     --db-cluster-identifier csr-lambda-api-prod-aurora-cluster-restored \
     --restore-to-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S.000Z)
   ```

2. **Lambda 関数復旧**

   ```bash
   # 最新のデプロイメントパッケージで再デプロイ
   aws lambda update-function-code \
     --function-name csr-lambda-api-prod-api \
     --s3-bucket csr-lambda-api-prod-lambda-deployments-<ACCOUNT-ID> \
     --s3-key lambda-deployment-package.zip
   ```

3. **CloudFront 復旧**
   ```bash
   # 新しいディストリビューションの作成（必要に応じて）
   aws cloudformation update-stack \
     --stack-name csr-lambda-api-prod-frontend \
     --use-previous-template \
     --capabilities CAPABILITY_NAMED_IAM
   ```

## セキュリティ監査

### 定期チェック項目

- [ ] IAM ロールと権限の最小化確認
- [ ] セキュリティグループルールの見直し
- [ ] WAF ルールの効果測定
- [ ] VPC フローログの分析
- [ ] アクセスログの監査
- [ ] 暗号化設定の確認
- [ ] バックアップの整合性確認

### コンプライアンス

本インフラストラクチャは以下の基準に準拠：

- **AWS Well-Architected Framework**
- **セキュリティピラー**: 暗号化、アクセス制御、監視
- **信頼性ピラー**: Multi-AZ、自動バックアップ、監視
- **パフォーマンス効率性ピラー**: 適切なインスタンスサイズ、キャッシング
- **コスト最適化ピラー**: 使用量ベースの課金、適切なリソースサイジング
- **運用上の優秀性ピラー**: 自動化、監視、ログ記録

## コスト見積もり

本番環境の月額コスト概算（東京リージョン）：

- **Aurora MySQL (t3.medium + Read Replica)**: ~$180
- **Lambda (1024MB + Provisioned Concurrency)**: ~$50
- **API Gateway (高トラフィック)**: ~$30
- **S3 (数百 GB)**: ~$15
- **CloudFront (グローバル配信)**: ~$50
- **NAT Gateway (2 つ)**: ~$90
- **WAF (リクエスト数による)**: ~$20
- **KMS (複数キー)**: ~$10
- **その他 (CloudWatch, SNS, VPC エンドポイント等)**: ~$25

**合計: 約 $470/月**

※実際のコストは使用量により大きく変動します。本番環境では高可用性とパフォーマンスを重視した設定のため、他の環境より高コストになります。

## サポート

本番環境で問題が発生した場合：

1. **緊急時**: クリティカルアラームの SNS 通知を確認
2. **CloudWatch ダッシュボード**: リアルタイム監視
3. **ログ分析**: CloudWatch Logs Insights を使用
4. **AWS サポート**: Business または Enterprise サポートプランの利用を推奨

本番環境の安定運用のため、定期的な監視とメンテナンスを実施してください。
