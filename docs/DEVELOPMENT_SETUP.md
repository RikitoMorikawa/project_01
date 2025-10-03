# 開発環境セットアップガイド

このガイドでは、CSR Lambda API の開発環境を簡単に起動・管理する方法を説明します。

## 🚀 クイックスタート

### 1. 開発環境の起動

```bash
# 方法1: 便利なスクリプトを使用（推奨）
./scripts/dev-setup.sh start

# 方法2: Makeコマンドを使用
make dev-start

# 方法3: 直接Docker Composeを使用
docker-compose up --build -d
```

### 2. サービスへのアクセス

起動後、以下の URL でサービスにアクセスできます：

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **MySQL**: localhost:3306

## 📋 利用可能なコマンド

### 開発環境管理スクリプト

```bash
# 開発環境を起動
./scripts/dev-setup.sh start

# 開発環境を停止
./scripts/dev-setup.sh stop

# 開発環境を再起動
./scripts/dev-setup.sh restart

# コンテナの状態を確認
./scripts/dev-setup.sh status

# ログを表示（全サービス）
./scripts/dev-setup.sh logs

# 特定のサービスのログを表示
./scripts/dev-setup.sh logs backend
./scripts/dev-setup.sh logs frontend
./scripts/dev-setup.sh logs mysql

# 完全なクリーンアップ
./scripts/dev-setup.sh cleanup

# ヘルプを表示
./scripts/dev-setup.sh help
```

### Make コマンド

```bash
# 開発環境管理
make dev-start          # 開発環境を起動
make dev-stop           # 開発環境を停止
make dev-restart        # 開発環境を再起動
make dev-status         # 詳細な状態を表示
make dev-cleanup        # 完全なクリーンアップ

# ログ表示
make dev-logs           # 全サービスのログ
make dev-logs-backend   # バックエンドのログ
make dev-logs-frontend  # フロントエンドのログ
make dev-logs-mysql     # MySQLのログ

# コンテナシェル
make dev-shell-backend  # バックエンドコンテナのシェル
make dev-shell-mysql    # MySQLシェル

# 従来のコマンド
make start              # サービス起動
make stop               # サービス停止
make status             # 状態確認
make logs               # ログ表示
```

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. コンテナが起動しない

```bash
# Docker Desktopが起動しているか確認
docker info

# 既存のコンテナをクリーンアップ
./scripts/dev-setup.sh cleanup

# 再度起動を試す
./scripts/dev-setup.sh start
```

#### 2. ポートが既に使用されている

```bash
# ポート使用状況を確認
lsof -i :8000  # バックエンド
lsof -i :3000  # フロントエンド
lsof -i :3306  # MySQL

# 使用中のプロセスを停止してから再起動
./scripts/dev-setup.sh restart
```

#### 3. データベース接続エラー

```bash
# MySQLコンテナの状態を確認
docker-compose ps mysql

# MySQLのログを確認
./scripts/dev-setup.sh logs mysql

# データベースに直接接続してテスト
make dev-shell-mysql
```

#### 4. バックエンド API が応答しない

```bash
# バックエンドのログを確認
./scripts/dev-setup.sh logs backend

# コンテナ内でシェルを開いて調査
make dev-shell-backend

# 環境変数を確認
docker exec csr-lambda-backend env | grep -E "(DB_|DATABASE_)"
```

## 🛠️ 開発ワークフロー

### 日常的な開発作業

1. **朝の作業開始時**:

   ```bash
   ./scripts/dev-setup.sh start
   ```

2. **コードの変更**:

   - バックエンド: `backend/` フォルダ内のファイルを編集
   - フロントエンド: `frontend/` フォルダ内のファイルを編集
   - 変更は自動的にリロードされます

3. **ログの確認**:

   ```bash
   ./scripts/dev-setup.sh logs backend  # バックエンドのログ
   ./scripts/dev-setup.sh logs frontend # フロントエンドのログ
   ```

4. **作業終了時**:
   ```bash
   ./scripts/dev-setup.sh stop
   ```

### データベース操作

```bash
# MySQLシェルに接続
make dev-shell-mysql

# データベースの状態を確認
SHOW DATABASES;
USE csr_lambda_dev;
SHOW TABLES;
```

## 📁 設定ファイル

### 重要な設定ファイル

- `docker-compose.yml`: Docker Compose 設定
- `backend/.env.dev`: バックエンド開発環境変数
- `backend/Dockerfile.dev`: バックエンド Dockerfile
- `frontend/Dockerfile.dev`: フロントエンド Dockerfile

### 環境変数の変更

バックエンドの環境変数を変更する場合：

1. `backend/.env.dev` を編集
2. コンテナを再起動: `./scripts/dev-setup.sh restart`

## 🚨 注意事項

- **Docker Desktop**: 必ず Docker Desktop が起動していることを確認してください
- **ポート競合**: 8000, 3000, 3306 ポートが他のアプリケーションで使用されていないことを確認してください
- **リソース**: 初回起動時はイメージのビルドに時間がかかります
- **データ永続化**: MySQL のデータは `mysql_data` ボリュームに保存されます

## 📞 サポート

問題が発生した場合：

1. まず `./scripts/dev-setup.sh status` で状態を確認
2. ログを確認: `./scripts/dev-setup.sh logs`
3. クリーンアップを試す: `./scripts/dev-setup.sh cleanup`
4. それでも解決しない場合は、開発チームに相談してください

---

Happy Coding! 🎉
