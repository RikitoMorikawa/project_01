"""
Cognito認証機能の単体テスト
Unit tests for Cognito authentication functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import jwt
from botocore.exceptions import ClientError, BotoCoreError

from app.auth.cognito import CognitoTokenVerifier, get_user_from_token, extract_token_from_header
from app.exceptions import AuthenticationError, ExternalServiceError


class TestCognitoTokenVerifier:
    """CognitoTokenVerifierのテストクラス / CognitoTokenVerifier test class"""
    
    def test_init(self):
        """初期化テスト / Test initialization"""
        verifier = CognitoTokenVerifier()
        
        assert verifier.region is not None
        assert verifier.user_pool_id is not None
        assert verifier.client_id is not None
    
    def test_jwks_client_property(self):
        """JWKSクライアントプロパティのテスト / Test JWKS client property"""
        verifier = CognitoTokenVerifier()
        
        with patch('app.auth.cognito.PyJWKClient') as mock_jwks_client:
            mock_client = Mock()
            mock_jwks_client.return_value = mock_client
            
            # 初回アクセス / First access
            client1 = verifier.jwks_client
            assert client1 == mock_client
            
            # 2回目のアクセス（キャッシュされる） / Second access (should be cached)
            client2 = verifier.jwks_client
            assert client2 == mock_client
            
            # PyJWKClientは1回だけ呼ばれる / PyJWKClient should be called only once
            mock_jwks_client.assert_called_once()
    
    def test_cognito_client_property(self):
        """Cognitoクライアントプロパティのテスト / Test Cognito client property"""
        verifier = CognitoTokenVerifier()
        
        with patch('boto3.client') as mock_boto3_client:
            mock_client = Mock()
            mock_boto3_client.return_value = mock_client
            
            # 初回アクセス / First access
            client1 = verifier.cognito_client
            assert client1 == mock_client
            
            # 2回目のアクセス（キャッシュされる） / Second access (should be cached)
            client2 = verifier.cognito_client
            assert client2 == mock_client
            
            # boto3.clientは1回だけ呼ばれる / boto3.client should be called only once
            mock_boto3_client.assert_called_once_with('cognito-idp', region_name=verifier.region)
    
    def test_verify_token_success(self, mock_cognito_token_claims):
        """トークン検証成功のテスト / Test successful token verification"""
        verifier = CognitoTokenVerifier()
        
        with patch.object(verifier, 'jwks_client') as mock_jwks_client, \
             patch('jwt.decode') as mock_jwt_decode:
            
            # モック署名キー / Mock signing key
            mock_signing_key = Mock()
            mock_signing_key.key = "mock-key"
            mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key
            
            # モックデコード結果 / Mock decode result
            mock_jwt_decode.return_value = mock_cognito_token_claims
            
            result = verifier.verify_token("valid-jwt-token")
            
            assert result == mock_cognito_token_claims
            assert result['username'] == 'testuser'
            assert result['email'] == 'test@example.com'
    
    def test_verify_token_expired(self):
        """期限切れトークンの検証テスト / Test verification of expired token"""
        verifier = CognitoTokenVerifier()
        
        with patch.object(verifier, 'jwks_client') as mock_jwks_client, \
             patch('jwt.decode') as mock_jwt_decode:
            
            mock_signing_key = Mock()
            mock_signing_key.key = "mock-key"
            mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key
            
            # 期限切れ例外を発生 / Raise expired signature exception
            mock_jwt_decode.side_effect = jwt.ExpiredSignatureError("Token has expired")
            
            with pytest.raises(AuthenticationError) as exc_info:
                verifier.verify_token("expired-token")
            
            assert "expired" in str(exc_info.value)
    
    def test_verify_token_invalid_signature(self):
        """無効な署名のトークン検証テスト / Test verification of token with invalid signature"""
        verifier = CognitoTokenVerifier()
        
        with patch.object(verifier, 'jwks_client') as mock_jwks_client, \
             patch('jwt.decode') as mock_jwt_decode:
            
            mock_signing_key = Mock()
            mock_signing_key.key = "mock-key"
            mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key
            
            # 無効な署名例外を発生 / Raise invalid signature exception
            mock_jwt_decode.side_effect = jwt.InvalidSignatureError("Invalid signature")
            
            with pytest.raises(AuthenticationError) as exc_info:
                verifier.verify_token("invalid-signature-token")
            
            assert "signature" in str(exc_info.value)
    
    def test_verify_token_invalid_token_type(self, mock_cognito_token_claims):
        """無効なトークンタイプの検証テスト / Test verification of invalid token type"""
        verifier = CognitoTokenVerifier()
        
        # IDトークンのクレーム（accessではない） / ID token claims (not access)
        id_token_claims = mock_cognito_token_claims.copy()
        id_token_claims['token_use'] = 'id'
        
        with patch.object(verifier, 'jwks_client') as mock_jwks_client, \
             patch('jwt.decode') as mock_jwt_decode:
            
            mock_signing_key = Mock()
            mock_signing_key.key = "mock-key"
            mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key
            mock_jwt_decode.return_value = id_token_claims
            
            with pytest.raises(AuthenticationError) as exc_info:
                verifier.verify_token("id-token")
            
            assert "Invalid token type" in str(exc_info.value)
    
    def test_get_user_info_success(self):
        """ユーザー情報取得成功のテスト / Test successful get user info"""
        verifier = CognitoTokenVerifier()
        
        mock_response = {
            'Username': 'testuser',
            'UserStatus': 'CONFIRMED',
            'UserAttributes': [
                {'Name': 'email', 'Value': 'test@example.com'},
                {'Name': 'given_name', 'Value': 'テスト'},
                {'Name': 'family_name', 'Value': 'ユーザー'}
            ],
            'MFAOptions': []
        }
        
        with patch.object(verifier, 'cognito_client') as mock_cognito_client:
            mock_cognito_client.get_user.return_value = mock_response
            
            result = verifier.get_user_info("valid-access-token")
            
            assert result['username'] == 'testuser'
            assert result['user_status'] == 'CONFIRMED'
            assert result['attributes']['email'] == 'test@example.com'
            assert result['attributes']['given_name'] == 'テスト'
    
    def test_get_user_info_invalid_token(self):
        """無効なトークンでのユーザー情報取得テスト / Test get user info with invalid token"""
        verifier = CognitoTokenVerifier()
        
        with patch.object(verifier, 'cognito_client') as mock_cognito_client:
            # NotAuthorizedExceptionを発生 / Raise NotAuthorizedException
            error_response = {'Error': {'Code': 'NotAuthorizedException'}}
            mock_cognito_client.get_user.side_effect = ClientError(error_response, 'GetUser')
            
            with pytest.raises(AuthenticationError) as exc_info:
                verifier.get_user_info("invalid-token")
            
            assert "Invalid or expired access token" in str(exc_info.value)
    
    def test_get_user_info_service_error(self):
        """サービスエラーでのユーザー情報取得テスト / Test get user info with service error"""
        verifier = CognitoTokenVerifier()
        
        with patch.object(verifier, 'cognito_client') as mock_cognito_client:
            # その他のClientErrorを発生 / Raise other ClientError
            error_response = {'Error': {'Code': 'InternalErrorException'}}
            mock_cognito_client.get_user.side_effect = ClientError(error_response, 'GetUser')
            
            with pytest.raises(ExternalServiceError) as exc_info:
                verifier.get_user_info("valid-token")
            
            assert "Cognito" in str(exc_info.value)
    
    def test_refresh_token_success(self):
        """トークン更新成功のテスト / Test successful token refresh"""
        verifier = CognitoTokenVerifier()
        
        mock_response = {
            'AuthenticationResult': {
                'AccessToken': 'new-access-token',
                'IdToken': 'new-id-token',
                'TokenType': 'Bearer',
                'ExpiresIn': 3600
            }
        }
        
        with patch.object(verifier, 'cognito_client') as mock_cognito_client:
            mock_cognito_client.initiate_auth.return_value = mock_response
            
            result = verifier.refresh_token("valid-refresh-token")
            
            assert result['access_token'] == 'new-access-token'
            assert result['id_token'] == 'new-id-token'
            assert result['token_type'] == 'Bearer'
            assert result['expires_in'] == 3600
    
    def test_refresh_token_invalid(self):
        """無効なリフレッシュトークンのテスト / Test invalid refresh token"""
        verifier = CognitoTokenVerifier()
        
        with patch.object(verifier, 'cognito_client') as mock_cognito_client:
            error_response = {'Error': {'Code': 'NotAuthorizedException'}}
            mock_cognito_client.initiate_auth.side_effect = ClientError(error_response, 'InitiateAuth')
            
            with pytest.raises(AuthenticationError) as exc_info:
                verifier.refresh_token("invalid-refresh-token")
            
            assert "Invalid or expired refresh token" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_check_cognito_health_success(self):
        """Cognitoヘルスチェック成功のテスト / Test successful Cognito health check"""
        verifier = CognitoTokenVerifier()
        
        mock_response = {
            'UserPool': {
                'Id': 'test-user-pool-id',
                'Name': 'test-user-pool'
            }
        }
        
        with patch.object(verifier, 'cognito_client') as mock_cognito_client:
            mock_cognito_client.describe_user_pool.return_value = mock_response
            
            result = await verifier.check_cognito_health()
            
            assert result['status'] == 'healthy'
            assert 'accessible' in result['message']
    
    @pytest.mark.asyncio
    async def test_check_cognito_health_error(self):
        """Cognitoヘルスチェックエラーのテスト / Test Cognito health check error"""
        verifier = CognitoTokenVerifier()
        
        with patch.object(verifier, 'cognito_client') as mock_cognito_client:
            error_response = {'Error': {'Code': 'ResourceNotFoundException'}}
            mock_cognito_client.describe_user_pool.side_effect = ClientError(error_response, 'DescribeUserPool')
            
            result = await verifier.check_cognito_health()
            
            assert result['status'] == 'unhealthy'
            assert 'ResourceNotFoundException' in result['message']


class TestAuthUtilityFunctions:
    """認証ユーティリティ関数のテストクラス / Authentication utility functions test class"""
    
    def test_extract_token_from_header_success(self):
        """認証ヘッダーからのトークン抽出成功テスト / Test successful token extraction from header"""
        header = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        
        result = extract_token_from_header(header)
        
        assert result == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    
    def test_extract_token_from_header_missing(self):
        """認証ヘッダー不足のテスト / Test missing authorization header"""
        with pytest.raises(AuthenticationError) as exc_info:
            extract_token_from_header("")
        
        assert "missing" in str(exc_info.value)
    
    def test_extract_token_from_header_invalid_format(self):
        """無効な認証ヘッダー形式のテスト / Test invalid authorization header format"""
        # Bearerなしのヘッダー / Header without Bearer
        with pytest.raises(AuthenticationError) as exc_info:
            extract_token_from_header("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
        
        assert "Invalid authorization header format" in str(exc_info.value)
        
        # 複数のスペースを含むヘッダー / Header with multiple spaces
        with pytest.raises(AuthenticationError) as exc_info:
            extract_token_from_header("Bearer token extra")
        
        assert "Invalid authorization header format" in str(exc_info.value)
    
    def test_extract_token_from_header_wrong_scheme(self):
        """間違った認証スキームのテスト / Test wrong authentication scheme"""
        with pytest.raises(AuthenticationError) as exc_info:
            extract_token_from_header("Basic dXNlcjpwYXNzd29yZA==")
        
        assert "Invalid authorization header format" in str(exc_info.value)
    
    def test_get_user_from_token_success(self, mock_cognito_token_claims):
        """トークンからのユーザー情報取得成功テスト / Test successful get user from token"""
        with patch('app.auth.cognito.cognito_verifier.verify_token') as mock_verify:
            mock_verify.return_value = mock_cognito_token_claims
            
            result = get_user_from_token("valid-jwt-token")
            
            assert result['cognito_user_id'] == mock_cognito_token_claims['sub']
            assert result['username'] == mock_cognito_token_claims['username']
            assert result['email'] == mock_cognito_token_claims['email']
            assert result['scope'] == mock_cognito_token_claims['scope'].split()
    
    def test_get_user_from_token_verification_error(self):
        """トークン検証エラーでのユーザー情報取得テスト / Test get user from token with verification error"""
        with patch('app.auth.cognito.cognito_verifier.verify_token') as mock_verify:
            mock_verify.side_effect = AuthenticationError("Invalid token")
            
            with pytest.raises(AuthenticationError) as exc_info:
                get_user_from_token("invalid-token")
            
            assert "Failed to extract user information" in str(exc_info.value)
    
    def test_get_cognito_public_keys_success(self):
        """Cognito公開鍵取得成功のテスト / Test successful get Cognito public keys"""
        from app.auth.cognito import get_cognito_public_keys
        
        mock_jwks_response = {
            "keys": [
                {
                    "kid": "test-key-id",
                    "kty": "RSA",
                    "use": "sig",
                    "n": "test-modulus",
                    "e": "AQAB"
                }
            ]
        }
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # キャッシュをクリア / Clear cache
            get_cognito_public_keys.cache_clear()
            
            result = get_cognito_public_keys()
            
            assert result == mock_jwks_response
            assert len(result["keys"]) == 1
            assert result["keys"][0]["kid"] == "test-key-id"
    
    def test_get_cognito_public_keys_request_error(self):
        """Cognito公開鍵取得リクエストエラーのテスト / Test get Cognito public keys request error"""
        from app.auth.cognito import get_cognito_public_keys
        import requests
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.RequestException("Connection error")
            
            # キャッシュをクリア / Clear cache
            get_cognito_public_keys.cache_clear()
            
            with pytest.raises(ExternalServiceError) as exc_info:
                get_cognito_public_keys()
            
            assert "Cognito" in str(exc_info.value)
            assert "Failed to fetch public keys" in str(exc_info.value)


class TestCognitoIntegration:
    """Cognito統合テストクラス / Cognito integration test class"""
    
    def test_full_authentication_flow(self, mock_cognito_token_claims):
        """完全な認証フローのテスト / Test complete authentication flow"""
        verifier = CognitoTokenVerifier()
        
        # 1. トークン検証 / Token verification
        with patch.object(verifier, 'jwks_client') as mock_jwks_client, \
             patch('jwt.decode') as mock_jwt_decode:
            
            mock_signing_key = Mock()
            mock_signing_key.key = "mock-key"
            mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key
            mock_jwt_decode.return_value = mock_cognito_token_claims
            
            # トークン検証 / Verify token
            token_claims = verifier.verify_token("valid-jwt-token")
            assert token_claims['username'] == 'testuser'
            
            # ユーザー情報抽出 / Extract user info
            user_info = get_user_from_token("valid-jwt-token")
            assert user_info['cognito_user_id'] == mock_cognito_token_claims['sub']
            assert user_info['username'] == mock_cognito_token_claims['username']
    
    def test_token_refresh_flow(self):
        """トークン更新フローのテスト / Test token refresh flow"""
        verifier = CognitoTokenVerifier()
        
        # 1. 初回認証 / Initial authentication
        login_response = {
            'AuthenticationResult': {
                'AccessToken': 'initial-access-token',
                'RefreshToken': 'refresh-token',
                'ExpiresIn': 3600
            }
        }
        
        # 2. トークン更新 / Token refresh
        refresh_response = {
            'AuthenticationResult': {
                'AccessToken': 'new-access-token',
                'IdToken': 'new-id-token',
                'ExpiresIn': 3600
            }
        }
        
        with patch.object(verifier, 'cognito_client') as mock_cognito_client:
            # 初回ログイン / Initial login
            mock_cognito_client.initiate_auth.return_value = login_response
            
            # リフレッシュトークンでの更新 / Refresh with refresh token
            mock_cognito_client.initiate_auth.return_value = refresh_response
            
            result = verifier.refresh_token("refresh-token")
            
            assert result['access_token'] == 'new-access-token'
            assert result['id_token'] == 'new-id-token'