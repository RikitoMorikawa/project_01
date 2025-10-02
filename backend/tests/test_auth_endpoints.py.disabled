"""
認証エンドポイントの単体テスト
Unit tests for authentication endpoints
"""
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from app.exceptions import AuthenticationError, ExternalServiceError


class TestAuthEndpoints:
    """認証エンドポイントのテストクラス / Authentication endpoints test class"""
    
    def test_login_success(self, client: TestClient, mock_cognito_client, mock_request_id):
        """ログイン成功のテスト / Test successful login"""
        with patch('app.auth.cognito.cognito_verifier.cognito_client', mock_cognito_client), \
             patch('app.auth.cognito.cognito_verifier.verify_token') as mock_verify:
            
            # モックトークン検証の設定 / Setup mock token verification
            mock_verify.return_value = {
                'sub': 'test-cognito-id',
                'username': 'testuser',
                'email': 'test@example.com',
                'scope': 'openid email profile'
            }
            
            # ログインリクエスト / Login request
            response = client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "testpassword123"
            })
            
            # レスポンス検証 / Response verification
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "access_token" in data["data"]
            assert "user" in data["data"]
            assert data["data"]["user"]["email"] == "test@example.com"
    
    def test_login_invalid_credentials(self, client: TestClient, mock_cognito_client, mock_request_id):
        """無効な認証情報でのログインテスト / Test login with invalid credentials"""
        # NotAuthorizedExceptionを発生させる / Raise NotAuthorizedException
        mock_cognito_client.initiate_auth.side_effect = mock_cognito_client.exceptions.NotAuthorizedException()
        
        with patch('app.auth.cognito.cognito_verifier.cognito_client', mock_cognito_client):
            response = client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "wrongpassword"
            })
            
            assert response.status_code == 401
            data = response.json()
            assert data["status"] == "error"
            assert data["error_code"] == "INVALID_CREDENTIALS"
    
    def test_login_user_not_confirmed(self, client: TestClient, mock_cognito_client, mock_request_id):
        """未確認ユーザーのログインテスト / Test login with unconfirmed user"""
        mock_cognito_client.initiate_auth.side_effect = mock_cognito_client.exceptions.UserNotConfirmedException()
        
        with patch('app.auth.cognito.cognito_verifier.cognito_client', mock_cognito_client):
            response = client.post("/api/v1/auth/login", json={
                "email": "unconfirmed@example.com",
                "password": "testpassword123"
            })
            
            assert response.status_code == 401
            data = response.json()
            assert data["status"] == "error"
            assert data["error_code"] == "USER_NOT_CONFIRMED"
    
    def test_login_user_not_found(self, client: TestClient, mock_cognito_client, mock_request_id):
        """存在しないユーザーのログインテスト / Test login with non-existent user"""
        mock_cognito_client.initiate_auth.side_effect = mock_cognito_client.exceptions.UserNotFoundException()
        
        with patch('app.auth.cognito.cognito_verifier.cognito_client', mock_cognito_client):
            response = client.post("/api/v1/auth/login", json={
                "email": "nonexistent@example.com",
                "password": "testpassword123"
            })
            
            assert response.status_code == 401
            data = response.json()
            assert data["status"] == "error"
            assert data["error_code"] == "USER_NOT_FOUND"
    
    def test_login_too_many_requests(self, client: TestClient, mock_cognito_client, mock_request_id):
        """リクエスト過多のログインテスト / Test login with too many requests"""
        mock_cognito_client.initiate_auth.side_effect = mock_cognito_client.exceptions.TooManyRequestsException()
        
        with patch('app.auth.cognito.cognito_verifier.cognito_client', mock_cognito_client):
            response = client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "testpassword123"
            })
            
            assert response.status_code == 429
            data = response.json()
            assert data["status"] == "error"
            assert data["error_code"] == "TOO_MANY_REQUESTS"
    
    def test_login_invalid_email_format(self, client: TestClient, mock_request_id):
        """無効なメール形式のテスト / Test invalid email format"""
        response = client.post("/api/v1/auth/login", json={
            "email": "invalid-email",
            "password": "testpassword123"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_refresh_token_success(self, client: TestClient, mock_cognito_client, mock_request_id):
        """トークン更新成功のテスト / Test successful token refresh"""
        with patch('app.auth.cognito.cognito_verifier.refresh_token') as mock_refresh:
            mock_refresh.return_value = {
                'access_token': 'new-access-token',
                'token_type': 'Bearer',
                'expires_in': 3600
            }
            
            response = client.post("/api/v1/auth/refresh", json={
                "refresh_token": "valid-refresh-token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["access_token"] == "new-access-token"
    
    def test_refresh_token_invalid(self, client: TestClient, mock_request_id):
        """無効なリフレッシュトークンのテスト / Test invalid refresh token"""
        with patch('app.auth.cognito.cognito_verifier.refresh_token') as mock_refresh:
            mock_refresh.side_effect = AuthenticationError("Invalid refresh token")
            
            response = client.post("/api/v1/auth/refresh", json={
                "refresh_token": "invalid-refresh-token"
            })
            
            assert response.status_code == 401
            data = response.json()
            assert data["status"] == "error"
            assert data["error_code"] == "INVALID_REFRESH_TOKEN"
    
    def test_refresh_token_service_error(self, client: TestClient, mock_request_id):
        """リフレッシュトークンサービスエラーのテスト / Test refresh token service error"""
        with patch('app.auth.cognito.cognito_verifier.refresh_token') as mock_refresh:
            mock_refresh.side_effect = ExternalServiceError("Cognito", "Service unavailable")
            
            response = client.post("/api/v1/auth/refresh", json={
                "refresh_token": "valid-refresh-token"
            })
            
            assert response.status_code == 502
            data = response.json()
            assert data["status"] == "error"
            assert data["error_code"] == "SERVICE_ERROR"
    
    def test_logout_success(self, client: TestClient, mock_cognito_client, mock_current_user, mock_request_id):
        """ログアウト成功のテスト / Test successful logout"""
        with patch('app.auth.cognito.cognito_verifier.cognito_client', mock_cognito_client):
            response = client.post("/api/v1/auth/logout", headers={
                "Authorization": "Bearer valid-access-token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "logout_time" in data["data"]
    
    def test_logout_invalid_token(self, client: TestClient, mock_cognito_client, mock_request_id):
        """無効なトークンでのログアウトテスト / Test logout with invalid token"""
        mock_cognito_client.global_sign_out.side_effect = mock_cognito_client.exceptions.NotAuthorizedException()
        
        with patch('app.auth.cognito.cognito_verifier.cognito_client', mock_cognito_client), \
             patch('app.auth.dependencies.get_current_user') as mock_get_user:
            
            mock_get_user.return_value = {'username': 'testuser'}
            
            response = client.post("/api/v1/auth/logout", headers={
                "Authorization": "Bearer invalid-token"
            })
            
            # 無効なトークンでもログアウト成功として扱う / Treat as successful logout even with invalid token
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
    
    def test_get_current_user_info_success(self, client: TestClient, mock_current_user, mock_request_id):
        """現在のユーザー情報取得成功のテスト / Test successful get current user info"""
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer valid-access-token"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "user" in data["data"]
        assert "token_info" in data["data"]
    
    def test_verify_token_success(self, client: TestClient, mock_request_id):
        """トークン検証成功のテスト / Test successful token verification"""
        with patch('app.auth.cognito.cognito_verifier.verify_token') as mock_verify:
            mock_verify.return_value = {
                'sub': 'test-cognito-id',
                'username': 'testuser',
                'email': 'test@example.com',
                'scope': 'openid email profile',
                'exp': 1704067200,
                'iat': 1704063600
            }
            
            response = client.post("/api/v1/auth/verify", headers={
                "Authorization": "Bearer valid-token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["valid"] is True
            assert "claims" in data["data"]
    
    def test_verify_token_invalid(self, client: TestClient, mock_request_id):
        """無効なトークン検証のテスト / Test invalid token verification"""
        with patch('app.auth.cognito.cognito_verifier.verify_token') as mock_verify:
            mock_verify.side_effect = AuthenticationError("Invalid token")
            
            response = client.post("/api/v1/auth/verify", headers={
                "Authorization": "Bearer invalid-token"
            })
            
            assert response.status_code == 401
            data = response.json()
            assert data["status"] == "error"
            assert data["error_code"] == "INVALID_TOKEN"
    
    def test_verify_token_missing_authorization(self, client: TestClient, mock_request_id):
        """認証ヘッダー不足のテスト / Test missing authorization header"""
        response = client.post("/api/v1/auth/verify")
        
        assert response.status_code == 401
        data = response.json()
        assert data["status"] == "error"
        assert data["error_code"] == "MISSING_TOKEN"
    
    def test_login_challenge_response(self, client: TestClient, mock_cognito_client, mock_request_id):
        """ログインチャレンジレスポンスのテスト / Test login challenge response"""
        # MFAチャレンジを返すように設定 / Setup to return MFA challenge
        mock_cognito_client.initiate_auth.return_value = {
            'ChallengeName': 'SMS_MFA',
            'Session': 'challenge-session-token',
            'ChallengeParameters': {
                'CODE_DELIVERY_DELIVERY_MEDIUM': 'SMS',
                'CODE_DELIVERY_DESTINATION': '+81***1234'
            }
        }
        
        with patch('app.auth.cognito.cognito_verifier.cognito_client', mock_cognito_client):
            response = client.post("/api/v1/auth/login", json={
                "email": "mfa-user@example.com",
                "password": "testpassword123"
            })
            
            assert response.status_code == 202
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["challenge"] == "SMS_MFA"
            assert "session" in data["data"]
    
    def test_login_unexpected_response(self, client: TestClient, mock_cognito_client, mock_request_id):
        """予期しないレスポンスのテスト / Test unexpected response"""
        # 予期しないレスポンス構造 / Unexpected response structure
        mock_cognito_client.initiate_auth.return_value = {
            'UnexpectedField': 'unexpected_value'
        }
        
        with patch('app.auth.cognito.cognito_verifier.cognito_client', mock_cognito_client):
            response = client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "testpassword123"
            })
            
            assert response.status_code == 500
            data = response.json()
            assert data["status"] == "error"
            assert data["error_code"] == "UNEXPECTED_RESPONSE"