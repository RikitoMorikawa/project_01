-- 開発環境用データベーススキーマの初期化
-- CSR Lambda API システム用のテーブル定義
USE csr_lambda_dev;

-- ユーザー情報テーブル
-- AWS Cognito と連携したユーザーの基本情報を管理
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'ユーザーID（主キー）',
    cognito_user_id VARCHAR(255) UNIQUE NOT NULL COMMENT 'AWS Cognito ユーザーID（一意）',
    email VARCHAR(255) UNIQUE NOT NULL COMMENT 'メールアドレス（一意、ログイン用）',
    username VARCHAR(100) NOT NULL COMMENT 'ユーザー名（表示用）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'レコード作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'レコード更新日時',
    
    -- インデックス定義
    INDEX idx_cognito_user_id (cognito_user_id) COMMENT 'Cognito ユーザーID検索用インデックス',
    INDEX idx_email (email) COMMENT 'メールアドレス検索用インデックス'
) COMMENT 'ユーザー基本情報テーブル - AWS Cognito と連携したユーザー管理';

-- ユーザープロファイルテーブル
-- ユーザーの詳細情報（プロフィール）を管理
CREATE TABLE user_profiles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'プロファイルID（主キー）',
    user_id BIGINT NOT NULL COMMENT 'ユーザーID（外部キー）',
    first_name VARCHAR(100) COMMENT '名前',
    last_name VARCHAR(100) COMMENT '姓',
    avatar_url VARCHAR(500) COMMENT 'アバター画像のURL',
    bio TEXT COMMENT '自己紹介文',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'レコード作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'レコード更新日時',
    
    -- 外部キー制約
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE COMMENT 'ユーザーテーブルへの外部キー（カスケード削除）'
) COMMENT 'ユーザープロファイル情報テーブル - ユーザーの詳細情報を管理';

-- 開発環境用サンプルデータの挿入
-- テスト・開発用のユーザーデータを作成

-- サンプルユーザーの作成
INSERT INTO users (cognito_user_id, email, username) VALUES
('dev-user-1', 'dev@example.com', 'devuser'),    -- 開発用ユーザー
('dev-user-2', 'test@example.com', 'testuser');  -- テスト用ユーザー

-- サンプルユーザーのプロファイル情報
INSERT INTO user_profiles (user_id, first_name, last_name, bio) VALUES
(1, '開発', 'ユーザー', 'システム開発・テスト用のユーザーアカウントです'),
(2, 'テスト', 'ユーザー', 'アプリケーションテスト用のユーザーアカウントです');