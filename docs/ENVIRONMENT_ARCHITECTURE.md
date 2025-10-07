# 環境別アーキテクチャ

## 🏗️ システム構成

### ローカル開発環境

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │   MySQL         │
│   (Next.js)     │◄──►│   (FastAPI)      │◄──►│   (Docker)      │
│   localhost:3000│    │   localhost:8000 │    │   localhost:3306│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         └────────────────────────┼─────────────────────────────────┐
                                  │                                 │
                            ┌─────▼──────────────────────────────────▼─┐
                            │        AWS Cognito (共通)              │
                            │   ap-northeast-1_HluYCXwCo            │
                            └────────────────────────────────────────┘
```

### 開発環境 (AWS)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │   Aurora MySQL  │
│   (CloudFront)  │◄──►│   (Lambda)       │◄──►│   (AWS RDS)     │
│   + S3          │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         └────────────────────────┼─────────────────────────────────┐
                                  │                                 │
                            ┌─────▼──────────────────────────────────▼─┐
                            │        AWS Cognito (共通)              │
                            │   ap-northeast-1_HluYCXwCo            │
                            └────────────────────────────────────────┘
```

### 本番環境 (AWS)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │   Aurora MySQL  │
│   (CloudFront)  │◄──►│   (Lambda)       │◄──►│   (AWS RDS)     │
│   + S3          │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         └────────────────────────┼─────────────────────────────────┐
                                  │                                 │
                            ┌─────▼──────────────────────────────────▼─┐
                            │        AWS Cognito (本番用)            │
                            │   ap-northeast-1_xxxxxxxxx            │
                            └────────────────────────────────────────┘
```

## 🔧 環境変数設定

### ローカル開発

```bash
# Cognito (開発環境と共通)
COGNITO_USER_POOL_ID=ap-northeast-1_HluYCXwCo
COGNITO_CLIENT_ID=71mnemjh6en2qpd5cmv21qp30u

# Database (Docker MySQL)
DB_HOST=mysql
DB_PORT=3306
DATABASE_URL=mysql+pymysql://dev_user:dev_password@mysql:3306/csr_lambda_dev
```

### 開発環境 (AWS)

```bash
# Cognito (ローカルと共通)
COGNITO_USER_POOL_ID=ap-northeast-1_HluYCXwCo
COGNITO_CLIENT_ID=71mnemjh6en2qpd5cmv21qp30u

# Database (Aurora MySQL)
DB_HOST=csr-lambda-dev-aurora.cluster-xxxxx.ap-northeast-1.rds.amazonaws.com
DB_PORT=3306
DATABASE_URL=mysql+pymysql://username:password@aurora-endpoint/csr_lambda_dev
```

### 本番環境 (AWS)

```bash
# Cognito (本番専用)
COGNITO_USER_POOL_ID=ap-northeast-1_xxxxxxxxx
COGNITO_CLIENT_ID=yyyyyyyyyyyyyyyy

# Database (Aurora MySQL)
DB_HOST=csr-lambda-prod-aurora.cluster-xxxxx.ap-northeast-1.rds.amazonaws.com
DB_PORT=3306
DATABASE_URL=mysql+pymysql://username:password@aurora-endpoint/csr_lambda_prod
```

## 🎯 メリット

### Cognito 共通使用のメリット

- **開発効率**: ローカルと開発環境で同じユーザーでテスト可能
- **コスト削減**: 開発用 Cognito リソースの節約
- **一貫性**: 認証フローの統一

### データベース分離のメリット

- **データ安全性**: ローカル開発でのデータ破損リスクなし
- **パフォーマンス**: 本番データに影響なし
- **独立性**: 各環境での独立したテスト

### サーバーレス構成のメリット

- **コスト効率**: 使用量に応じた課金
- **スケーラビリティ**: 自動スケーリング
- **運用負荷軽減**: インフラ管理不要
- **高可用性**: AWS マネージドサービスの恩恵

## 🌿 ブランチ戦略とデプロイフロー

### Git ブランチ構成

```
main (ステージング・本番環境)
├── develop (開発環境)
│   ├── feature/xxx (機能開発)
│   └── hotfix/xxx (緊急修正)
└── release/xxx (リリース準備)
```

### 環境とブランチの対応

- **ローカル開発**: 任意のブランチ
- **開発環境 (dev)**: `develop` ブランチ → 自動デプロイ
- **ステージング環境 (staging)**: `main` ブランチ → 自動デプロイ
- **本番環境 (prod)**: `main` ブランチ → 手動トリガー（workflow_dispatch）

### CI/CD パイプライン

#### 開発環境 (develop ブランチ)

```
develop push → GitHub Actions → Build → Deploy to dev
├── Frontend: S3 + CloudFront
├── Backend: Lambda + API Gateway
└── Database: Aurora MySQL (dev)
```

#### ステージング環境 (main ブランチ)

```
main push → GitHub Actions → Build → Deploy to staging
├── Frontend: S3 + CloudFront
├── Backend: Lambda + API Gateway
└── Database: Aurora MySQL (staging)
```

#### 本番環境 (手動トリガー)

```
Manual Trigger → GitHub Actions → Build → Deploy to prod
├── Frontend: S3 + CloudFront
├── Backend: Lambda + API Gateway
└── Database: Aurora MySQL (prod)
```

## 🚀 デプロイフロー詳細

### フロントエンド

1. **ローカル開発** → Next.js 開発サーバー
2. **開発環境** → `develop` → GitHub Actions → S3 → CloudFront
3. **本番環境** → `main` → GitHub Actions → 手動承認 → S3 → CloudFront

### バックエンド

1. **ローカル開発** → FastAPI 開発サーバー
2. **開発環境** → `develop` → GitHub Actions → Lambda → API Gateway
3. **本番環境** → `main` → GitHub Actions → 手動承認 → Lambda → API Gateway

### データベース

1. **ローカル開発** → Docker MySQL
2. **開発環境** → Aurora MySQL (dev cluster)
3. **本番環境** → Aurora MySQL (prod cluster)

## 📝 注意点

- **Cognito ユーザー**: 開発環境とローカルで共通のため、テストユーザーの管理に注意
- **データベース**: 環境ごとに完全分離されているため、データ移行時は注意が必要
- **環境変数**: 各環境で適切な設定が必要
