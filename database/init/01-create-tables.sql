-- Initialize database schema for development
USE csr_lambda_dev;

-- Create users table
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    cognito_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_cognito_user_id (cognito_user_id),
    INDEX idx_email (email)
);

-- Create user_profiles table
CREATE TABLE user_profiles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url VARCHAR(500),
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Insert sample data for development
INSERT INTO users (cognito_user_id, email, username) VALUES
('dev-user-1', 'dev@example.com', 'devuser'),
('dev-user-2', 'test@example.com', 'testuser');

INSERT INTO user_profiles (user_id, first_name, last_name, bio) VALUES
(1, 'Dev', 'User', 'Development user for testing'),
(2, 'Test', 'User', 'Test user for development');