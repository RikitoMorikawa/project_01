# CSR Lambda API System

サーバーレス Lambda API バックエンドを持つクライアントサイドレンダリング（CSR）Web アプリケーション

## アーキテクチャ

- **フロントエンド**: Next.js (CSR モード) + TypeScript
- **バックエンド**: FastAPI + Python + AWS Lambda
- **データベース**: Aurora MySQL
- **インフラ**: AWS (CloudFront, S3, API Gateway, Lambda, Aurora)

## プロジェクト構成

```
project_01/
├── frontend/                    # Next.js CSR アプリケーション
├── backend/                     # FastAPI アプリケーション
├── infrastructure/              # AWS CloudFormation テンプレート
├── database/                    # データベース初期化スクリプト
├── .github/workflows/           # GitHub Actions CI/CD
└── docker-compose.yml           # ローカル開発環境
```

## 開発環境セットアップ

### 前提条件

- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- AWS CLI (デプロイ用)

### ローカル開発環境の起動

```bash
# 全サービスを起動
docker-compose up -d

# ログを確認
docker-compose logs -f

# サービス停止
docker-compose down
```

### 個別開発

#### フロントエンド

```bash
cd frontend
npm install
npm run dev
```

アクセス: http://localhost:3000

#### バックエンド

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

アクセス: http://localhost:8000
API ドキュメント: http://localhost:8000/docs

## 環境設定

### 開発環境 (dev)

- ローカル MySQL (Docker)
- Lambda シミュレーション (uvicorn)
- CloudFront 無効

### ステージング環境 (staging)

- Aurora MySQL t3.small
- Lambda 512MB
- CloudFront 有効

### 本番環境 (prod)

- Aurora MySQL t3.medium + Read Replica
- Lambda 1024MB + Provisioned Concurrency
- CloudFront + WAF

## デプロイメント

### 自動デプロイ

- `develop` ブランチ → 開発環境
- `main` ブランチ → ステージング環境
- 手動トリガー → 本番環境

### 手動デプロイ

```bash
# インフラストラクチャのデプロイ
aws cloudformation deploy --template-file infrastructure/dev/template.yml --stack-name csr-lambda-dev

# アプリケーションのデプロイ
# (後のタスクで実装)
```

## 監視・ログ

- CloudWatch Logs
- CloudWatch Metrics
- X-Ray トレーシング (本番環境)

## セキュリティ

- AWS Cognito 認証
- VPC プライベートサブネット
- HTTPS 暗号化
- WAF (本番環境)

## 開発ガイドライン

### コーディング規約

- TypeScript: ESLint + Prettier
- Python: Black + isort + flake8

### テスト

- フロントエンド: Jest + React Testing Library
- バックエンド: pytest + FastAPI TestClient

## トラブルシューティング

### よくある問題

1. **MySQL 接続エラー**

   ```bash
   docker-compose down
   docker-compose up -d mysql
   # MySQL の起動を待ってから他のサービスを起動
   ```

2. **ポート競合**

   - 3000, 3306, 8000 ポートが使用されていないか確認

3. **環境変数**
   - 各環境の `.env.*` ファイルを確認

## ライセンス

MIT License
