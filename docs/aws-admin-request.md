# AWS 管理者への依頼事項

## 概要

CSR Lambda API システムの CI/CD パイプライン用に AWS リソースへのアクセス権限が必要です。

## 依頼内容

### 1. IAM ユーザーの作成（推奨）

新しい CI/CD 専用ユーザーを作成してください：

```bash
# ユーザー作成
aws iam create-user --user-name github-actions-cicd-csr-lambda-api

# アクセスキー作成
aws iam create-access-key --user-name github-actions-cicd-csr-lambda-api
```

### 2. 必要な権限ポリシーのアタッチ

以下のポリシーをユーザーにアタッチしてください：

#### カスタムポリシーの作成

```bash
# ポリシー作成
aws iam create-policy \
  --policy-name CSR-Lambda-API-CICD-Policy \
  --policy-document file://docs/aws-iam-policy.json

# ポリシーをユーザーにアタッチ
aws iam attach-user-policy \
  --user-name github-actions-cicd-csr-lambda-api \
  --policy-arn arn:aws:iam::040433403151:policy/CSR-Lambda-API-CICD-Policy
```

#### または既存の管理ポリシーを使用（開発環境の場合）

```bash
# PowerUserAccess（本番環境では推奨しません）
aws iam attach-user-policy \
  --user-name github-actions-cicd-csr-lambda-api \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

# IAMReadOnlyAccess（IAM リソースの読み取り用）
aws iam attach-user-policy \
  --user-name github-actions-cicd-csr-lambda-api \
  --policy-arn arn:aws:iam::aws:policy/IAMReadOnlyAccess
```

### 3. 代替案：既存ユーザーの権限拡張

新しいユーザーを作成できない場合は、既存ユーザー `prod-ippon-service-user` に必要な権限を追加してください：

```bash
# 必要な権限ポリシーをアタッチ
aws iam attach-user-policy \
  --user-name prod-ippon-service-user \
  --policy-arn arn:aws:iam::040433403151:policy/CSR-Lambda-API-CICD-Policy
```

## セキュリティ考慮事項

### 最小権限の原則

- 本番環境では必要最小限の権限のみを付与
- 開発・ステージング環境でのみ広範囲な権限を使用

### アクセスキーの管理

- アクセスキーは GitHub Secrets で安全に管理
- 定期的なローテーション（90 日ごと推奨）
- 不要になったキーは即座に削除

### 監査とモニタリング

- CloudTrail でのアクション監視
- 異常なアクセスパターンの検出

## 作成後の確認事項

作成完了後、以下の情報を開発チームに共有してください：

```
AWS_ACCESS_KEY_ID: AKIA...
AWS_SECRET_ACCESS_KEY: ...
IAM User ARN: arn:aws:iam::040433403151:user/github-actions-cicd-csr-lambda-api
```

## テスト手順

権限設定後、以下のコマンドでテストしてください：

```bash
# 認証テスト
aws sts get-caller-identity

# 基本権限テスト
aws s3 ls
aws lambda list-functions --max-items 1
aws cloudformation list-stacks --max-items 1
```
