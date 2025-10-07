# データベースアーキテクチャ

## 🗄️ 環境別データベース構成

### ローカル開発環境

```
選択肢1: ローカルMySQL（デフォルト）
┌─────────────────────────────────┐
│  ローカル開発                    │
│  ├── Frontend (localhost:3000)  │
│  ├── Backend (localhost:8000)   │
│  └── MySQL (Docker Container)   │
│      └── localhost:3306         │
└─────────────────────────────────┘

選択肢2: Aurora MySQL（オプション）
┌─────────────────────────────────┐
│  ローカル開発                    │
│  ├── Frontend (localhost:3000)  │
│  ├── Backend (localhost:8000)   │
│  └── Aurora MySQL (AWS)         │
│      └── xxx.cluster-xxx.rds... │
└─────────────────────────────────┘
```

### AWS 環境

```
開発環境 (develop ブランチ)
┌─────────────────────────────────┐
│  AWS 開発環境                    │
│  ├── Frontend (CloudFront)      │
│  ├── Backend (Lambda)           │
│  └── Aurora MySQL               │
│      └── dev-cluster.rds...     │
└─────────────────────────────────┘

ステージング環境 (main ブランチ)
┌─────────────────────────────────┐
│  AWS ステージング環境            │
│  ├── Frontend (CloudFront)      │
│  ├── Backend (Lambda)           │
│  └── Aurora MySQL               │
│      └── staging-cluster.rds... │
└─────────────────────────────────┘

本番環境 (手動デプロイ)
┌─────────────────────────────────┐
│  AWS 本番環境                    │
│  ├── Frontend (CloudFront)      │
│  ├── Backend (Lambda)           │
│  └── Aurora MySQL               │
│      └── prod-cluster.rds...    │
└─────────────────────────────────┘
```

## 🔄 データベース切り替え

### ローカル開発での切り替え

#### 1. ローカル MySQL 使用（デフォルト）

```bash
make use-local-db
make dev-restart
```

**特徴:**

- ✅ 高速・軽量
- ✅ オフライン作業可能
- ✅ 完全に独立した環境
- ✅ 無料
- ❌ クラウド環境との差異

#### 2. Aurora MySQL 使用（オプション）

```bash
make setup-aurora      # 初回のみ
make sync-to-aurora     # データ同期
make use-aurora-db
make dev-restart
```

**特徴:**

- ✅ 本番環境と同じインフラ
- ✅ クラウドでのテスト
- ✅ チーム間でのデータ共有
- ❌ インターネット接続必要
- ❌ AWS 料金発生

## 📋 データ同期

### ローカル → Aurora

```bash
# ローカルのデータをAuroraに同期
make sync-to-aurora
```

### Aurora → ローカル

```bash
# Auroraのデータをローカルに同期（逆方向）
./scripts/sync-aurora-to-local.sh  # 今後実装予定
```

## 🎯 推奨使用パターン

### 日常開発

```bash
# 通常はローカルMySQLを使用
make use-local-db
```

### クラウドテスト

```bash
# クラウド環境でのテストが必要な場合
make use-aurora-db
```

### チーム開発

```bash
# チームでデータを共有したい場合
make sync-to-aurora
make use-aurora-db
```

## 🔧 環境変数ファイル

### ローカル MySQL 用

```bash
# backend/.env.dev
DB_HOST=mysql
DB_PORT=3306
DATABASE_URL=mysql+pymysql://dev_user:dev_password@mysql:3306/csr_lambda_dev
```

### Aurora MySQL 用

```bash
# backend/.env.dev.aurora
DB_HOST=csr-lambda-api-dev-aurora.cluster-xxx.ap-northeast-1.rds.amazonaws.com
DB_PORT=3306
DATABASE_URL=mysql+pymysql://dev_user:DevPassword123!@aurora-endpoint:3306/csr_lambda_dev
```

## 💰 コスト考慮

### ローカル MySQL

- **コスト**: 無料
- **リソース**: ローカルマシンのみ

### Aurora MySQL

- **コスト**: AWS 料金発生
  - Aurora Serverless v2: 使用量に応じた課金
  - 最小: ~$0.5/時間（アイドル時は低コスト）
- **リソース**: AWS 管理

## 🚨 注意事項

1. **データの独立性**: ローカルと Aurora は独立したデータベース
2. **同期の方向性**: 手動同期が必要
3. **セキュリティ**: Aurora は適切なセキュリティグループ設定が必要
4. **コスト管理**: Aurora 使用時は AWS 料金に注意

## 🔍 トラブルシューティング

### Aurora 接続エラー

```bash
# セキュリティグループの確認
aws ec2 describe-security-groups --group-names csr-lambda-api-dev-aurora-sg

# 接続テスト
mysql -h your-aurora-endpoint -u dev_user -p
```

### データ同期エラー

```bash
# ローカルMySQL確認
docker exec -it csr-lambda-mysql mysql -u dev_user -p

# Aurora確認
mysql -h your-aurora-endpoint -u dev_user -p
```
