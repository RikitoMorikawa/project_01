# CSR Lambda API System - 本番環境デプロイメントガイド

## 概要

このドキュメントは、CSR Lambda API システムの本番環境への安全で確実なデプロイメントを実行するための包括的なガイドです。

## 前提条件

### 必要なツール

- AWS CLI v2.x 以上
- jq (JSON プロセッサ)
- Node.js 18.x 以上
- Python 3.11 以上
- Git

### AWS アカウント要件

- 本番環境専用の AWS アカウント（推奨）
- 適切な IAM 権限を持つユーザー/ロール
- 請求アラートの設定
- AWS Organizations での管理（推奨）

### 必要な権限

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "lambda:*",
        "apigateway:*",
        "rds:*",
        "s3:*",
        "cloudfront:*",
        "wafv2:*",
        "cognito-idp:*",
        "iam:*",
        "logs:*",
        "cloudwatch:*",
        "sns:*",
        "sqs:*",
        "secretsmanager:*",
        "ssm:*",
        "kms:*",
        "ec2:*",
        "application-autoscaling:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## デプロイメント前チェックリスト

### 1. 環境設定

- [ ] AWS CLI の設定確認
- [ ] 本番環境用 AWS プロファイルの設定
- [ ] リージョン設定の確認（ap-northeast-1）
- [ ] 必要な環境変数の設定

```bash
export NotificationEmail="admin@your-domain.com"
export LambdaCodeS3Bucket="csr-lambda-api-prod-lambda-code"
export FrontendCodeS3Bucket="csr-lambda-api-prod-frontend-code"
export SlackWebhookUrl="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
```

### 2. コード準備

- [ ] 最新のコードをプルダウン
- [ ] テストの実行と成功確認
- [ ] セキュリティスキャンの実行
- [ ] 依存関係の脆弱性チェック
- [ ] コードレビューの完了

### 3. 設定ファイル確認

- [ ] `parameters.json` の本番環境用設定確認
- [ ] `.env.prod.enhanced` の設定確認
- [ ] SSL 証明書の準備（カスタムドメイン使用時）
- [ ] DNS 設定の準備

### 4. バックアップ・復旧計画

- [ ] 既存システムのバックアップ（該当する場合）
- [ ] ロールバック手順の確認
- [ ] 災害復旧計画の確認
- [ ] データ移行計画の確認（該当する場合）

## デプロイメント手順

### Phase 1: 準備フェーズ

1. **リポジトリの準備**

   ```bash
   git clone https://github.com/RikitoMorikawa/project_01.git
   cd project_01/infrastructure/prod
   ```

2. **権限確認**

   ```bash
   aws sts get-caller-identity
   aws iam get-user
   ```

3. **パラメータ設定**

   ```bash
   # parameters.json を本番環境用に編集
   vim parameters.json

   # 必要な環境変数を設定
   source ./set-prod-env.sh
   ```

### Phase 2: インフラストラクチャデプロイ

1. **デプロイスクリプト実行**

   ```bash
   chmod +x deploy-enhanced.sh
   ./deploy-enhanced.sh
   ```

2. **デプロイ進行状況の監視**
   - AWS CloudFormation コンソールでスタック作成状況を監視
   - CloudWatch Logs でエラーログを確認
   - 各フェーズの完了を確認

### Phase 3: 検証フェーズ

1. **基本機能テスト**

   ```bash
   # API ヘルスチェック
   curl -f https://your-api-gateway-url/health

   # フロントエンド確認
   curl -f https://your-cloudfront-url
   ```

2. **認証機能テスト**

   - Cognito ユーザープールの動作確認
   - JWT トークンの検証
   - 認証フローのテスト

3. **データベース接続テスト**
   - Aurora クラスターへの接続確認
   - 読み取り専用レプリカの動作確認
   - パフォーマンス確認

### Phase 4: 監視・アラート設定

1. **CloudWatch ダッシュボード確認**

   - メトリクスの表示確認
   - アラームの設定確認
   - ログの収集確認

2. **通知設定テスト**
   - SNS トピックのテスト
   - Slack 通知のテスト
   - メール通知のテスト

## 本番環境設定詳細

### Lambda 関数設定

- **メモリサイズ**: 1024MB
- **タイムアウト**: 30 秒
- **予約済み同時実行数**: 500
- **Provisioned Concurrency**: 10（初期値）
- **Auto Scaling**: 有効（5-50 の範囲）

### データベース設定

- **インスタンスクラス**: db.t3.medium
- **マルチ AZ**: 有効
- **読み取り専用レプリカ**: 有効
- **バックアップ保持期間**: 30 日
- **暗号化**: 有効

### API Gateway 設定

- **スロットリング**: 500 req/sec（バースト: 1000）
- **キャッシング**: 有効（TTL: 300 秒）
- **WAF**: 有効
- **ログ記録**: 有効

### CloudFront 設定

- **価格クラス**: PriceClass_All
- **キャッシュ動作**: 最適化済み
- **圧縮**: 有効
- **セキュリティヘッダー**: 設定済み

## 監視・アラート設定

### クリティカルアラート

- Lambda エラー（1 件以上）
- API Gateway 5xx エラー（1 件以上）
- データベース CPU 使用率（90%以上）
- CloudFront エラー率（5%以上）

### 高優先度アラート

- Lambda 実行時間（20 秒以上）
- API Gateway レイテンシ（5 秒以上）
- データベース接続数（180 以上）
- Provisioned Concurrency 使用率（80%以上）

