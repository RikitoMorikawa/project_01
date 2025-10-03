"""
データ保持期間管理ユーティリティ

個人データの保持期間管理と自動削除機能を提供する
GDPR および個人情報保護法に準拠したデータライフサイクル管理
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DataRetentionPeriod(Enum):
    """データ保持期間の定義"""
    USER_PROFILE = 2555  # 7年（個人情報保護法の推奨期間）
    ACCESS_LOG = 365     # 1年
    AUDIT_LOG = 2555     # 7年
    SESSION_DATA = 30    # 30日
    TEMPORARY_DATA = 7   # 7日


class DataAnonymizationLevel(Enum):
    """データ匿名化レベル"""
    SOFT_DELETE = "soft_delete"      # 論理削除（削除フラグ）
    ANONYMIZE = "anonymize"          # 匿名化（個人識別情報を除去）
    HARD_DELETE = "hard_delete"      # 物理削除（完全削除）


class DataRetentionManager:
    """データ保持期間管理クラス
    
    個人データの保持期間管理と削除・匿名化処理を提供
    """
    
    def __init__(self, db_connection):
        """データ保持期間管理クラスの初期化
        
        Args:
            db_connection: データベース接続オブジェクト
        """
        self.db = db_connection
    
    def calculate_retention_expiry(
        self, 
        created_at: datetime, 
        retention_period: DataRetentionPeriod
    ) -> datetime:
        """データ保持期限の計算
        
        Args:
            created_at: データ作成日時
            retention_period: 保持期間
            
        Returns:
            datetime: 保持期限日時
        """
        return created_at + timedelta(days=retention_period.value)
    
    def is_data_expired(
        self, 
        created_at: datetime, 
        retention_period: DataRetentionPeriod
    ) -> bool:
        """データ保持期限の確認
        
        Args:
            created_at: データ作成日時
            retention_period: 保持期間
            
        Returns:
            bool: 期限切れの場合 True
        """
        expiry_date = self.calculate_retention_expiry(created_at, retention_period)
        return datetime.utcnow() > expiry_date
    
    async def find_expired_user_data(self) -> List[Dict[str, Any]]:
        """期限切れユーザーデータの検索
        
        Returns:
            List[Dict[str, Any]]: 期限切れユーザーデータのリスト
        """
        try:
            # 7年以上前に作成されたユーザーデータを検索
            cutoff_date = datetime.utcnow() - timedelta(days=DataRetentionPeriod.USER_PROFILE.value)
            
            query = """
            SELECT 
                u.id,
                u.cognito_user_id,
                u.email,
                u.username,
                u.created_at,
                up.id as profile_id
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE u.created_at < %s
            AND u.deleted_at IS NULL
            """
            
            cursor = await self.db.execute(query, (cutoff_date,))
            return await cursor.fetchall()
            
        except Exception as e:
            logger.error(f"期限切れユーザーデータの検索に失敗しました: {e}")
            return []
    
    async def anonymize_user_data(
        self, 
        user_id: int, 
        anonymization_level: DataAnonymizationLevel = DataAnonymizationLevel.ANONYMIZE
    ) -> bool:
        """ユーザーデータの匿名化
        
        Args:
            user_id: ユーザーID
            anonymization_level: 匿名化レベル
            
        Returns:
            bool: 匿名化成功の場合 True
        """
        try:
            if anonymization_level == DataAnonymizationLevel.SOFT_DELETE:
                return await self._soft_delete_user(user_id)
            elif anonymization_level == DataAnonymizationLevel.ANONYMIZE:
                return await self._anonymize_user(user_id)
            elif anonymization_level == DataAnonymizationLevel.HARD_DELETE:
                return await self._hard_delete_user(user_id)
            else:
                logger.error(f"不正な匿名化レベル: {anonymization_level}")
                return False
                
        except Exception as e:
            logger.error(f"ユーザーデータの匿名化に失敗しました (user_id: {user_id}): {e}")
            return False
    
    async def _soft_delete_user(self, user_id: int) -> bool:
        """ユーザーデータの論理削除
        
        Args:
            user_id: ユーザーID
            
        Returns:
            bool: 削除成功の場合 True
        """
        try:
            # deleted_at カラムを追加する必要がある場合のマイグレーション
            # ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP NULL;
            # ALTER TABLE user_profiles ADD COLUMN deleted_at TIMESTAMP NULL;
            
            await self.db.execute(
                "UPDATE users SET deleted_at = %s WHERE id = %s",
                (datetime.utcnow(), user_id)
            )
            
            await self.db.execute(
                "UPDATE user_profiles SET deleted_at = %s WHERE user_id = %s",
                (datetime.utcnow(), user_id)
            )
            
            logger.info(f"ユーザーデータを論理削除しました (user_id: {user_id})")
            return True
            
        except Exception as e:
            logger.error(f"ユーザーデータの論理削除に失敗しました (user_id: {user_id}): {e}")
            return False
    
    async def _anonymize_user(self, user_id: int) -> bool:
        """ユーザーデータの匿名化
        
        Args:
            user_id: ユーザーID
            
        Returns:
            bool: 匿名化成功の場合 True
        """
        try:
            # 匿名化されたデータで更新
            anonymous_timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            
            await self.db.execute("""
                UPDATE users 
                SET 
                    email = %s,
                    username = %s,
                    cognito_user_id = %s,
                    updated_at = %s
                WHERE id = %s
            """, (
                f"anonymized_{anonymous_timestamp}@deleted.local",
                f"匿名化ユーザー_{anonymous_timestamp}",
                f"anonymized_{anonymous_timestamp}",
                datetime.utcnow(),
                user_id
            ))
            
            await self.db.execute("""
                UPDATE user_profiles 
                SET 
                    first_name = %s,
                    last_name = %s,
                    bio = %s,
                    avatar_url = NULL,
                    updated_at = %s
                WHERE user_id = %s
            """, (
                "匿名化",
                "ユーザー",
                "このユーザーのデータは匿名化されました",
                datetime.utcnow(),
                user_id
            ))
            
            logger.info(f"ユーザーデータを匿名化しました (user_id: {user_id})")
            return True
            
        except Exception as e:
            logger.error(f"ユーザーデータの匿名化に失敗しました (user_id: {user_id}): {e}")
            return False
    
    async def _hard_delete_user(self, user_id: int) -> bool:
        """ユーザーデータの物理削除
        
        Args:
            user_id: ユーザーID
            
        Returns:
            bool: 削除成功の場合 True
        """
        try:
            # 外部キー制約により、user_profiles が先に削除される
            await self.db.execute("DELETE FROM user_profiles WHERE user_id = %s", (user_id,))
            await self.db.execute("DELETE FROM users WHERE id = %s", (user_id,))
            
            logger.info(f"ユーザーデータを物理削除しました (user_id: {user_id})")
            return True
            
        except Exception as e:
            logger.error(f"ユーザーデータの物理削除に失敗しました (user_id: {user_id}): {e}")
            return False
    
    async def cleanup_expired_data(self) -> Dict[str, int]:
        """期限切れデータの一括クリーンアップ
        
        Returns:
            Dict[str, int]: クリーンアップ結果の統計
        """
        results = {
            "processed_users": 0,
            "anonymized_users": 0,
            "failed_users": 0
        }
        
        try:
            expired_users = await self.find_expired_user_data()
            results["processed_users"] = len(expired_users)
            
            for user_data in expired_users:
                user_id = user_data["id"]
                success = await self.anonymize_user_data(
                    user_id, 
                    DataAnonymizationLevel.ANONYMIZE
                )
                
                if success:
                    results["anonymized_users"] += 1
                else:
                    results["failed_users"] += 1
            
            logger.info(f"データクリーンアップ完了: {results}")
            return results
            
        except Exception as e:
            logger.error(f"データクリーンアップに失敗しました: {e}")
            results["failed_users"] = results["processed_users"]
            return results


class UserDataDeletionRequest:
    """ユーザーデータ削除リクエスト管理
    
    GDPR の「忘れられる権利」に対応したデータ削除リクエスト管理
    """
    
    def __init__(self, db_connection):
        """削除リクエスト管理クラスの初期化
        
        Args:
            db_connection: データベース接続オブジェクト
        """
        self.db = db_connection
        self.retention_manager = DataRetentionManager(db_connection)
    
    async def create_deletion_request(
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
        try:
            # データ削除リクエストテーブルに記録
            # CREATE TABLE data_deletion_requests (
            #     id BIGINT PRIMARY KEY AUTO_INCREMENT,
            #     user_id BIGINT NOT NULL,
            #     reason TEXT,
            #     status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
            #     requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            #     processed_at TIMESTAMP NULL,
            #     FOREIGN KEY (user_id) REFERENCES users(id)
            # );
            
            await self.db.execute("""
                INSERT INTO data_deletion_requests (user_id, reason, status)
                VALUES (%s, %s, 'pending')
            """, (user_id, reason))
            
            logger.info(f"データ削除リクエストを作成しました (user_id: {user_id})")
            return True
            
        except Exception as e:
            logger.error(f"データ削除リクエストの作成に失敗しました (user_id: {user_id}): {e}")
            return False
    
    async def process_deletion_request(self, request_id: int) -> bool:
        """データ削除リクエストの処理
        
        Args:
            request_id: 削除リクエストID
            
        Returns:
            bool: 処理成功の場合 True
        """
        try:
            # リクエスト情報の取得
            cursor = await self.db.execute(
                "SELECT user_id FROM data_deletion_requests WHERE id = %s AND status = 'pending'",
                (request_id,)
            )
            request_data = await cursor.fetchone()
            
            if not request_data:
                logger.warning(f"処理対象の削除リクエストが見つかりません (request_id: {request_id})")
                return False
            
            user_id = request_data["user_id"]
            
            # ステータスを処理中に更新
            await self.db.execute(
                "UPDATE data_deletion_requests SET status = 'processing' WHERE id = %s",
                (request_id,)
            )
            
            # ユーザーデータの削除実行
            success = await self.retention_manager.anonymize_user_data(
                user_id, 
                DataAnonymizationLevel.HARD_DELETE
            )
            
            # 処理結果の更新
            status = 'completed' if success else 'failed'
            await self.db.execute("""
                UPDATE data_deletion_requests 
                SET status = %s, processed_at = %s 
                WHERE id = %s
            """, (status, datetime.utcnow(), request_id))
            
            logger.info(f"データ削除リクエストを処理しました (request_id: {request_id}, success: {success})")
            return success
            
        except Exception as e:
            logger.error(f"データ削除リクエストの処理に失敗しました (request_id: {request_id}): {e}")
            
            # エラー時のステータス更新
            await self.db.execute(
                "UPDATE data_deletion_requests SET status = 'failed' WHERE id = %s",
                (request_id,)
            )
            return False