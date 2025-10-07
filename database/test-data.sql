-- CSR Lambda Development Test Data
-- テスト用のユーザーデータを挿入

USE csr_lambda_dev;

-- テストユーザーの挿入
INSERT INTO users (cognito_user_id, email, username, created_at, updated_at) VALUES
('test_user_cognito_id', 'test@example.com', 'testuser', NOW(), NOW()),
('admin_user_cognito_id', 'admin@example.com', 'admin', NOW(), NOW()),
('demo_user_cognito_id', 'demo@example.com', 'demo', NOW(), NOW())
ON DUPLICATE KEY UPDATE
    email = VALUES(email),
    username = VALUES(username),
    updated_at = NOW();

-- テストデータの確認
SELECT * FROM users;

-- 追加のテストデータ（必要に応じて）
-- INSERT INTO other_tables ...