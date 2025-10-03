-- データ保護・プライバシー機能用テーブル定義
-- GDPR および個人情報保護法対応のためのテーブル追加

USE csr_lambda_dev;

-- 既存テーブルへのカラム追加（データ保持期間管理用）
ALTER TABLE users 
ADD COLUMN deleted_at TIMESTAMP NULL COMMENT '論理削除日時（NULL=有効、値あり=削除済み）',
ADD COLUMN data_retention_expiry TIMESTAMP NULL COMMENT 'データ保持期限日時';

ALTER TABLE user_profiles 
ADD COLUMN deleted_at TIMESTAMP NULL COMMENT '論理削除日時（NULL=有効、値あり=削除済み）';

-- 監査ログテーブル
-- 個人データへのアクセス・操作を記録
CREATE TABLE audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '監査ログID（主キー）',
    user_id BIGINT NULL COMMENT '操作実行ユーザーID（NULL=システム操作）',
    action VARCHAR(50) NOT NULL COMMENT '実行されたアクション（create/read/update/delete/export/login/logout）',
    data_category VARCHAR(50) NOT NULL COMMENT 'データカテゴリ（personal_info/profile_data/auth_data/system_data）',
    target_user_id BIGINT NULL COMMENT '操作対象ユーザーID（NULL=システム全体操作）',
    details JSON NULL COMMENT '操作詳細情報（JSON形式）',
    ip_address VARCHAR(45) NULL COMMENT 'クライアントIPアドレス（IPv4/IPv6対応）',
    user_agent TEXT NULL COMMENT 'ユーザーエージェント情報',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'ログ記録日時',
    
    -- インデックス定義
    INDEX idx_user_id (user_id) COMMENT '操作実行ユーザー検索用インデックス',
    INDEX idx_target_user_id (target_user_id) COMMENT '操作対象ユーザー検索用インデックス',
    INDEX idx_action (action) COMMENT 'アクション種別検索用インデックス',
    INDEX idx_created_at (created_at) COMMENT '日時範囲検索用インデックス',
    INDEX idx_data_category (data_category) COMMENT 'データカテゴリ検索用インデックス',
    
    -- 外部キー制約
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL COMMENT '操作実行ユーザーへの外部キー',
    FOREIGN KEY (target_user_id) REFERENCES users(id) ON DELETE SET NULL COMMENT '操作対象ユーザーへの外部キー'
) COMMENT '監査ログテーブル - 個人データアクセス・操作の記録';

-- データ削除リクエストテーブル
-- GDPR「忘れられる権利」対応のためのデータ削除リクエスト管理
CREATE TABLE data_deletion_requests (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '削除リクエストID（主キー）',
    user_id BIGINT NOT NULL COMMENT '削除対象ユーザーID',
    reason TEXT NULL COMMENT '削除理由・根拠',
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending' COMMENT 'リクエスト処理状況',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'リクエスト作成日時',
    processed_at TIMESTAMP NULL COMMENT 'リクエスト処理完了日時',
    processor_user_id BIGINT NULL COMMENT 'リクエスト処理実行者ID',
    processing_notes TEXT NULL COMMENT '処理時の備考・エラー情報',
    
    -- インデックス定義
    INDEX idx_user_id (user_id) COMMENT '削除対象ユーザー検索用インデックス',
    INDEX idx_status (status) COMMENT 'ステータス検索用インデックス',
    INDEX idx_requested_at (requested_at) COMMENT 'リクエスト日時検索用インデックス',
    
    -- 外部キー制約
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE COMMENT '削除対象ユーザーへの外部キー',
    FOREIGN KEY (processor_user_id) REFERENCES users(id) ON DELETE SET NULL COMMENT '処理実行者への外部キー'
) COMMENT 'データ削除リクエストテーブル - GDPR忘れられる権利対応';

-- ユーザー同意管理テーブル
-- プライバシーポリシー・利用規約への同意履歴管理
CREATE TABLE user_consents (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '同意記録ID（主キー）',
    user_id BIGINT NOT NULL COMMENT 'ユーザーID',
    consent_type ENUM('privacy_policy', 'terms_of_service', 'cookie_policy', 'marketing') NOT NULL COMMENT '同意種別',
    consent_version VARCHAR(20) NOT NULL COMMENT '同意したポリシー・規約のバージョン',
    consented BOOLEAN NOT NULL DEFAULT FALSE COMMENT '同意フラグ（TRUE=同意、FALSE=拒否）',
    consent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '同意・拒否日時',
    ip_address VARCHAR(45) NULL COMMENT '同意時のIPアドレス',
    user_agent TEXT NULL COMMENT '同意時のユーザーエージェント',
    withdrawn_at TIMESTAMP NULL COMMENT '同意撤回日時（NULL=有効、値あり=撤回済み）',
    
    -- インデックス定義
    INDEX idx_user_id (user_id) COMMENT 'ユーザー検索用インデックス',
    INDEX idx_consent_type (consent_type) COMMENT '同意種別検索用インデックス',
    INDEX idx_consent_date (consent_date) COMMENT '同意日時検索用インデックス',
    INDEX idx_user_consent_type (user_id, consent_type) COMMENT 'ユーザー・同意種別複合インデックス',
    
    -- 外部キー制約
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE COMMENT 'ユーザーテーブルへの外部キー'
) COMMENT 'ユーザー同意管理テーブル - プライバシーポリシー等への同意履歴';

