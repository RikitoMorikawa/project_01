"""
AWS Cognito JWT token verification and authentication utilities
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
    AWS Cognito JWT token verifier
    """
    
    def __init__(self):
        self.region = settings.aws_region
        self.user_pool_id = settings.cognito_user_pool_id
        self.client_id = settings.cognito_client_id
        self._jwks_client = None
        self._cognito_client = None
    
    @property
    def jwks_client(self) -> PyJWKClient:
        """Get or create JWKS client for token verification"""
        if self._jwks_client is None:
            if not self.user_pool_id:
                raise AuthenticationError("Cognito User Pool ID not configured")
            
            jwks_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
            self._jwks_client = PyJWKClient(jwks_url)
        
        return self._jwks_client
    
    @jwks_client.setter
    def jwks_client(self, value):
        """Set JWKS client (for testing)"""
        self._jwks_client = value
    
    @jwks_client.deleter
    def jwks_client(self):
        """Delete JWKS client (for testing)"""
        self._jwks_client = None
    
    @property
    def cognito_client(self):
        """Get or create Cognito client"""
        if self._cognito_client is None:
            self._cognito_client = boto3.client('cognito-idp', region_name=self.region)
        return self._cognito_client
    
    @cognito_client.setter
    def cognito_client(self, value):
        """Set Cognito client (for testing)"""
        self._cognito_client = value
    
    @cognito_client.deleter
    def cognito_client(self):
        """Delete Cognito client (for testing)"""
        self._cognito_client = None
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token and return decoded claims
        """
        try:
            # Get signing key
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            # Decode and verify token
            decoded_token = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"
            )
            
            # Verify token type
            if decoded_token.get('token_use') != 'access':
                raise AuthenticationError("Invalid token type")
            
            # Verify expiration
            exp = decoded_token.get('exp')
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                raise AuthenticationError("Token has expired")
            
            logger.info(f"Token verified successfully for user: {decoded_token.get('username')}")
            return decoded_token
            
        except ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except InvalidSignatureError:
            raise AuthenticationError("Invalid token signature")
        except InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise AuthenticationError("Token verification failed")
    
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
                raise AuthenticationError("Invalid or expired access token")
            else:
                logger.error(f"Cognito API error: {error_code}")
                raise ExternalServiceError("Cognito", f"Failed to get user info: {error_code}")
        except BotoCoreError as e:
            logger.error(f"AWS SDK error: {str(e)}")
            raise ExternalServiceError("AWS", "Failed to connect to Cognito service")
    
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
                raise AuthenticationError("Invalid or expired refresh token")
            else:
                logger.error(f"Cognito API error: {error_code}")
                raise ExternalServiceError("Cognito", f"Failed to refresh token: {error_code}")
        except BotoCoreError as e:
            logger.error(f"AWS SDK error: {str(e)}")
            raise ExternalServiceError("AWS", "Failed to connect to Cognito service")
    
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
    Extract JWT token from Authorization header
    """
    if not authorization_header:
        raise AuthenticationError("Authorization header is missing")
    
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise AuthenticationError("Invalid authorization header format")
    
    return parts[1]


def get_user_from_token(token: str) -> Dict[str, Any]:
    """
    Get user information from JWT token
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
        logger.error(f"Failed to get user from token: {str(e)}")
        raise AuthenticationError("Failed to extract user information from token")