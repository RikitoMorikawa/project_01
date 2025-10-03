# デプロイメントガイド

## 概要

このドキュメントは、CSR Lambda API システムの本番環境へのデプロイメント手順を説明します。

## 前提条件

### 必要なツール

- AWS CLI v2.x
- Node.js 18.x 以上
- Python 3.11
- Docker
- Git

### AWS アカウント設定

- AWS アカウント: 3165071@gmail.com
- リージョン: ap-northeast-1 (東京)
- 必要な IAM 権限:
  - CloudFormation フルアクセス
  - Lambda フルアクセス
  - API Gateway フルアクセス
  - S3 フルアクセス
  - CloudFront フルアクセス
  - RDS フルアクセス
  - VPC フルアクセス
  - IAM 管理権限

## 環境別デプロイメント

### 1. 開発環境 (dev)

#### 1.1 環境変数の設定

```bash
# AWS 認証情報の設定
export AWS_PROFILE=default
export AWS_REGION=ap-northeast-1

# 開発環境固有の設定
export ENVIRONMENT=dev
export PROJECT_NAME=csr-lambda-api
export STACK_NAME=${PROJECT_NAME}-${ENVIRONMENT}
```

#### 1.2 インフラストラクチャのデプロイ

```bash
# 開発環境ディレクトリに移動
cd infrastructure/dev

# パラメータファイルの確認・編集
vim parameters.json

# CloudFormation スタックのデプロイ
./deploy.sh

# デプロイ状況の確認
aws cloudformation describe-stacks --stack-name ${STACK_NAME}
```

#### 1.3 アプリケーションのデプロイ

```bash
# バックエンドのビルドとデプロイ
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v

# Lambda 関数の更新
aws lambda update-function-code \
  --function-name ${STACK_NAME}-api-function \
  --zip-file fileb://deployment-package.zip

# フロントエンドのビルドとデプロイ
cd ../frontend
npm install
npm run build
npm run export

# S3 への静的ファイルアップロード
aws s3 sync out/ s3://${STACK_NAME}-frontend-bucket/ --delete
```

### 2. ステージング環境 (staging)

#### 2.1 環境変数の設定

```bash
export ENVIRONMENT=staging
export STACK_NAME=${PROJECT_NAME}-${ENVIRONMENT}
```

#### 2.2 インフラストラクチャのデプロイ

```bash
cd infrastructure/staging
./deploy.sh
```

#### 2.3 アプリケーションのデプロイ

```bash
# CI/CD パイプライン経由でのデプロイ
# main ブランチへのマージで自動実行される

# 手動デプロイの場合
cd scripts
./build-and-deploy.sh staging
```

### 3. 本番環境 (prod)

#### 3.1 事前チェックリスト

- [ ] ステージング環境でのテストが完了している
- [ ] セキュリティスキャンが完了している
- [ ] パフォーマンステストが完了している
- [ ] データベースバックアップが取得されている
- [ ] ロールバック手順が準備されている

#### 3.2 環境変数の設定

```bash
export ENVIRONMENT=prod
export STACK_NAME=${PROJECT_NAME}-${ENVIRONMENT}
```

#### 3.3 インフラストラクチャのデプロイ

```bash
cd infrastructure/prod

# 本番用パラメータの確認
vim parameters.json

# 本番環境デプロイ（承認ゲート付き）
./deploy.sh

# デプロイ後の確認
aws cloudformation describe-stacks --stack-name ${STACK_NAME}
```

#### 3.4 アプリケーションのデプロイ

```bash
# 本番デプロイスクリプトの実行
cd scripts
./build-and-deploy.sh prod

# デプロイ後の動作確認
python backend/tests/production/test_production_health.py
```

## CI/CD パイプライン

### GitHub Actions ワークフロー

#### 開発環境 (dev ブランチ)

```yaml
# .github/workflows/dev-deploy.yml
name: Deploy to Development
on:
  push:
    branches: [dev]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: "18"
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Deploy to Dev
        run: |
          cd scripts
          ./build-and-deploy.sh dev
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

#### ステージング環境 (main ブランチ)

```yaml
# .github/workflows/staging-deploy.yml
name: Deploy to Staging
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: |
          cd backend
          pip install -r requirements.txt
          python -m pytest tests/ -v

          cd ../frontend
          npm install
          npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Staging
        run: |
          cd scripts
          ./build-and-deploy.sh staging
```

#### 本番環境 (手動トリガー)

```yaml
# .github/workflows/prod-deploy.yml
name: Deploy to Production
on:
  workflow_dispatch:
    inputs:
      version:
        description: "Version to deploy"
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to Production
        run: |
          cd scripts
          ./build-and-deploy.sh prod
```

## データベース管理

### マイグレーション

```bash
# マイグレーションファイルの作成
cd backend
python manage_db.py create_migration "migration_name"

# マイグレーションの実行
python manage_db.py migrate

# マイグレーション状態の確認
python manage_db.py status
```

### バックアップ

```bash
# 本番データベースのバックアップ
aws rds create-db-snapshot \
  --db-instance-identifier ${STACK_NAME}-aurora-cluster \
  --db-snapshot-identifier ${STACK_NAME}-backup-$(date +%Y%m%d-%H%M%S)

# バックアップの確認
aws rds describe-db-snapshots \
  --db-instance-identifier ${STACK_NAME}-aurora-cluster
```

## 監視とアラート

### CloudWatch ダッシュボード

```bash
# ダッシュボードの作成
aws cloudwatch put-dashboard \
  --dashboard-name "${STACK_NAME}-dashboard" \
  --dashboard-body file://monitoring/dashboard.json
