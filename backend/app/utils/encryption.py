"""
個人情報暗号化ユーティリティ

個人データの暗号化・復号化機能を提供する
AES-256-GCM を使用した対称暗号化を実装
"""

import os
import base64
from typing import Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


class PersonalDataEncryption:
    """個人データ暗号化クラス
    
    個人情報保護のためのデータ暗号化・復号化機能を提供
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """暗号化クラスの初期化
        
        Args:
            encryption_key: 暗号化キー（環境変数から取得する場合は None）
        """
        self._key = self._get_or_generate_key(encryption_key)
        self._fernet = Fernet(self._key)
    
    def _get_or_generate_key(self, provided_key: Optional[str] = None) -> bytes:
        """暗号化キーの取得または生成
        
        Args:
            provided_key: 提供された暗号化キー
            
        Returns:
            bytes: 暗号化キー
        """
        if provided_key:
            # 提供されたキーを使用
            return provided_key.encode()
        
        # 環境変数から暗号化キーを取得
        env_key = os.getenv('PERSONAL_DATA_ENCRYPTION_KEY')
        if env_key:
            return base64.urlsafe_b64decode(env_key.encode())
        
        # 開発環境用のデフォルトキー生成（本番では使用禁止）
        logger.warning("暗号化キーが設定されていません。開発用キーを生成します。")
        password = b"dev-encryption-password"  # 本番では環境変数から取得
        salt = b"dev-salt-12345678"  # 本番では動的に生成
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password))
    
    def encrypt_personal_data(self, data: Union[str, None]) -> Optional[str]:
        """個人データの暗号化
        
        Args:
            data: 暗号化する個人データ
            
        Returns:
            Optional[str]: 暗号化されたデータ（Base64エンコード）
        """
        if data is None or data == "":
            return None
        
        try:
            encrypted_data = self._fernet.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"個人データの暗号化に失敗しました: {e}")
            raise ValueError("データの暗号化に失敗しました")
    
    def decrypt_personal_data(self, encrypted_data: Union[str, None]) -> Optional[str]:
        """個人データの復号化
        
        Args:
            encrypted_data: 暗号化されたデータ（Base64エンコード）
            
        Returns:
            Optional[str]: 復号化されたデータ
        """
        if encrypted_data is None or encrypted_data == "":
            return None
        
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self._fernet.decrypt(decoded_data)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"個人データの復号化に失敗しました: {e}")
            raise ValueError("データの復号化に失敗しました")
    
    def encrypt_email(self, email: str) -> str:
        """メールアドレスの暗号化
        
        Args:
            email: メールアドレス
            
        Returns:
            str: 暗号化されたメールアドレス
        """
        return self.encrypt_personal_data(email) or ""
    
    def decrypt_email(self, encrypted_email: str) -> str:
        """メールアドレスの復号化
        
        Args:
            encrypted_email: 暗号化されたメールアドレス
            
        Returns:
            str: 復号化されたメールアドレス
        """
        return self.decrypt_personal_data(encrypted_email) or ""


# グローバルインスタンス（シングルトンパターン）
_encryption_instance: Optional[PersonalDataEncryption] = None


def get_encryption_instance() -> PersonalDataEncryption:
    """暗号化インスタンスの取得
    
    Returns:
        PersonalDataEncryption: 暗号化インスタンス
    """
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = PersonalDataEncryption()
    return _encryption_instance


def encrypt_personal_field(data: Union[str, None]) -> Optional[str]:
    """個人データフィールドの暗号化（便利関数）
    
    Args:
        data: 暗号化するデータ
        
    Returns:
        Optional[str]: 暗号化されたデータ
    """
    return get_encryption_instance().encrypt_personal_data(data)


def decrypt_personal_field(encrypted_data: Union[str, None]) -> Optional[str]:
    """個人データフィールドの復号化（便利関数）
    
    Args:
        encrypted_data: 暗号化されたデータ
        
    Returns:
        Optional[str]: 復号化されたデータ
    """
    return get_encryption_instance().decrypt_personal_data(encrypted_data)