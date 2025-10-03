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
- GitHub Personal Access Token (CI/CD 用)

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

### GitHub Personal Access Token の設定

CI/CD パイプラインを使用する前に、GitHub Personal Access Token を設定する必要があります。

#### 1. GitHub トークンの作成

1. GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token (classic)" をクリック
3. 以下の権限を選択：
   - `repo` (Full control of private repositories)
   - `admin:repo_hook` (Full control of repository hooks)
4. トークンをコピーして保存

#### 2. AWS Parameter Store への保存

```bash
# 自動設定スクリプトを使用（推奨）
./scripts/setup-github-token.sh --token YOUR_GITHUB_TOKEN --env dev

# または手動で設定
aws ssm put-parameter \
    --name "/codepipeline/dev/github/token" \
    --value "YOUR_GITHUB_TOKEN" \
    --type "SecureString" \
    --region ap-northeast-1
```

#### 3. トークンの検証

```bash
# トークンの有効性を確認
./scripts/verify-github-token.sh --env dev
```

#### 4. GitHub 統合の一括デプロイ

```bash
# トークン設定からパイプライン作成まで一括実行
./scripts/deploy-github-integration.sh --env dev --token YOUR_GITHUB_TOKEN

# トークンが既に設定済みの場合
./scripts/deploy-github-integration.sh --env dev --skip-token
```

詳細な手順は [GitHub Token Setup Guide](docs/github-token-setup.md) を参照してください。

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

#### 包括的テストの実行

最終統合テストと検証を実行するには、以下のスクリプトを使用してください：

```bash
# 基本的な実行
./scripts/run_final_verification.sh

# 本番環境URLを指定して実行
./scripts/run_final_verification.sh --url https://your-api-domain.com

# 軽量負荷テストで実行
./scripts/run_final_verification.sh --light-load

# 設定ファイルを指定して実行
./scripts/run_final_verification.sh --config prod_test_config.json
```

#### 個別テストの実行

**バックエンドテスト:**

```bash
cd backend

# 単体テスト
python -m pytest tests/unit/ -v

# 統合テスト
python -m pytest tests/integration/ -v

# 本番環境ヘルスチェック
python tests/production/test_production_health.py

# パフォーマンステスト
python tests/performance/load_test.py

# セキュリティスキャン
python tests/security/security_scanner.py
```

**フロントエンドテスト:**

```bash
cd frontend

# 単体テスト
npm test

# E2E テスト
npx playwright test

# カバレッジ付きテスト
npm test -- --coverage
```

#### テスト設定

テスト設定は `test_config.json` ファイルで管理されています。環境変数での設定上書きも可能です：

- `PRODUCTION_API_URL`: 本番環境の API URL
- `PRODUCTION_API_KEY`: API 認証キー
- `LOAD_TEST_USERS`: 負荷テストの同時ユーザー数
- `LOAD_TEST_REQUESTS_PER_USER`: ユーザーあたりのリクエスト数

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