```

### アラートの設定

```bash
# Lambda エラー率アラート
aws cloudwatch put-metric-alarm \
  --alarm-name "${STACK_NAME}-lambda-error-rate" \
  --alarm-description "Lambda function error rate" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=${STACK_NAME}-api-function \
  --evaluation-periods 2

# Aurora 接続数アラート
aws cloudwatch put-metric-alarm \
  --alarm-name "${STACK_NAME}-aurora-connections" \
  --alarm-description "Aurora connection count" \
  --metric-name DatabaseConnections \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=DBClusterIdentifier,Value=${STACK_NAME}-aurora-cluster \
  --evaluation-periods 2
```

## セキュリティ設定

### WAF ルールの設定

```bash
# WAF Web ACL の作成
aws wafv2 create-web-acl \
  --name "${STACK_NAME}-waf" \
  --scope CLOUDFRONT \
  --default-action Allow={} \
  --rules file://security/waf-rules.json
```

### SSL 証明書の管理

```bash
# 証明書の有効期限確認
aws acm list-certificates \
  --certificate-statuses ISSUED \
  --query 'CertificateSummaryList[?DomainName==`example.com`]'

# 証明書の更新（Let's Encrypt の場合）
certbot renew --dry-run
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. Lambda コールドスタート問題

```bash
# Provisioned Concurrency の設定
aws lambda put-provisioned-concurrency-config \
  --function-name ${STACK_NAME}-api-function \
  --qualifier $LATEST \
  --provisioned-concurrency-units 5
```

#### 2. Aurora 接続エラー

```bash
# セキュリティグループの確認
aws ec2 describe-security-groups \
  --group-ids sg-xxxxxxxxx

# VPC エンドポイントの確認
aws ec2 describe-vpc-endpoints \
  --filters Name=service-name,Values=com.amazonaws.ap-northeast-1.rds
```

#### 3. CloudFront キャッシュ問題

```bash
# キャッシュの無効化
aws cloudfront create-invalidation \
  --distribution-id EDFDVBD6EXAMPLE \
  --paths "/*"
```

### ログの確認

```bash
# Lambda ログの確認
aws logs describe-log-groups \
  --log-group-name-prefix "/aws/lambda/${STACK_NAME}"

aws logs tail "/aws/lambda/${STACK_NAME}-api-function" --follow

# Aurora ログの確認
aws rds describe-db-log-files \
  --db-instance-identifier ${STACK_NAME}-aurora-cluster

# CloudFront ログの確認
aws s3 ls s3://${STACK_NAME}-cloudfront-logs/
```

## ロールバック手順

### アプリケーションのロールバック

```bash
# Lambda 関数の前バージョンへのロールバック
aws lambda update-alias \
  --function-name ${STACK_NAME}-api-function \
  --name LIVE \
  --function-version $PREVIOUS_VERSION

# S3 静的ファイルのロールバック
aws s3 sync s3://${STACK_NAME}-frontend-backup/ s3://${STACK_NAME}-frontend-bucket/ --delete
```

### インフラストラクチャのロールバック

```bash
# CloudFormation スタックのロールバック
aws cloudformation cancel-update-stack --stack-name ${STACK_NAME}

# 前のスタック状態への復元
aws cloudformation continue-update-rollback --stack-name ${STACK_NAME}
```

### データベースのロールバック

```bash
# スナップショットからの復元
aws rds restore-db-cluster-from-snapshot \
  --db-cluster-identifier ${STACK_NAME}-aurora-cluster-restored \
  --snapshot-identifier ${STACK_NAME}-backup-20240101-120000
```

## パフォーマンス最適化

### Lambda 最適化

```bash
# メモリサイズの調整
aws lambda update-function-configuration \
  --function-name ${STACK_NAME}-api-function \
  --memory-size 1024

# タイムアウトの調整
aws lambda update-function-configuration \
  --function-name ${STACK_NAME}-api-function \
  --timeout 30
```

### Aurora 最適化

```bash
# インスタンスクラスの変更
aws rds modify-db-cluster \
  --db-cluster-identifier ${STACK_NAME}-aurora-cluster \
  --db-cluster-instance-class db.t3.medium \
  --apply-immediately
```

### CloudFront 最適化

```bash
# キャッシュ設定の更新
aws cloudfront update-distribution \
  --id EDFDVBD6EXAMPLE \
  --distribution-config file://cloudfront-config.json
```

## 定期メンテナンス

### 日次タスク

- [ ] アプリケーションログの確認
- [ ] エラー率の監視
- [ ] パフォーマンスメトリクスの確認

### 週次タスク

- [ ] セキュリティアップデートの確認
- [ ] データベースバックアップの確認
- [ ] 依存関係の脆弱性スキャン

### 月次タスク

- [ ] SSL 証明書の有効期限確認
- [ ] コスト分析とリソース最適化
- [ ] 災害復旧テストの実行

## 緊急時対応

### 障害対応フロー

1. **障害検知**

   - CloudWatch アラートの確認
   - ヘルスチェックエンドポイントの確認

2. **初期対応**

   - 影響範囲の特定
   - 関係者への通知

3. **復旧作業**

   - ロールバックの実行
   - 代替手段の検討

4. **事後対応**
   - 根本原因の分析
   - 再発防止策の実装

### 緊急連絡先

- システム管理者: [連絡先]
- AWS サポート: [サポートケース作成]
- 開発チーム: [Slack チャンネル]

## 参考資料

- [AWS Lambda ベストプラクティス](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Aurora MySQL パフォーマンスチューニング](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Aurora.BestPractices.html)
- [CloudFront 最適化ガイド](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/optimization.html)