-- データ処理活動記録テーブル
-- 個人データの処理活動を記録（GDPR Article 30 対応）
CREATE TABLE data_processing_activities (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '処理活動ID（主キー）',
    activity_name VARCHAR(255) NOT NULL COMMENT '処理活動名',
    purpose TEXT NOT NULL COMMENT '処理目的',
    legal_basis VARCHAR(100) NOT NULL COMMENT '法的根拠',
    data_categories TEXT NOT NULL COMMENT '処理する個人データのカテゴリ',
    data_subjects TEXT NOT NULL COMMENT 'データ主体のカテゴリ',
    recipients TEXT NULL COMMENT '個人データの受領者',
    third_country_transfers TEXT NULL COMMENT '第三国への移転情報',
    retention_period VARCHAR(100) NULL COMMENT 'データ保持期間',
    security_measures TEXT NULL COMMENT 'セキュリティ対策',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '記録作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '記録更新日時',
    
    -- インデックス定義
    INDEX idx_activity_name (activity_name) COMMENT '処理活動名検索用インデックス',
    INDEX idx_created_at (created_at) COMMENT '作成日時検索用インデックス'
) COMMENT 'データ処理活動記録テーブル - GDPR Article 30 対応';

-- セキュリティインシデント記録テーブル
-- データ漏洩・セキュリティ事故の記録管理
CREATE TABLE security_incidents (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'インシデントID（主キー）',
    incident_type ENUM('data_breach', 'unauthorized_access', 'system_compromise', 'other') NOT NULL COMMENT 'インシデント種別',
    severity ENUM('low', 'medium', 'high', 'critical') NOT NULL COMMENT '重要度',
    title VARCHAR(255) NOT NULL COMMENT 'インシデントタイトル',
    description TEXT NOT NULL COMMENT 'インシデント詳細説明',
    affected_users_count INT DEFAULT 0 COMMENT '影響を受けたユーザー数',
    affected_data_types TEXT NULL COMMENT '影響を受けたデータの種類',
    detection_date TIMESTAMP NOT NULL COMMENT 'インシデント検知日時',
    resolution_date TIMESTAMP NULL COMMENT 'インシデント解決日時',
    status ENUM('detected', 'investigating', 'contained', 'resolved') DEFAULT 'detected' COMMENT '対応状況',
    response_actions TEXT NULL COMMENT '対応措置の内容',
    reported_to_authority BOOLEAN DEFAULT FALSE COMMENT '監督機関への報告フラグ',
    authority_report_date TIMESTAMP NULL COMMENT '監督機関報告日時',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '記録作成日時',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '記録更新日時',
    
    -- インデックス定義
    INDEX idx_incident_type (incident_type) COMMENT 'インシデント種別検索用インデックス',
    INDEX idx_severity (severity) COMMENT '重要度検索用インデックス',
    INDEX idx_detection_date (detection_date) COMMENT '検知日時検索用インデックス',
    INDEX idx_status (status) COMMENT '対応状況検索用インデックス'
) COMMENT 'セキュリティインシデント記録テーブル - データ漏洩・セキュリティ事故管理';

-- 初期データの挿入

-- データ処理活動の初期記録
INSERT INTO data_processing_activities (
    activity_name, 
    purpose, 
    legal_basis, 
    data_categories, 
    data_subjects, 
    recipients, 
    retention_period, 
    security_measures
) VALUES 
(
    'ユーザーアカウント管理',
    'Webアプリケーションのユーザーアカウント作成・管理・認証',
    '契約の履行（利用規約に基づくサービス提供）',
    'メールアドレス、ユーザー名、プロファイル情報',
    'Webアプリケーション利用者',
    'AWS（クラウドインフラ提供者）',
    '7年間（アカウント削除後は即座に匿名化）',
    'データベース暗号化、アクセス制御、監査ログ、定期的なセキュリティ監査'
),
(
    'システム監査・ログ管理',
    'セキュリティ監視、不正アクセス検知、システム運用管理',
    '正当な利益（システムセキュリティ確保）',
    'IPアドレス、アクセスログ、操作履歴',
    'Webアプリケーション利用者',
    'システム管理者',
    '1年間（セキュリティ監査目的）',
    'ログデータ暗号化、アクセス制限、定期的なログローテーション'
);

-- 既存ユーザーのデータ保持期限設定（7年後）
UPDATE users 
SET data_retention_expiry = DATE_ADD(created_at, INTERVAL 7 YEAR)
WHERE data_retention_expiry IS NULL;

-- 開発環境用のサンプル同意記録
INSERT INTO user_consents (user_id, consent_type, consent_version, consented, ip_address) VALUES
(1, 'privacy_policy', '1.0', TRUE, '127.0.0.1'),
(1, 'terms_of_service', '1.0', TRUE, '127.0.0.1'),
(2, 'privacy_policy', '1.0', TRUE, '127.0.0.1'),
(2, 'terms_of_service', '1.0', TRUE, '127.0.0.1');