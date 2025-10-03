-- マイグレーションテンプレート
-- 新しいテーブルやカラムを追加する際のテンプレート

-- マイグレーション情報
-- 作成日: YYYY-MM-DD
-- 作成者: [開発者名]
-- 目的: [マイグレーションの目的]
-- 影響範囲: [影響を受けるテーブル・機能]

-- 実行前チェック
-- 1. バックアップが取得されていることを確認
-- 2. 本番環境では必ずメンテナンス時間内に実行
-- 3. ロールバック手順を準備

-- ===== マイグレーション開始 =====

-- 新しいテーブルの作成例
/*
CREATE TABLE example_table (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'ID（主キー）',
    name VARCHAR(255) NOT NULL COMMENT '名前',
    description TEXT COMMENT '説明',
    status ENUM('active', 'inactive') DEFAULT 'active' COMMENT 'ステータス（active: 有効, inactive: 無効）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'レコード作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'レコード更新日時',
    
    -- インデックス
    INDEX idx_name (name) COMMENT '名前検索用インデックス',
    INDEX idx_status (status) COMMENT 'ステータス検索用インデックス'
) COMMENT 'サンプルテーブル - 機能の説明';
*/

-- 既存テーブルへのカラム追加例
/*
ALTER TABLE users 
ADD COLUMN phone VARCHAR(20) COMMENT '電話番号' AFTER email,
ADD COLUMN is_verified BOOLEAN DEFAULT FALSE COMMENT 'メール認証済みフラグ' AFTER phone;
*/

-- インデックスの追加例
/*
ALTER TABLE users 
ADD INDEX idx_phone (phone) COMMENT '電話番号検索用インデックス';
*/

-- 外部キー制約の追加例
/*
ALTER TABLE user_profiles 
ADD CONSTRAINT fk_user_profiles_user_id 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
COMMENT 'ユーザーテーブルへの外部キー制約';
*/

-- データの更新例
/*
UPDATE users 
SET is_verified = TRUE 
WHERE email LIKE '%@example.com'
  AND created_at < '2024-01-01';
*/

-- ===== マイグレーション終了 =====

-- 実行後確認事項
-- 1. テーブル構造が正しく変更されていることを確認
-- 2. データの整合性をチェック
-- 3. アプリケーションが正常に動作することを確認
-- 4. パフォーマンスに影響がないことを確認

-- ロールバック手順（必要に応じて記述）
/*
-- テーブル削除の場合
DROP TABLE IF EXISTS example_table;

-- カラム削除の場合
ALTER TABLE users 
DROP COLUMN phone,
DROP COLUMN is_verified;

-- インデックス削除の場合
ALTER TABLE users DROP INDEX idx_phone;
*/