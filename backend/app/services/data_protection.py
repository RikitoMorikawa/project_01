"""
データ保護サービス

個人情報保護・プライバシー機能のビジネスロジックを提供する
GDPR および個人情報保護法に準拠したデータ保護機能
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from ..utils.encryption import get_encryption_instance
from ..utils.data_retention import DataRetentionManager, UserDataDeletionRequest, DataAnonymizationLevel
from ..utils.audit_logging import AuditLogger, AuditAction, DataCategory

logger = logging.getLogger(__name__)


class DataProtectionService:
    """データ保護サービスクラス
    
    個人情報保護・プライバシー機能の統合サービス
    """
    
    def __init__(self, db_connection):
        """データ保護サービスの初期化
        
        Args:
            db_connection: データベース接続オブジェクト
        """
        self.db = db_connection
        self.encryption = get_encryption_instance()
        self.retention_manager = DataRetentionManager(db_connection)
        self.deletion_manager = UserDataDeletionRequest(db_connection)
        self.audit_logger = AuditLogger(db_connection)
    
    async def encrypt_user_profile_data(
        self, 
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ユーザープロファイルデータの暗号化
        
        Args:
            profile_data: プロファイルデータ
            
        Returns:
            Dict[str, Any]: 暗号化されたプロファイルデータ
        """
        try:
            encrypted_data = profile_data.copy()
            
            # 個人情報フィールドの暗号化
            sensitive_fields = ['first_name', 'last_name', 'bio']
            
            for field in sensitive_fields:
                if field in encrypted_data and encrypted_data[field]:
                    encrypted_data[field] = self.encryption.encrypt_personal_data(
                        encrypted_data[field]
                    )
            
            logger.info("ユーザープロファイルデータを暗号化しました")
            return encrypted_data
            
        except Exception as e:
            logger.error(f"プロファイルデータの暗号化に失敗しました: {e}")
            raise ValueError("プロファイルデータの暗号化に失敗しました")
    
    async def decrypt_user_profile_data(
        self, 
        encrypted_profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ユーザープロファイルデータの復号化
        
        Args:
            encrypted_profile_data: 暗号化されたプロファイルデータ
            
        Returns:
            Dict[str, Any]: 復号化されたプロファイルデータ
        """
        try:
            decrypted_data = encrypted_profile_data.copy()
            
            # 個人情報フィールドの復号化
            sensitive_fields = ['first_name', 'last_name', 'bio']
            
            for field in sensitive_fields:
                if field in decrypted_data and decrypted_data[field]:
                    decrypted_data[field] = self.encryption.decrypt_personal_data(
                        decrypted_data[field]
                    )
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"プロファイルデータの復号化に失敗しました: {e}")
            raise ValueError("プロファイルデータの復号化に失敗しました")
    
    async def create_user_consent_record(
        self,
        user_id: int,
        consent_type: str,
        consent_version: str,
        consented: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """ユーザー同意記録の作成
        
        Args:
            user_id: ユーザーID
            consent_type: 同意種別
            consent_version: 同意したポリシーバージョン
            consented: 同意フラグ
            ip_address: IPアドレス
            user_agent: ユーザーエージェント
            
        Returns:
            bool: 記録作成成功の場合 True
        """
        try:
            await self.db.execute("""
                INSERT INTO user_consents (
                    user_id, consent_type, consent_version, consented, 
                    ip_address, user_agent, consent_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, consent_type, consent_version, consented,
                ip_address, user_agent, datetime.utcnow()
            ))
            
            # 監査ログの記録
            await self.audit_logger.log_data_access(
                user_id=user_id,
                action=AuditAction.CREATE,
                data_category=DataCategory.PERSONAL_INFO,
                target_user_id=user_id,
                details={
                    "consent_type": consent_type,
                    "consent_version": consent_version,
                    "consented": consented
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"ユーザー同意記録を作成しました (user_id: {user_id}, type: {consent_type})")
            return True
            
        except Exception as e:
            logger.error(f"ユーザー同意記録の作成に失敗しました (user_id: {user_id}): {e}")
            return False
    
    async def get_user_consent_status(
        self, 
        user_id: int
    ) -> Dict[str, Any]:
        """ユーザーの同意状況取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            Dict[str, Any]: 同意状況
        """
        try:
            cursor = await self.db.execute("""
                SELECT 
                    consent_type,
                    consent_version,
                    consented,
                    consent_date,
                    withdrawn_at
                FROM user_consents 
                WHERE user_id = %s 
                AND withdrawn_at IS NULL
                ORDER BY consent_date DESC
            """, (user_id,))
            
            consents = await cursor.fetchall()
            
            # 同意種別ごとの最新状況を整理
            consent_status = {}
            for consent in consents:
                consent_type = consent['consent_type']
                if consent_type not in consent_status:
                    consent_status[consent_type] = {
                        'consented': consent['consented'],
                        'version': consent['consent_version'],
                        'date': consent['consent_date'].isoformat() if consent['consent_date'] else None
                    }
            
            return consent_status
            
        except Exception as e:
            logger.error(f"ユーザー同意状況の取得に失敗しました (user_id: {user_id}): {e}")
            return {}
    
    async def withdraw_user_consent(
        self,
        user_id: int,
        consent_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """ユーザー同意の撤回
        
        Args:
            user_id: ユーザーID
            consent_type: 同意種別
            ip_address: IPアドレス
            user_agent: ユーザーエージェント
            
        Returns:
            bool: 撤回成功の場合 True
        """
        try:
            # 既存の同意記録を撤回状態に更新
            await self.db.execute("""
                UPDATE user_consents 
                SET withdrawn_at = %s 
                WHERE user_id = %s 
                AND consent_type = %s 
                AND withdrawn_at IS NULL
            """, (datetime.utcnow(), user_id, consent_type))
            
            # 監査ログの記録
            await self.audit_logger.log_data_access(
                user_id=user_id,
                action=AuditAction.UPDATE,
                data_category=DataCategory.PERSONAL_INFO,
                target_user_id=user_id,
                details={
                    "action": "consent_withdrawal",
                    "consent_type": consent_type
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"ユーザー同意を撤回しました (user_id: {user_id}, type: {consent_type})")
            return True
            
        except Exception as e:
            logger.error(f"ユーザー同意の撤回に失敗しました (user_id: {user_id}): {e}")
            return False
    
    async def request_data_deletion(
        self,
        user_id: int,
        reason: str = "ユーザーからの削除要求"
    ) -> bool:
        """データ削除リクエストの作成
        
        Args:
            user_id: ユーザーID
            reason: 削除理由
            
        Returns:
            bool: リクエスト作成成功の場合 True
        """
        return await self.deletion_manager.create_deletion_request(user_id, reason)
    
    async def export_user_data(
        self,
        user_id: int,
        requesting_user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """ユーザーデータのエクスポート（データポータビリティ対応）
        
        Args:
            user_id: エクスポート対象ユーザーID
            requesting_user_id: リクエスト実行ユーザーID
            ip_address: IPアドレス
            user_agent: ユーザーエージェント
            
        Returns:
            Dict[str, Any]: エクスポートされたユーザーデータ
        """
        try:
            # ユーザー基本情報の取得
            cursor = await self.db.execute("""
                SELECT id, cognito_user_id, email, username, created_at, updated_at
                FROM users 
                WHERE id = %s AND deleted_at IS NULL
            """, (user_id,))
            user_data = await cursor.fetchone()
            
            if not user_data:
                raise ValueError("ユーザーが見つかりません")
            
            # プロファイル情報の取得
            cursor = await self.db.execute("""
                SELECT first_name, last_name, avatar_url, bio, created_at, updated_at
                FROM user_profiles 
                WHERE user_id = %s AND deleted_at IS NULL
            """, (user_id,))
            profile_data = await cursor.fetchone()
            
            # 暗号化されたプロファイルデータの復号化
            if profile_data:
                profile_data = await self.decrypt_user_profile_data(dict(profile_data))
            
            # 同意履歴の取得
            consent_status = await self.get_user_consent_status(user_id)
            
            # アクセス履歴の取得（直近100件）
            access_history = await self.audit_logger.get_user_access_history(
                target_user_id=user_id,
                limit=100
            )
            
            # エクスポートデータの構築
            export_data = {
                "export_info": {
                    "exported_at": datetime.utcnow().isoformat(),
                    "exported_by_user_id": requesting_user_id,
                    "data_format": "JSON"
                },
                "user_data": dict(user_data) if user_data else {},
                "profile_data": profile_data or {},
                "consent_history": consent_status,
                "access_history": access_history
            }
            
            # 監査ログの記録
            await self.audit_logger.log_data_access(
                user_id=requesting_user_id,
                action=AuditAction.EXPORT,
                data_category=DataCategory.PERSONAL_INFO,
                target_user_id=user_id,
                details={
                    "export_size": len(str(export_data)),
                    "exported_sections": list(export_data.keys())
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(f"ユーザーデータをエクスポートしました (user_id: {user_id})")
            return export_data
            
        except Exception as e:
            logger.error(f"ユーザーデータのエクスポートに失敗しました (user_id: {user_id}): {e}")
            raise ValueError(f"データエクスポートに失敗しました: {str(e)}")
    
    async def check_data_retention_compliance(self) -> Dict[str, Any]:
        """データ保持期間コンプライアンスチェック
        
        Returns:
            Dict[str, Any]: コンプライアンスチェック結果
        """
        try:
            # 期限切れデータの検索
            expired_users = await self.retention_manager.find_expired_user_data()
            
            # 削除待ちリクエストの確認
            cursor = await self.db.execute("""
                SELECT COUNT(*) as pending_count
                FROM data_deletion_requests 
                WHERE status = 'pending'
            """)
            pending_result = await cursor.fetchone()
            pending_deletions = pending_result['pending_count'] if pending_result else 0
            
            # 最近のセキュリティインシデント確認
            cursor = await self.db.execute("""
                SELECT COUNT(*) as recent_incidents
                FROM security_incidents 
                WHERE detection_date >= %s
                AND status != 'resolved'
            """, (datetime.utcnow() - timedelta(days=30),))
            incident_result = await cursor.fetchone()
            recent_incidents = incident_result['recent_incidents'] if incident_result else 0
            
            compliance_status = {
                "check_date": datetime.utcnow().isoformat(),
                "expired_data_count": len(expired_users),
                "pending_deletion_requests": pending_deletions,
                "recent_unresolved_incidents": recent_incidents,
                "compliance_issues": [],
                "recommendations": []
            }
            
            # コンプライアンス問題の特定
            if len(expired_users) > 0:
                compliance_status["compliance_issues"].append(
                    f"{len(expired_users)}件の期限切れユーザーデータが存在します"
                )
                compliance_status["recommendations"].append(
                    "期限切れデータの匿名化または削除を実行してください"
                )
            
            if pending_deletions > 0:
                compliance_status["compliance_issues"].append(
                    f"{pending_deletions}件の削除リクエストが未処理です"
                )
                compliance_status["recommendations"].append(
                    "削除リクエストの処理を実行してください"
                )
            
            if recent_incidents > 0:
                compliance_status["compliance_issues"].append(
                    f"{recent_incidents}件の未解決セキュリティインシデントがあります"
                )
                compliance_status["recommendations"].append(
                    "セキュリティインシデントの対応を完了してください"
                )
            
            return compliance_status
            
        except Exception as e:
            logger.error(f"データ保持期間コンプライアンスチェックに失敗しました: {e}")
            return {
                "check_date": datetime.utcnow().isoformat(),
                "error": str(e),
                "compliance_issues": ["コンプライアンスチェックの実行に失敗しました"],
                "recommendations": ["システム管理者に連絡してください"]
            }