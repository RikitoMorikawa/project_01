# CSR Lambda API システム - 監視設定ガイド

## 概要

このドキュメントでは、CSR Lambda API システムの監視とログ設定について説明します。システムは CloudWatch を使用して包括的な監視を提供し、アラート、ダッシュボード、カスタムメトリクスを含みます。

## 監視アーキテクチャ

### 監視対象コンポーネント

1. **Lambda 関数**

   - 実行時間、エラー率、スロットリング
   - 同時実行数、Provisioned Concurrency 使用率
   - メモリ使用量、コールドスタート

2. **API Gateway**

   - リクエスト数、エラー率（4xx/5xx）
   - レスポンス時間、統合レイテンシ
   - スロットリング

3. **Aurora MySQL データベース**

   - CPU 使用率、メモリ使用量
   - 接続数、読み取り/書き込みレイテンシ
   - スループット、デッドロック

4. **CloudFront CDN**

   - リクエスト数、エラー率
   - キャッシュヒット率、オリジンレイテンシ
   - データ転送量

5. **カスタムアプリケーションメトリクス**
   - ユーザー登録・ログイン数
   - API エンドポイント使用状況
   - 認証エラー、バリデーションエラー
   - ビジネス KPI

## デプロイ手順

### 1. 前提条件

- AWS CLI がインストール・設定済み
- 適切な IAM 権限（CloudFormation、CloudWatch、SNS）
- jq コマンドがインストール済み（JSON 処理用）

### 2. 監視インフラストラクチャのデプロイ

```bash
# 開発環境
./infrastructure/scripts/deploy-monitoring.sh dev

# ステージング環境（メール通知付き）
./infrastructure/scripts/deploy-monitoring.sh staging \
  --notification-email admin@example.com

# 本番環境（フル監視）
./infrastructure/scripts/deploy-monitoring.sh prod \
  --notification-email admin@example.com \
  --slack-webhook-url https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

### 3. 手動設定が必要な項目

#### メール通知の購読確認

1. SNS からの確認メールを確認
2. 購読確認リンクをクリック
3. CloudWatch コンソールでテスト通知を送信

#### Slack 通知の設定

1. Slack ワークスペースで Incoming Webhook を作成
2. Webhook URL をデプロイスクリプトに指定
3. テスト通知で動作確認

## 監視ダッシュボード

### 開発環境

- **システム概要ダッシュボード**: 基本的なシステムメトリクス
- **アプリケーションメトリクス**: ビジネス関連メトリクス

### ステージング環境

- **システム概要ダッシュボード**: 本番類似の監視
- **パフォーマンステスト**: 負荷テスト用メトリクス

### 本番環境

- **システム概要ダッシュボード**: 24/7 監視用
- **ビジネスメトリクス**: KPI とユーザー行動分析
- **セキュリティ監視**: 認証・認可関連イベント

## アラート設定

### 開発環境のアラート閾値

| メトリクス             | 閾値  | 評価期間 |
| ---------------------- | ----- | -------- |
| Lambda エラー          | 5 回  | 5 分間   |
| API Gateway 4xx エラー | 10 回 | 5 分間   |
| API Gateway 5xx エラー | 1 回  | 5 分間   |
| データベース CPU       | 80%   | 5 分間   |
| レスポンス時間         | 5 秒  | 5 分間   |

### ステージング環境のアラート閾値

| メトリクス             | 閾値 | 評価期間 |
| ---------------------- | ---- | -------- |
| Lambda エラー          | 3 回 | 5 分間   |
| API Gateway 4xx エラー | 5 回 | 5 分間   |
| API Gateway 5xx エラー | 1 回 | 5 分間   |
| データベース CPU       | 70%  | 5 分間   |
| レスポンス時間         | 3 秒 | 5 分間   |

### 本番環境のアラート閾値

| メトリクス             | 閾値   | 評価期間 | 重要度   |
| ---------------------- | ------ | -------- | -------- |
| Lambda エラー          | 1 回   | 5 分間   | CRITICAL |
| Lambda スロットリング  | 1 回   | 5 分間   | CRITICAL |
| API Gateway 5xx エラー | 1 回   | 5 分間   | CRITICAL |
| API Gateway 4xx エラー | 10 回  | 5 分間   | WARNING  |
| データベース CPU       | 80%    | 5 分間   | CRITICAL |
| データベース接続数     | 150 個 | 5 分間   | CRITICAL |
| レスポンス時間         | 2 秒   | 5 分間   | WARNING  |
| CloudFront エラー率    | 1%     | 5 分間   | CRITICAL |

## カスタムメトリクス

### ビジネスメトリクス

```python
from app.utils.metrics import BusinessMetrics

# ユーザー登録の追跡
BusinessMetrics.track_user_registration()

# ログイン成功の追跡
BusinessMetrics.track_user_login()

# 認証失敗の追跡
BusinessMetrics.track_authentication_failure("invalid_password")
```

### API メトリクス

```python
from app.utils.metrics import track_api_call

@track_api_call("users_create")
async def create_user():
    # API 実装
    pass
