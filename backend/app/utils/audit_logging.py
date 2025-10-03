"""
データアクセス監査ログユーティリティ

個人データへのアクセス・操作を記録し、監査証跡を提供する
GDPR および個人情報保護法に準拠した監査ログ機能
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class AuditAction(Enum):
    """監査対象アクション"""
    CREATE = "create"           # データ作成
    READ = "read"              # データ読み取り
    UPDATE = "update"          # データ更新
    DELETE = "delete"          # データ削除
    EXPORT = "export"          # データエクスポート
    LOGIN = "login"            # ログイン
    LOGOUT = "logout"          # ログアウト
    ACCESS_DENIED = "access_denied"  # アクセス拒否


class DataCategory(Enum):
    """データカテゴリ"""
    PERSONAL_INFO = "personal_info"      # 個人情報
    PROFILE_DATA = "profile_data"        # プロファイルデータ
    AUTH_DATA = "auth_data"              # 認証データ
    SYSTEM_DATA = "system_data"          # システムデータ


class AuditLogger:
    """監査ログ記録クラス
    
    個人データへのアクセス・操作を記録し、監査証跡を提供
    """
    
    def __init__(self, db_connection):
        """監査ログクラスの初期化
        
        Args:
            db_connection: データベース接続オブジェクト
        """
        self.db = db_connection
    
    async def log_data_access(
        self,
        user_id: Optional[int],
        action: AuditAction,
        data_category: DataCategory,
        target_user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """データアクセスログの記録
        
        Args:
            user_id: 操作実行ユーザーID
            action: 実行されたアクション
            data_category: データカテゴリ
            target_user_id: 操作対象ユーザーID
            details: 詳細情報
            ip_address: IPアドレス
            user_agent: ユーザーエージェント
            
        Returns:
            bool: ログ記録成功の場合 True
        """
        try:
            # 監査ログテーブルへの記録
            # CREATE TABLE audit_logs (
            #     id BIGINT PRIMARY KEY AUTO_INCREMENT,
            #     user_id BIGINT NULL,
            #     action VARCHAR(50) NOT NULL,
            #     data_category VARCHAR(50) NOT NULL,
            #     target_user_id BIGINT NULL,
            #     details JSON NULL,
            #     ip_address VARCHAR(45) NULL,
            #     user_agent TEXT NULL,
            #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            #     INDEX idx_user_id (user_id),
            #     INDEX idx_target_user_id (target_user_id),
            #     INDEX idx_action (action),
            #     INDEX idx_created_at (created_at)
            # );
            
            details_json = json.dumps(details, ensure_ascii=False) if details else None
            
            await self.db.execute("""
                INSERT INTO audit_logs (
                    user_id, action, data_category, target_user_id, 
                    details, ip_address, user_agent, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                action.value,
                data_category.value,
                target_user_id,
                details_json,
                ip_address,
                user_agent,
                datetime.utcnow()
            ))
            
            # 構造化ログとしても出力
            log_entry = {
                "event": "data_access",
                "user_id": user_id,
                "action": action.value,
                "data_category": data_category.value,
                "target_user_id": target_user_id,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"データアクセスログ記録: {json.dumps(log_entry, ensure_ascii=False)}")
            return True
            
        except Exception as e:
            logger.error(f"監査ログの記録に失敗しました: {e}")
            return False
    
    async def log_personal_data_access(
        self,
        user_id: int,
        target_user_id: int,
        action: AuditAction,
        accessed_fields: List[str],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """個人データアクセスログの記録
        
        Args:
            user_id: 操作実行ユーザーID
            target_user_id: 操作対象ユーザーID
            action: 実行されたアクション
            accessed_fields: アクセスされたフィールドリスト
            ip_address: IPアドレス
            user_agent: ユーザーエージェント
            
        Returns:
            bool: ログ記録成功の場合 True
        """
        details = {
            "accessed_fields": accessed_fields,
            "field_count": len(accessed_fields)
        }
        
        return await self.log_data_access(
            user_id=user_id,
            action=action,
            data_category=DataCategory.PERSONAL_INFO,
            target_user_id=target_user_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def log_authentication_event(
        self,
        user_id: Optional[int],
        action: AuditAction,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> bool:
        """認証イベントログの記録
        
        Args:
            user_id: ユーザーID
            action: 認証アクション
            success: 認証成功フラグ
            ip_address: IPアドレス
            user_agent: ユーザーエージェント
            failure_reason: 失敗理由
            
        Returns:
            bool: ログ記録成功の場合 True
        """
        details = {
            "success": success,
            "failure_reason": failure_reason
        }
        
        return await self.log_data_access(
            user_id=user_id,
            action=action,
            data_category=DataCategory.AUTH_DATA,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def get_user_access_history(
        self,
        target_user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """ユーザーのアクセス履歴取得
        
        Args:
            target_user_id: 対象ユーザーID
            start_date: 開始日時
            end_date: 終了日時
            limit: 取得件数制限
            
        Returns:
            List[Dict[str, Any]]: アクセス履歴リスト
        """
        try:
            query = """
            SELECT 
                id,
                user_id,
                action,
                data_category,
                details,
                ip_address,
                user_agent,
                created_at
            FROM audit_logs 
            WHERE target_user_id = %s
            """
            params = [target_user_id]
            
            if start_date:
                query += " AND created_at >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND created_at <= %s"
                params.append(end_date)
            
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            
            cursor = await self.db.execute(query, params)
            results = await cursor.fetchall()
            
            # JSON フィールドをパース
            for result in results:
                if result.get('details'):
                    try:
                        result['details'] = json.loads(result['details'])
                    except json.JSONDecodeError:
                        result['details'] = {}
            
            return results
            
        except Exception as e:
            logger.error(f"アクセス履歴の取得に失敗しました (target_user_id: {target_user_id}): {e}")
            return []
    
    async def get_system_audit_summary(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """システム監査サマリーの取得
        
        Args:
            start_date: 開始日時
            end_date: 終了日時
            
        Returns:
            Dict[str, Any]: 監査サマリー
        """
        try:
            # アクション別統計
            cursor = await self.db.execute("""
                SELECT action, COUNT(*) as count
                FROM audit_logs 
                WHERE created_at BETWEEN %s AND %s
                GROUP BY action
                ORDER BY count DESC
            """, (start_date, end_date))
            action_stats = await cursor.fetchall()
            
            # データカテゴリ別統計
            cursor = await self.db.execute("""
                SELECT data_category, COUNT(*) as count
                FROM audit_logs 
                WHERE created_at BETWEEN %s AND %s
                GROUP BY data_category
                ORDER BY count DESC
            """, (start_date, end_date))
            category_stats = await cursor.fetchall()
            
            # 日別アクセス統計
            cursor = await self.db.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM audit_logs 
                WHERE created_at BETWEEN %s AND %s
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """, (start_date, end_date))
            daily_stats = await cursor.fetchall()
            
            # 総アクセス数
            cursor = await self.db.execute("""
                SELECT COUNT(*) as total_count
                FROM audit_logs 
                WHERE created_at BETWEEN %s AND %s
            """, (start_date, end_date))
            total_result = await cursor.fetchone()
            total_count = total_result['total_count'] if total_result else 0
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_access_count": total_count,
                "action_statistics": action_stats,
                "category_statistics": category_stats,
                "daily_statistics": daily_stats
            }
            
        except Exception as e:
            logger.error(f"システム監査サマリーの取得に失敗しました: {e}")
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_access_count": 0,
                "action_statistics": [],
                "category_statistics": [],
                "daily_statistics": [],
                "error": str(e)
            }


# 便利関数
async def log_user_data_read(
    db_connection,
    user_id: int,
    target_user_id: int,
    accessed_fields: List[str],
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> bool:
    """ユーザーデータ読み取りログ（便利関数）
    
    Args:
        db_connection: データベース接続
        user_id: 操作実行ユーザーID
        target_user_id: 操作対象ユーザーID
        accessed_fields: アクセスされたフィールド
        ip_address: IPアドレス
        user_agent: ユーザーエージェント
        
    Returns:
        bool: ログ記録成功の場合 True
    """
    audit_logger = AuditLogger(db_connection)
    return await audit_logger.log_personal_data_access(
        user_id=user_id,
        target_user_id=target_user_id,
        action=AuditAction.READ,
        accessed_fields=accessed_fields,
        ip_address=ip_address,
        user_agent=user_agent
    )


async def log_user_data_update(
    db_connection,
    user_id: int,
    target_user_id: int,
    updated_fields: List[str],
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> bool:
    """ユーザーデータ更新ログ（便利関数）
    
    Args:
        db_connection: データベース接続
        user_id: 操作実行ユーザーID
        target_user_id: 操作対象ユーザーID
        updated_fields: 更新されたフィールド
        ip_address: IPアドレス
        user_agent: ユーザーエージェント
        
    Returns:
        bool: ログ記録成功の場合 True
    """
    audit_logger = AuditLogger(db_connection)
    return await audit_logger.log_personal_data_access(
        user_id=user_id,
        target_user_id=target_user_id,
        action=AuditAction.UPDATE,
        accessed_fields=updated_fields,
        ip_address=ip_address,
        user_agent=user_agent
    )