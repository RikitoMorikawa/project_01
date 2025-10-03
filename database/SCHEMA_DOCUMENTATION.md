# データベーススキーマドキュメント

CSR Lambda API システムのデータベーススキーマ設計書

## 概要

このドキュメントは、CSR Lambda API システムで使用されるデータベーススキーマの詳細を説明します。
システムは AWS Aurora MySQL を使用し、AWS Cognito と連携したユーザー管理機能を提供します。

## データベース設計原則

### 命名規則

- **テーブル名**: 英語の複数形、スネークケース（例: `users`, `user_profiles`）
- **カラム名**: 英語、スネークケース（例: `user_id`, `created_at`）
- **インデックス名**: `idx_` プレフィックス + 対象カラム名（例: `idx_email`）
- **外部キー制約名**: `fk_` プレフィックス + テーブル名 + カラム名（例: `fk_user_profiles_user_id`）
- **コメント**: 日本語で記述

### データ型の選択基準

- **ID**: `BIGINT` - 将来的なスケーラビリティを考慮
- **文字列**: `VARCHAR` - 長さ制限が明確な場合、`TEXT` - 長い文章
- **日時**: `TIMESTAMP` - タイムゾーン対応
- **フラグ**: `BOOLEAN` - 真偽値
- **列挙型**: `ENUM` - 固定の選択肢

## テーブル設計

### users テーブル