```

### データベースメトリクス

```python
from app.utils.metrics import track_database_operation

@track_database_operation("user_query")
async def get_user():
    # データベース操作
    pass
```

## ログ設定

### ログレベル

- **開発環境**: DEBUG
- **ステージング環境**: INFO
- **本番環境**: WARNING

### ログ保持期間

- **開発環境**: 14 日
- **ステージング環境**: 30 日
- **本番環境**: 90 日

### 構造化ログ

```python
import logging

logger = logging.getLogger(__name__)

# 構造化ログの例
logger.info(
    "ユーザーログイン成功",
    extra={
        "user_id": user.id,
        "email": user.email,
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent")
    }
)
```

## 通知設定

### 通知チャネル

1. **メール通知**

   - 全てのアラートレベル
   - 管理者・開発チーム向け

2. **Slack 通知**

   - CRITICAL・HIGH レベルのアラート
   - リアルタイム通知

3. **PagerDuty**（本番環境のみ）
   - CRITICAL レベルのアラート
   - 24/7 オンコール対応

### 通知内容

- アラート名と重要度
- 発生時刻と環境
- 詳細なエラー情報
- 対応手順へのリンク

## 運用手順

### 日常監視

1. **毎日の確認事項**

   - システム概要ダッシュボードの確認
   - エラーログの確認
   - パフォーマンスメトリクスの確認

2. **週次の確認事項**
   - ビジネスメトリクスの分析
   - 容量計画の見直し
   - アラート閾値の調整

### インシデント対応

1. **アラート受信時**

   - アラート内容の確認
   - 影響範囲の特定
   - 初期対応の実施

2. **エスカレーション**
   - CRITICAL アラート: 即座にオンコール担当者に連絡
   - HIGH アラート: 1 時間以内に対応開始
   - MEDIUM アラート: 営業時間内に対応

### パフォーマンス最適化

1. **定期的な見直し**

   - レスポンス時間の分析
   - リソース使用率の確認
   - ボトルネック の特定

2. **スケーリング判断**
   - Lambda 同時実行数の調整
   - データベースインスタンスサイズの変更
   - Provisioned Concurrency の設定

## トラブルシューティング

### よくある問題と対処法

#### Lambda 関数のタイムアウト

```bash
# CloudWatch Logs でタイムアウトログを確認
aws logs filter-log-events \
  --log-group-name "/aws/lambda/csr-lambda-api-prod-api" \
  --filter-pattern "Task timed out"
```

#### データベース接続エラー

```bash
# RDS のメトリクスを確認
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBClusterIdentifier,Value=csr-lambda-api-prod-aurora-cluster \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 300 \
  --statistics Average
```

#### API Gateway エラー

```bash
# API Gateway のログを確認
aws logs filter-log-events \
  --log-group-name "API-Gateway-Execution-Logs_<api-id>/v1" \
  --filter-pattern "ERROR"
```

### メトリクス取得コマンド

```bash
# カスタムメトリクスの確認
aws cloudwatch get-metric-statistics \
  --namespace CSR-Lambda-API \
  --metric-name user_logins \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 3600 \
  --statistics Sum

# アラーム状態の確認
aws cloudwatch describe-alarms \
  --alarm-names "csr-lambda-api-prod-lambda-error-rate"
```

## セキュリティ監視

### 監視対象イベント

1. **認証関連**

   - ログイン失敗の急増
   - 異常なアクセスパターン
   - 権限昇格の試行

2. **API アクセス**

   - 異常な API 呼び出し頻度
   - 不正なエンドポイントアクセス
   - 大量データアクセス

3. **システム**
   - 設定変更
   - 権限変更
   - インフラストラクチャ変更

### セキュリティアラート

```python
from app.utils.notifications import send_security_notification

# 疑わしいログイン試行
send_security_notification(
    "suspicious_login_attempts",
    "短時間で複数回のログイン失敗が検出されました",
    {"user_email": "user@example.com", "attempt_count": 5}
)
```

## 費用最適化

### 監視コストの管理

1. **ログ保持期間の最適化**

   - 開発環境: 短期間（14 日）
   - 本番環境: 法的要件に応じて設定

2. **メトリクス頻度の調整**

   - 重要でないメトリクス: 5 分間隔
   - 重要なメトリクス: 1 分間隔

3. **ダッシュボードの効率化**
   - 必要最小限のウィジェット
   - 適切な時間範囲の設定

### 月額費用見積もり

| 環境         | CloudWatch Logs | CloudWatch Metrics | SNS | 合計 |
| ------------ | --------------- | ------------------ | --- | ---- |
| 開発         | $5              | $10                | $1  | $16  |
| ステージング | $15             | $25                | $2  | $42  |
| 本番         | $50             | $75                | $5  | $130 |

## 参考資料

- [AWS CloudWatch ユーザーガイド](https://docs.aws.amazon.com/cloudwatch/)
- [Lambda 監視ベストプラクティス](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-functions.html)
- [API Gateway 監視](https://docs.aws.amazon.com/apigateway/latest/developerguide/monitoring_overview.html)
- [RDS 監視](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/monitoring-overview.html)
