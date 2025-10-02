"""
テスト設定とフィクスチャ
Test configuration and fixtures
"""
import pytest
import asyncio
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch
import pymysql
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """イベントループフィクスチャ / Event loop fixture"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> TestClient:
    """FastAPI テストクライアント / FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_db_connection():
    """モックデータベース接続 / Mock database connection"""
    mock_connection = Mock(spec=pymysql.Connection)
    mock_cursor = Mock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.cursor.return_value.__exit__.return_value = None
    return mock_connection, mock_cursor


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """サンプルユーザーデータ / Sample user data"""
    return {
        "id": 1,
        "cognito_user_id": "test-cognito-id-123",
        "email": "test@example.com",
        "username": "testuser",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def sample_user_profile_data() -> Dict[str, Any]:
    """サンプルユーザープロファイルデータ / Sample user profile data"""
    return {
        "id": 1,
        "user_id": 1,
        "first_name": "テスト",
        "last_name": "ユーザー",
        "avatar_url": "https://example.com/avatar.jpg",
        "bio": "テストユーザーの自己紹介",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def mock_cognito_token_claims() -> Dict[str, Any]:
    """モックCognitoトークンクレーム / Mock Cognito token claims"""
    return {
        "sub": "test-cognito-id-123",
        "username": "testuser",
        "email": "test@example.com",
        "token_use": "access",
        "client_id": "test-client-id",
        "scope": "openid email profile",
        "exp": 1704067200,  # 2024-01-01 00:00:00 UTC
        "iat": 1704063600   # 2023-12-31 23:00:00 UTC
    }


@pytest.fixture
def mock_cognito_verifier():
    """モックCognito検証器 / Mock Cognito verifier"""
    with patch('app.auth.cognito.cognito_verifier') as mock_verifier:
        yield mock_verifier


@pytest.fixture
def authenticated_headers(mock_cognito_token_claims) -> Dict[str, str]:
    """認証済みリクエストヘッダー / Authenticated request headers"""
    return {
        "Authorization": "Bearer test-jwt-token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def mock_database_operations():
    """データベース操作のモック / Mock database operations"""
    with patch('app.database.get_db') as mock_get_db, \
         patch('app.database.execute_query') as mock_execute_query, \
         patch('app.database.execute_update') as mock_execute_update, \
         patch('app.database.execute_insert') as mock_execute_insert:
        
        # モック接続を返す / Return mock connection
        mock_connection = Mock()
        mock_get_db.return_value = mock_connection
        
        yield {
            'get_db': mock_get_db,
            'execute_query': mock_execute_query,
            'execute_update': mock_execute_update,
            'execute_insert': mock_execute_insert,
            'connection': mock_connection
        }


@pytest.fixture
def mock_request_id():
    """モックリクエストID / Mock request ID"""
    with patch('app.dependencies.get_request_id') as mock_get_request_id:
        mock_get_request_id.return_value = "test-request-id-123"
        yield mock_get_request_id


@pytest.fixture
def mock_current_user(mock_cognito_token_claims):
    """モック現在のユーザー / Mock current user"""
    with patch('app.auth.dependencies.get_current_user') as mock_get_current_user:
        mock_get_current_user.return_value = {
            'cognito_user_id': mock_cognito_token_claims['sub'],
            'username': mock_cognito_token_claims['username'],
            'email': mock_cognito_token_claims['email'],
            'scope': mock_cognito_token_claims['scope'].split(),
            'client_id': mock_cognito_token_claims['client_id'],
            'exp': mock_cognito_token_claims['exp']
        }
        yield mock_get_current_user


@pytest.fixture
def mock_admin_user(mock_cognito_token_claims):
    """モック管理者ユーザー / Mock admin user"""
    with patch('app.auth.dependencies.get_current_user') as mock_get_current_user:
        mock_get_current_user.return_value = {
            'cognito_user_id': mock_cognito_token_claims['sub'],
            'username': 'admin_user',
            'email': 'admin@example.com',
            'scope': ['admin', 'user:read', 'user:write'],
            'client_id': mock_cognito_token_claims['client_id'],
            'exp': mock_cognito_token_claims['exp']
        }
        yield mock_get_current_user


class MockCognitoClient:
    """モックCognitoクライアント / Mock Cognito client"""
    
    def __init__(self):
        self.exceptions = Mock()
        self.exceptions.NotAuthorizedException = Exception
        self.exceptions.UserNotConfirmedException = Exception
        self.exceptions.UserNotFoundException = Exception
        self.exceptions.TooManyRequestsException = Exception
    
    def initiate_auth(self, **kwargs):
        """モック認証開始 / Mock initiate auth"""
        return {
            'AuthenticationResult': {
                'AccessToken': 'mock-access-token',
                'IdToken': 'mock-id-token',
                'RefreshToken': 'mock-refresh-token',
                'TokenType': 'Bearer',
                'ExpiresIn': 3600
            }
        }
    
    def global_sign_out(self, **kwargs):
        """モックグローバルサインアウト / Mock global sign out"""
        return {'ResponseMetadata': {'HTTPStatusCode': 200}}
    
    def describe_user_pool(self, **kwargs):
        """モックユーザープール記述 / Mock describe user pool"""
        return {
            'UserPool': {
                'Id': 'test-user-pool-id',
                'Name': 'test-user-pool'
            }
        }


@pytest.fixture
def mock_cognito_client():
    """モックCognitoクライアントフィクスチャ / Mock Cognito client fixture"""
    return MockCognitoClient()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """テスト環境のセットアップ / Test environment setup"""
    # テスト用の設定を適用 / Apply test configuration
    original_environment = settings.environment
    settings.environment = "test"
    
    yield
    
    # 元の設定を復元 / Restore original configuration
    settings.environment = original_environment