ユーザーの基本情報を管理するメインテーブル。AWS Cognito と連携。

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'ユーザーID（主キー）',
    cognito_user_id VARCHAR(255) UNIQUE NOT NULL COMMENT 'AWS Cognito ユーザーID（一意）',
    email VARCHAR(255) UNIQUE NOT NULL COMMENT 'メールアドレス（一意、ログイン用）',
    username VARCHAR(100) NOT NULL COMMENT 'ユーザー名（表示用）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'レコード作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'レコード更新日時',

    INDEX idx_cognito_user_id (cognito_user_id) COMMENT 'Cognito ユーザーID検索用インデックス',
    INDEX idx_email (email) COMMENT 'メールアドレス検索用インデックス'
) COMMENT 'ユーザー基本情報テーブル - AWS Cognito と連携したユーザー管理';
```

#### カラム詳細

| カラム名        | データ型     | 制約                                                  | 説明                                |
| --------------- | ------------ | ----------------------------------------------------- | ----------------------------------- |
| id              | BIGINT       | PRIMARY KEY, AUTO_INCREMENT                           | システム内部で使用するユーザー ID   |
| cognito_user_id | VARCHAR(255) | UNIQUE, NOT NULL                                      | AWS Cognito で管理されるユーザー ID |
| email           | VARCHAR(255) | UNIQUE, NOT NULL                                      | ログインに使用するメールアドレス    |
| username        | VARCHAR(100) | NOT NULL                                              | 画面表示用のユーザー名              |
| created_at      | TIMESTAMP    | DEFAULT CURRENT_TIMESTAMP                             | レコード作成日時                    |
| updated_at      | TIMESTAMP    | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | レコード更新日時                    |

#### インデックス

| インデックス名      | 対象カラム      | 目的                               |
| ------------------- | --------------- | ---------------------------------- |
| idx_cognito_user_id | cognito_user_id | Cognito ユーザー ID による高速検索 |
| idx_email           | email           | メールアドレスによる高速検索       |

### user_profiles テーブル

ユーザーの詳細プロファイル情報を管理。

```sql
CREATE TABLE user_profiles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'プロファイルID（主キー）',
    user_id BIGINT NOT NULL COMMENT 'ユーザーID（外部キー）',
    first_name VARCHAR(100) COMMENT '名前',
    last_name VARCHAR(100) COMMENT '姓',
    avatar_url VARCHAR(500) COMMENT 'アバター画像のURL',
    bio TEXT COMMENT '自己紹介文',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'レコード作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'レコード更新日時',

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE COMMENT 'ユーザーテーブルへの外部キー（カスケード削除）'
) COMMENT 'ユーザープロファイル情報テーブル - ユーザーの詳細情報を管理';
```

#### カラム詳細

| カラム名   | データ型     | 制約                                                  | 説明                   |
| ---------- | ------------ | ----------------------------------------------------- | ---------------------- |
| id         | BIGINT       | PRIMARY KEY, AUTO_INCREMENT                           | プロファイル ID        |
| user_id    | BIGINT       | NOT NULL, FOREIGN KEY                                 | 関連するユーザーの ID  |
| first_name | VARCHAR(100) | NULL                                                  | ユーザーの名前         |
| last_name  | VARCHAR(100) | NULL                                                  | ユーザーの姓           |
| avatar_url | VARCHAR(500) | NULL                                                  | プロフィール画像の URL |
| bio        | TEXT         | NULL                                                  | 自己紹介文             |
| created_at | TIMESTAMP    | DEFAULT CURRENT_TIMESTAMP                             | レコード作成日時       |
| updated_at | TIMESTAMP    | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | レコード更新日時       |

#### 外部キー制約

| 制約名                   | 参照元                | 参照先   | 削除時動作 |
| ------------------------ | --------------------- | -------- | ---------- |
| fk_user_profiles_user_id | user_profiles.user_id | users.id | CASCADE    |

## リレーションシップ

```
users (1) ←→ (0..1) user_profiles
```

- 1 人のユーザーは 0 個または 1 個のプロファイルを持つ
- プロファイルは必ず 1 人のユーザーに属する
- ユーザーが削除されると、関連するプロファイルも自動削除される

## インデックス戦略

### 検索パフォーマンス最適化

1. **主キー検索**: 自動的に最適化される
2. **Cognito ID 検索**: 認証時の高速検索のため
3. **メール検索**: ログイン時の高速検索のため

### 将来的な拡張を考慮したインデックス

- ユーザー名検索用インデックス（必要に応じて追加）
- 作成日時範囲検索用インデックス（レポート機能で使用）

## セキュリティ考慮事項

### データ保護

1. **個人情報の暗号化**: 必要に応じてアプリケーションレベルで実装
2. **アクセス制御**: データベースユーザーの権限を最小限に制限
3. **監査ログ**: 重要な操作のログ記録

### バックアップ戦略

1. **自動バックアップ**: Aurora の自動バックアップ機能を使用
2. **ポイントインタイム復旧**: 35 日間の復旧ポイント保持
3. **クロスリージョンバックアップ**: 災害復旧のため

## パフォーマンス最適化

### クエリ最適化

1. **適切なインデックス使用**: EXPLAIN を使用してクエリプランを確認
2. **N+1 問題の回避**: JOIN を使用した効率的なデータ取得
3. **ページネーション**: 大量データの効率的な取得

### 接続プール管理

1. **接続数制限**: Lambda の同時実行数に応じた調整
2. **接続タイムアウト**: 適切なタイムアウト値の設定
3. **接続再利用**: 接続プールによる効率的な接続管理

## マイグレーション管理

### マイグレーション実行手順

1. **バックアップ取得**: 実行前に必ずバックアップを取得
2. **テスト環境での検証**: 本番環境実行前にテスト環境で検証
3. **ロールバック準備**: 問題発生時のロールバック手順を準備
4. **メンテナンス時間**: 本番環境では必ずメンテナンス時間内に実行

### マイグレーションファイル命名規則

```
YYYYMMDD_HHMMSS_migration_description.sql
```

例: `20240101_120000_add_user_phone_column.sql`

## 監視とメンテナンス

### 定期監視項目

1. **テーブルサイズ**: ディスク使用量の監視
2. **インデックス効率**: 使用されていないインデックスの確認
3. **スロークエリ**: パフォーマンス問題の早期発見
4. **接続数**: 接続プールの使用状況監視

### 定期メンテナンス

1. **統計情報更新**: クエリオプティマイザーの最適化
2. **不要データ削除**: 古いログデータの削除
3. **インデックス再構築**: 必要に応じてインデックスの最適化

## 環境別設定

### 開発環境 (dev)

- **インスタンスタイプ**: db.t3.small
- **ストレージ**: 20GB
- **バックアップ保持期間**: 7 日
- **マルチ AZ**: 無効

### ステージング環境 (staging)

- **インスタンスタイプ**: db.t3.small
- **ストレージ**: 100GB
- **バックアップ保持期間**: 14 日
- **マルチ AZ**: 有効

### 本番環境 (prod)

- **インスタンスタイプ**: db.t3.medium
- **ストレージ**: 500GB（自動スケーリング有効）
- **バックアップ保持期間**: 35 日
- **マルチ AZ**: 有効
- **リードレプリカ**: 1 台（読み取り負荷分散用）

## トラブルシューティング

### よくある問題と対処法

1. **接続エラー**

   - 接続プールの設定確認
   - セキュリティグループの設定確認
   - VPC 設定の確認

2. **パフォーマンス問題**

   - スロークエリログの確認
   - インデックス使用状況の確認
   - 統計情報の更新

3. **データ整合性エラー**
   - 外部キー制約の確認
   - トランザクション処理の見直し
   - データ修復手順の実行

### 緊急時対応

1. **データベース障害**

   - Aurora の自動フェイルオーバー
   - ポイントインタイム復旧
   - バックアップからの復元

2. **データ破損**
   - バックアップからの復元
   - レプリカからのデータ復旧
   - 部分的データ修復

## 参考資料

- [AWS Aurora MySQL ドキュメント](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/)
- [MySQL 8.0 リファレンスマニュアル](https://dev.mysql.com/doc/refman/8.0/ja/)
- [データベース設計ベストプラクティス](https://example.com/db-best-practices)