### 中優先度アラート

- Lambda メモリ使用率（85%以上）
- API Gateway 4xx エラー（10 件以上）
- データベースレプリケーション遅延（1 秒以上）
- CloudFront キャッシュヒット率（70%未満）

## セキュリティ設定

### ネットワークセキュリティ

- VPC 内でのプライベート通信
- セキュリティグループによる最小権限アクセス
- Network ACL による追加保護
- VPC Flow Logs による監視

### データ暗号化

- Aurora クラスター暗号化（KMS）
- S3 バケット暗号化（AES-256）
- CloudWatch Logs 暗号化（KMS）
- Secrets Manager 暗号化（KMS）

### アクセス制御

- IAM ロールによる最小権限の原則
- Cognito による認証・認可
- API Gateway オーソライザー
- WAF による悪意のあるトラフィック防御

## パフォーマンス最適化

### Lambda 最適化

- Provisioned Concurrency によるコールドスタート対策
- 接続プールによるデータベース接続最適化
- メモリサイズの適切な設定
- X-Ray による分散トレーシング

### データベース最適化

- 適切なインデックス設計
- 読み取り専用レプリカの活用
- 接続プール設定の最適化
- Performance Insights による監視

### CDN 最適化

- CloudFront による静的コンテンツ配信
- 適切なキャッシュ設定
- 圧縮の有効化
- エッジロケーションの活用

## 運用手順

### 日常監視

1. **CloudWatch ダッシュボード確認**（毎日）

   - システム全体の健全性確認
   - パフォーマンスメトリクス確認
   - エラー率の確認

2. **アラート対応**（随時）

   - クリティカルアラートの即座対応
   - 高優先度アラートの調査
   - 根本原因分析と対策

3. **ログ分析**（週次）
   - エラーログの分析
   - パフォーマンストレンドの確認
   - セキュリティログの確認

### 定期メンテナンス

1. **月次メンテナンス**

   - セキュリティパッチの適用
   - 依存関係の更新
   - パフォーマンス最適化

2. **四半期メンテナンス**

   - 容量計画の見直し
   - コスト最適化の実施
   - 災害復旧テスト

3. **年次メンテナンス**
   - アーキテクチャレビュー
   - セキュリティ監査
   - 事業継続計画の更新

## トラブルシューティング

### 一般的な問題と解決策

1. **Lambda タイムアウト**

   - メモリサイズの増加
   - コードの最適化
   - データベースクエリの最適化

2. **データベース接続エラー**

   - 接続プール設定の確認
   - セキュリティグループの確認
   - VPC 設定の確認

3. **API Gateway エラー**
   - Lambda 関数の状態確認
   - IAM 権限の確認
   - スロットリング設定の確認

### エスカレーション手順

1. **レベル 1**: 自動復旧・基本対応
2. **レベル 2**: 開発チームによる調査
3. **レベル 3**: アーキテクトによる設計見直し
4. **レベル 4**: ベンダーサポートへの連絡

## ロールバック手順

### 緊急ロールバック

```bash
# 緊急時のロールバック実行
./deploy-enhanced.sh --rollback

# 手動でのスタック削除（必要に応じて）
aws cloudformation delete-stack --stack-name csr-lambda-api-prod-monitoring-enhanced
aws cloudformation delete-stack --stack-name csr-lambda-api-prod-frontend
aws cloudformation delete-stack --stack-name csr-lambda-api-prod-api
# ... 他のスタック
```

### 段階的ロールバック

1. 新機能の無効化
2. 前バージョンへの切り戻し
3. データベースの復旧（必要に応じて）
4. 動作確認とテスト

## コスト管理

### 予想コスト（月額）

- **Lambda**: $50-100（実行回数による）
- **Aurora**: $200-300（t3.medium + レプリカ）
- **API Gateway**: $20-50（リクエスト数による）
- **CloudFront**: $10-30（転送量による）
- **その他**: $30-50（監視、ストレージ等）

**合計**: 約 $310-530/月

### コスト最適化

1. **リソース使用量の監視**

   - AWS Cost Explorer の活用
   - 予算アラートの設定
   - 未使用リソースの特定

2. **自動スケーリングの活用**
   - Lambda Provisioned Concurrency の最適化
   - Aurora Auto Scaling の設定
   - CloudFront キャッシュの最適化

## 連絡先・サポート

### 緊急連絡先

- **システム管理者**: admin@your-domain.com
- **開発チーム**: dev-team@your-domain.com
- **インフラチーム**: infra-team@your-domain.com

### サポートリソース

- **AWS サポート**: [AWS Support Center](https://console.aws.amazon.com/support/)
- **内部ドキュメント**: [社内 Wiki/Confluence]
- **監視ダッシュボード**: [CloudWatch Dashboard URL]

## 付録

### 関連ドキュメント

- [システム設計書](./design.md)
- [要件定義書](./requirements.md)
- [セキュリティガイドライン](./security-guidelines.md)
- [運用手順書](./operations-manual.md)

### 設定ファイルテンプレート

- [parameters.json](./parameters.json)
- [.env.prod.enhanced](../../backend/.env.prod.enhanced)
- [deploy-enhanced.sh](./deploy-enhanced.sh)

---

**注意**: このドキュメントは本番環境デプロイメントの重要な手順を含んでいます。実行前に必ず内容を確認し、適切な承認を得てから実行してください。
