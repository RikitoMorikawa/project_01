"""
AWS Cognito JWT トークン検証と認証ユーティリティ

AWS Cognito で発行された JWT トークンの検証、ユーザー情報の取得、
トークンリフレッシュなどの認証関連機能を提供する。
"""
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError, InvalidSignatureError
import requests
from functools import lru_cache

from app.config import settings
from app.exceptions import AuthenticationError, ExternalServiceError

logger = logging.getLogger(__name__)


class CognitoTokenVerifier:
    """
    AWS Cognito JWT トークン検証クラス
    
    Cognito で発行された JWT トークンの検証、ユーザー情報の取得、
    トークンリフレッシュなどの機能を提供する。
    """
    
    def __init__(self):
        """
        CognitoTokenVerifier を初期化する
        
        設定から AWS リージョン、ユーザープール ID、クライアント ID を取得し、
        JWKS クライアントと Cognito クライアントを遅延初期化する。
        """
        self.region = settings.aws_region
        self.user_pool_id = settings.cognito_user_pool_id
        self.client_id = settings.cognito_client_id
        self._jwks_client = None
        self._cognito_client = None
    
    @property
    def jwks_client(self) -> PyJWKClient:
        """
        JWKS クライアントを取得または作成する
        
        トークン検証用の JWKS（JSON Web Key Set）クライアントを
        遅延初期化で作成し、キャッシュする。
        
        Returns:
            PyJWKClient: JWT トークン検証用の JWKS クライアント
            
        Raises:
            AuthenticationError: Cognito ユーザープール ID が設定されていない場合
        """
        if self._jwks_client is None:
            if not self.user_pool_id:
                raise AuthenticationError("Cognito User Pool ID not configured")
            
            jwks_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
            self._jwks_client = PyJWKClient(jwks_url)
        
        return self._jwks_client
    
    @jwks_client.setter
    def jwks_client(self, value):
        """JWKS クライアントを設定する（テスト用）"""
        self._jwks_client = value
    
    @jwks_client.deleter
    def jwks_client(self):
        """JWKS クライアントを削除する（テスト用）"""
        self._jwks_client = None
    
    @property
    def cognito_client(self):
        """
        Cognito クライアントを取得または作成する
        
        AWS Cognito Identity Provider サービスとの通信用クライアントを
        遅延初期化で作成し、キャッシュする。
        
        Returns:
            boto3.client: Cognito Identity Provider クライアント
        """
        if self._cognito_client is None:
            self._cognito_client = boto3.client('cognito-idp', region_name=self.region)
        return self._cognito_client
    
    @cognito_client.setter
    def cognito_client(self, value):
        """Cognito クライアントを設定する（テスト用）"""
        self._cognito_client = value
    
    @cognito_client.deleter
    def cognito_client(self):
        """Cognito クライアントを削除する（テスト用）"""
        self._cognito_client = None
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        JWT トークンを検証してデコードされたクレームを返す
        
        Cognito で発行された JWT アクセストークンの署名、有効期限、
        発行者などを検証し、トークンに含まれるユーザー情報を返す。
        
        Args:
            token (str): 検証する JWT トークン
            
        Returns:
            Dict[str, Any]: デコードされたトークンクレーム
            
        Raises:
            AuthenticationError: トークンが無効、期限切れ、署名エラーの場合
        """
        try:
            # 署名キーを取得
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            # トークンをデコードして検証
            decoded_token = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"
            )
            
            # トークンタイプを検証（アクセストークンのみ受け入れ）
            if decoded_token.get('token_use') != 'access':
                raise AuthenticationError("Invalid token type")
            
            # 有効期限を検証
            exp = decoded_token.get('exp')
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                raise AuthenticationError("Token has expired")
            
            logger.info(f"トークン検証成功: ユーザー {decoded_token.get('username')}")
            return decoded_token
            
        except ExpiredSignatureError:
            raise AuthenticationError("認証トークンの有効期限が切れています")
        except InvalidSignatureError:
            raise AuthenticationError("認証トークンの署名が無効です")
        except InvalidTokenError as e:
            raise AuthenticationError(f"認証トークンが無効です: {str(e)}")
        except Exception as e:
            logger.error(f"トークン検証失敗: {str(e)}")
            raise AuthenticationError("認証トークンの検証に失敗しました")
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from Cognito using access token
        """
        try:
            response = self.cognito_client.get_user(AccessToken=access_token)
            
            # Convert user attributes to dict
            user_attributes = {}
            for attr in response.get('UserAttributes', []):
                user_attributes[attr['Name']] = attr['Value']
            
            return {
                'username': response.get('Username'),
                'user_status': response.get('UserStatus'),
                'attributes': user_attributes,
                'mfa_options': response.get('MFAOptions', [])
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NotAuthorizedException':
                raise AuthenticationError("アクセストークンが無効または期限切れです")
            else:
                logger.error(f"Cognito API エラー: {error_code}")
                raise ExternalServiceError("Cognito", f"ユーザー情報の取得に失敗しました: {error_code}")
        except BotoCoreError as e:
            logger.error(f"AWS SDK エラー: {str(e)}")
            raise ExternalServiceError("AWS", "Cognito サービスへの接続に失敗しました")
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token
        """
        try:
            response = self.cognito_client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': refresh_token
                }
            )
            
            auth_result = response.get('AuthenticationResult', {})
            return {
                'access_token': auth_result.get('AccessToken'),
                'id_token': auth_result.get('IdToken'),
                'token_type': auth_result.get('TokenType', 'Bearer'),
                'expires_in': auth_result.get('ExpiresIn')
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NotAuthorizedException':
                raise AuthenticationError("リフレッシュトークンが無効または期限切れです")
            else:
                logger.error(f"Cognito API エラー: {error_code}")
                raise ExternalServiceError("Cognito", f"トークンのリフレッシュに失敗しました: {error_code}")
        except BotoCoreError as e:
            logger.error(f"AWS SDK エラー: {str(e)}")
            raise ExternalServiceError("AWS", "Cognito サービスへの接続に失敗しました")
    
    async def check_cognito_health(self) -> Dict[str, Any]:
        """
        Check Cognito service health
        """
        try:
            # Try to describe user pool to test connectivity
            response = self.cognito_client.describe_user_pool(UserPoolId=self.user_pool_id)
            
            if response.get('UserPool'):
                return {
                    "status": "healthy",
                    "message": "Cognito service is accessible"
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Cognito service returned unexpected response"
                }
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            return {
                "status": "unhealthy",
                "message": f"Cognito service error: {error_code}"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Cognito health check failed: {str(e)}"
            }


# Global instance
cognito_verifier = CognitoTokenVerifier()


@lru_cache(maxsize=100)
def get_cognito_public_keys() -> Dict[str, Any]:
    """
    Get Cognito public keys for token verification (cached)
    """
    try:
        if not settings.cognito_user_pool_id:
            raise ValueError("Cognito User Pool ID not configured")
        
        jwks_url = f"https://cognito-idp.{settings.aws_region}.amazonaws.com/{settings.cognito_user_pool_id}/.well-known/jwks.json"
        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch Cognito public keys: {str(e)}")
        raise ExternalServiceError("Cognito", "Failed to fetch public keys")


def extract_token_from_header(authorization_header: str) -> str:
    """
    Authorization ヘッダーから JWT トークンを抽出する
    
    Args:
        authorization_header (str): Authorization ヘッダーの値
        
    Returns:
        str: 抽出された JWT トークン
        
    Raises:
        AuthenticationError: ヘッダーが無効な場合
    """
    if not authorization_header:
        raise AuthenticationError("認証ヘッダーが提供されていません")
    
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise AuthenticationError("認証ヘッダーの形式が正しくありません")
    
    return parts[1]


def get_user_from_token(token: str) -> Dict[str, Any]:
    """
    JWT トークンからユーザー情報を取得する
    
    Args:
        token (str): JWT トークン
        
    Returns:
        Dict[str, Any]: ユーザー情報
        
    Raises:
        AuthenticationError: トークンからユーザー情報を取得できない場合
    """
    try:
        decoded_token = cognito_verifier.verify_token(token)
        
        return {
            'cognito_user_id': decoded_token.get('sub'),
            'username': decoded_token.get('username'),
            'email': decoded_token.get('email'),
            'token_use': decoded_token.get('token_use'),
            'client_id': decoded_token.get('client_id'),
            'scope': decoded_token.get('scope', '').split(),
            'exp': decoded_token.get('exp'),
            'iat': decoded_token.get('iat')
        }
        
    except Exception as e:
        logger.error(f"トークンからのユーザー情報取得失敗: {str(e)}")
        raise AuthenticationError("トークンからユーザー情報を取得できませんでした")