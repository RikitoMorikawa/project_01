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
    
    # コンテキストマネージャーとして動作するモックカーソルを作成
    mock_cursor_context = Mock()
    mock_cursor_context.__enter__ = Mock(return_value=mock_cursor)
    mock_cursor_context.__exit__ = Mock(return_value=None)
    
    mock_connection.cursor.return_value = mock_cursor_context
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
    import time
    current_time = int(time.time())
    return {
        "sub": "test-cognito-id-123",
        "username": "testuser",
        "email": "test@example.com",
        "token_use": "access",
        "client_id": "test-client-id",
        "scope": "openid email profile",
        "exp": current_time + 3600,  # 1 hour from now
        "iat": current_time - 300    # 5 minutes ago
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


@pytest.fixture
def mock_cloudwatch_metrics():
    """CloudWatch メトリクスのモック / Mock CloudWatch metrics"""
    with patch('app.utils.metrics.metrics') as mock_metrics:
        # モックメトリクスコレクターを設定
        mock_metrics._mock_mode = True
        mock_metrics.put_metric = Mock()
        mock_metrics.increment_counter = Mock()
        mock_metrics.put_metrics_batch = Mock()
        mock_metrics.add_to_buffer = Mock()
        mock_metrics.flush_buffer = Mock()
        yield mock_metrics


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """テスト環境のセットアップ / Test environment setup"""
    # テスト用の環境変数を設定 / Set test environment variables
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("COGNITO_USER_POOL_ID", "test-user-pool-id")
    monkeypatch.setenv("COGNITO_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-northeast-1")
    monkeypatch.setenv("MOCK_CLOUDWATCH", "true")
    
    # 設定を再読み込み / Reload settings
    from app.config import settings
    settings.environment = "test"
    settings.cognito_user_pool_id = "test-user-pool-id"
    settings.cognito_client_id = "test-client-id"
    settings.jwt_secret_key = "test-secret-key"
    
    yield