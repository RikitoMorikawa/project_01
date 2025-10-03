"""
セキュリティインシデント管理サービス

データ漏洩・セキュリティ事故の検知、記録、対応を管理する
GDPR および個人情報保護法に準拠したインシデント管理機能
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
import logging
import json

from ..utils.audit_logging import AuditLogger, AuditAction, DataCategory
from ..utils.notifications import send_critical_alert, send_business_notification

logger = logging.getLogger(__name__)


class IncidentType(Enum):
    """インシデント種別"""
    DATA_BREACH = "data_breach"                    # データ漏洩
    UNAUTHORIZED_ACCESS = "unauthorized_access"    # 不正アクセス
    SYSTEM_COMPROMISE = "system_compromise"        # システム侵害
    OTHER = "other"                               # その他


class IncidentSeverity(Enum):
    """インシデント重要度"""
    LOW = "low"          # 低
    MEDIUM = "medium"    # 中
    HIGH = "high"        # 高
    CRITICAL = "critical" # 緊急


class IncidentStatus(Enum):
    """インシデント対応状況"""
    DETECTED = "detected"           # 検知
    INVESTIGATING = "investigating" # 調査中
    CONTAINED = "contained"         # 封じ込め完了
    RESOLVED = "resolved"          # 解決済み


class SecurityIncidentManager:
    """セキュリティインシデント管理クラス
    
    セキュリティインシデントの検知、記録、対応管理を提供
    """
    
    def __init__(self, db_connection):
        """インシデント管理クラスの初期化
        
        Args:
            db_connection: データベース接続オブジェクト
        """
        self.db = db_connection
        self.audit_logger = AuditLogger(db_connection)
    
    async def create_incident(
        self,
        incident_type: IncidentType,
        severity: IncidentSeverity,
        title: str,
        description: str,
        affected_users_count: int = 0,
        affected_data_types: Optional[List[str]] = None,
        detection_source: str = "system",
        additional_details: Optional[Dict[str, Any]] = None
    ) -> int:
        """セキュリティインシデントの作成
        
        Args:
            incident_type: インシデント種別
            severity: 重要度
            title: インシデントタイトル
            description: 詳細説明
            affected_users_count: 影響を受けたユーザー数
            affected_data_types: 影響を受けたデータの種類
            detection_source: 検知元
            additional_details: 追加詳細情報
            
        Returns:
            int: 作成されたインシデントID
        """
        try:
            # インシデント記録の作成
            cursor = await self.db.execute("""
                INSERT INTO security_incidents (
                    incident_type, severity, title, description,
                    affected_users_count, affected_data_types,
                    detection_date, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                incident_type.value,
                severity.value,
                title,
                description,
                affected_users_count,
                json.dumps(affected_data_types or [], ensure_ascii=False),
                datetime.utcnow(),
                IncidentStatus.DETECTED.value
            ))
            
            incident_id = cursor.lastrowid
            
            # 監査ログの記録
            await self.audit_logger.log_data_access(
                user_id=None,  # システム検知
                action=AuditAction.CREATE,
                data_category=DataCategory.SYSTEM_DATA,
                details={
                    "incident_id": incident_id,
                    "incident_type": incident_type.value,
                    "severity": severity.value,
                    "detection_source": detection_source,
                    "affected_users_count": affected_users_count,
                    "additional_details": additional_details
                }
            )
            
            # 重要度に応じた通知送信
            await self._send_incident_notification(
                incident_id, incident_type, severity, title, description
            )
            
            # GDPR 報告要件の確認
            if self._requires_gdpr_notification(incident_type, severity, affected_users_count):
                await self._schedule_gdpr_notification(incident_id)
            
            logger.info(f"セキュリティインシデントを作成しました (ID: {incident_id}, 重要度: {severity.value})")
            return incident_id
            
        except Exception as e:
            logger.error(f"セキュリティインシデントの作成に失敗しました: {e}")
            raise ValueError(f"インシデント作成に失敗しました: {str(e)}")
    
    async def update_incident_status(
        self,
        incident_id: int,
        new_status: IncidentStatus,
        response_actions: Optional[str] = None,
        resolver_user_id: Optional[int] = None
    ) -> bool:
        """インシデント状況の更新
        
        Args:
            incident_id: インシデントID
            new_status: 新しい状況
            response_actions: 対応措置の内容
            resolver_user_id: 対応者のユーザーID
            
        Returns:
            bool: 更新成功の場合 True
        """
        try:
            # 現在のインシデント情報を取得
            cursor = await self.db.execute(
                "SELECT * FROM security_incidents WHERE id = %s",
                (incident_id,)
            )
            incident = await cursor.fetchone()
            
            if not incident:
                raise ValueError("指定されたインシデントが見つかりません")
            
            # ステータス更新
            update_fields = ["status = %s", "updated_at = %s"]
            update_values = [new_status.value, datetime.utcnow()]
            
            if response_actions:
                update_fields.append("response_actions = %s")
                update_values.append(response_actions)
            
            if new_status == IncidentStatus.RESOLVED:
                update_fields.append("resolution_date = %s")
                update_values.append(datetime.utcnow())
            
            update_values.append(incident_id)
            
            await self.db.execute(f"""
                UPDATE security_incidents 
                SET {', '.join(update_fields)}
                WHERE id = %s
            """, update_values)
            
            # 監査ログの記録
            await self.audit_logger.log_data_access(
                user_id=resolver_user_id,
                action=AuditAction.UPDATE,
                data_category=DataCategory.SYSTEM_DATA,
                details={
                    "incident_id": incident_id,
                    "old_status": incident["status"],
                    "new_status": new_status.value,
                    "response_actions": response_actions
                }
            )
            
            # 解決通知
            if new_status == IncidentStatus.RESOLVED:
                await self._send_resolution_notification(incident_id, incident)
            
            logger.info(f"インシデント状況を更新しました (ID: {incident_id}, 状況: {new_status.value})")
            return True
            
        except Exception as e:
            logger.error(f"インシデント状況の更新に失敗しました (ID: {incident_id}): {e}")
            return False
    
    async def get_incident_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """インシデントサマリーの取得
        
        Args:
            start_date: 開始日時
            end_date: 終了日時
            
        Returns:
            Dict[str, Any]: インシデントサマリー
        """
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # 期間内のインシデント統計
            cursor = await self.db.execute("""
                SELECT 
                    COUNT(*) as total_incidents,
                    SUM(CASE WHEN status != 'resolved' THEN 1 ELSE 0 END) as open_incidents,
                    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical_incidents,
                    SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high_incidents,
                    SUM(affected_users_count) as total_affected_users
                FROM security_incidents 
                WHERE detection_date BETWEEN %s AND %s
            """, (start_date, end_date))
            
            summary_stats = await cursor.fetchone()
            
            # インシデント種別統計
            cursor = await self.db.execute("""
                SELECT incident_type, COUNT(*) as count
                FROM security_incidents 
                WHERE detection_date BETWEEN %s AND %s
                GROUP BY incident_type
                ORDER BY count DESC
            """, (start_date, end_date))
            
            type_stats = await cursor.fetchall()
            
            # 月別統計
            cursor = await self.db.execute("""
                SELECT 
                    DATE_FORMAT(detection_date, '%Y-%m') as month,
                    COUNT(*) as count
                FROM security_incidents 
                WHERE detection_date BETWEEN %s AND %s
                GROUP BY DATE_FORMAT(detection_date, '%Y-%m')
                ORDER BY month DESC
            """, (start_date, end_date))
            
            monthly_stats = await cursor.fetchall()
            
            # 平均解決時間
            cursor = await self.db.execute("""
                SELECT 
                    AVG(TIMESTAMPDIFF(HOUR, detection_date, resolution_date)) as avg_resolution_hours
                FROM security_incidents 
                WHERE detection_date BETWEEN %s AND %s
                AND resolution_date IS NOT NULL
            """, (start_date, end_date))
            
            resolution_time = await cursor.fetchone()
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "summary": dict(summary_stats) if summary_stats else {},
                "incident_types": type_stats,
                "monthly_trends": monthly_stats,
                "average_resolution_hours": resolution_time["avg_resolution_hours"] if resolution_time else None
            }
            
        except Exception as e:
            logger.error(f"インシデントサマリーの取得に失敗しました: {e}")
            return {
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "error": str(e)
            }
    
    async def detect_suspicious_activity(self) -> List[Dict[str, Any]]:
        """疑わしい活動の検知
        
        Returns:
            List[Dict[str, Any]]: 検知された疑わしい活動のリスト
        """
        suspicious_activities = []
        
        try:
            # 短時間での大量アクセス検知
            cursor = await self.db.execute("""
                SELECT 
                    user_id,
                    ip_address,
                    COUNT(*) as access_count,
                    MIN(created_at) as first_access,
                    MAX(created_at) as last_access
                FROM audit_logs 
                WHERE created_at >= %s
                AND user_id IS NOT NULL
                GROUP BY user_id, ip_address
                HAVING COUNT(*) > 100
                ORDER BY access_count DESC
            """, (datetime.utcnow() - timedelta(hours=1),))
            
            high_volume_access = await cursor.fetchall()
            
            for access in high_volume_access:
                suspicious_activities.append({
                    "type": "high_volume_access",
                    "severity": "medium",
                    "description": f"ユーザー {access['user_id']} が1時間で {access['access_count']} 回のアクセス",
                    "details": dict(access)
                })
            
            # 複数IPからの同時アクセス検知
            cursor = await self.db.execute("""
                SELECT 
                    user_id,
                    COUNT(DISTINCT ip_address) as ip_count,
                    GROUP_CONCAT(DISTINCT ip_address) as ip_addresses
                FROM audit_logs 
                WHERE created_at >= %s
                AND user_id IS NOT NULL
                GROUP BY user_id
                HAVING COUNT(DISTINCT ip_address) > 3
            """, (datetime.utcnow() - timedelta(minutes=30),))
            
            multi_ip_access = await cursor.fetchall()
            
            for access in multi_ip_access:
                suspicious_activities.append({
                    "type": "multi_ip_access",
                    "severity": "high",
                    "description": f"ユーザー {access['user_id']} が30分間で {access['ip_count']} 個のIPからアクセス",
                    "details": dict(access)
                })
            
            # 失敗したアクセス試行の検知
            cursor = await self.db.execute("""
                SELECT 
                    ip_address,
                    COUNT(*) as failed_attempts,
                    MIN(created_at) as first_attempt,
                    MAX(created_at) as last_attempt
                FROM audit_logs 
                WHERE created_at >= %s
                AND action = 'access_denied'
                GROUP BY ip_address
                HAVING COUNT(*) > 10
                ORDER BY failed_attempts DESC
            """, (datetime.utcnow() - timedelta(hours=1),))
            
            failed_attempts = await cursor.fetchall()
            
            for attempt in failed_attempts:
                suspicious_activities.append({
                    "type": "repeated_failed_access",
                    "severity": "high",
                    "description": f"IP {attempt['ip_address']} から1時間で {attempt['failed_attempts']} 回の失敗したアクセス試行",
                    "details": dict(attempt)
                })
            
            return suspicious_activities
            
        except Exception as e:
            logger.error(f"疑わしい活動の検知に失敗しました: {e}")
            return []
    
    async def _send_incident_notification(
        self,
        incident_id: int,
        incident_type: IncidentType,
        severity: IncidentSeverity,
        title: str,
        description: str
    ):
        """インシデント通知の送信
        
        Args:
            incident_id: インシデントID
            incident_type: インシデント種別
            severity: 重要度
            title: タイトル
            description: 説明
        """
        try:
            notification_data = {
                "incident_id": incident_id,
                "incident_type": incident_type.value,
                "severity": severity.value,
                "title": title,
                "description": description,
                "detection_time": datetime.utcnow().isoformat()
            }
            
            if severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
                # 緊急アラート送信
                send_critical_alert(
                    "security_incident",
                    f"セキュリティインシデント検知: {title}",
                    notification_data
                )
            else:
                # 通常の業務通知
                send_business_notification(
                    "security_incident",
                    f"セキュリティインシデント: {title}",
                    notification_data
                )
                
        except Exception as e:
            logger.error(f"インシデント通知の送信に失敗しました: {e}")
    
    async def _send_resolution_notification(self, incident_id: int, incident: Dict[str, Any]):
        """インシデント解決通知の送信
        
        Args:
            incident_id: インシデントID
            incident: インシデント情報
        """
        try:
            resolution_time = datetime.utcnow() - incident["detection_date"]
            
            notification_data = {
                "incident_id": incident_id,
                "title": incident["title"],
                "resolution_time_hours": resolution_time.total_seconds() / 3600,
                "resolution_date": datetime.utcnow().isoformat()
            }
            
            send_business_notification(
                "incident_resolved",
                f"セキュリティインシデント解決: {incident['title']}",
                notification_data
            )
            
        except Exception as e:
            logger.error(f"解決通知の送信に失敗しました: {e}")
    
    def _requires_gdpr_notification(
        self,
        incident_type: IncidentType,
        severity: IncidentSeverity,
        affected_users_count: int
    ) -> bool:
        """GDPR 報告要件の確認
        
        Args:
            incident_type: インシデント種別
            severity: 重要度
            affected_users_count: 影響ユーザー数
            
        Returns:
            bool: GDPR 報告が必要な場合 True
        """
        # データ漏洩で高リスクの場合は72時間以内の報告が必要
        if incident_type == IncidentType.DATA_BREACH:
            if severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]:
                return True
            if affected_users_count > 100:  # 閾値は組織のポリシーに応じて調整
                return True
        
        return False
    
    async def _schedule_gdpr_notification(self, incident_id: int):
        """GDPR 報告のスケジューリング
        
        Args:
            incident_id: インシデントID
        """
        try:
            # GDPR 報告フラグの設定
            await self.db.execute("""
                UPDATE security_incidents 
                SET reported_to_authority = %s, authority_report_date = %s
                WHERE id = %s
            """, (True, datetime.utcnow(), incident_id))
            
            # 緊急通知（72時間ルール）
            send_critical_alert(
                "gdpr_notification_required",
                f"GDPR 報告要件: インシデント {incident_id} は72時間以内の監督機関報告が必要です",
                {"incident_id": incident_id, "deadline": (datetime.utcnow() + timedelta(hours=72)).isoformat()}
            )
            
        except Exception as e:
            logger.error(f"GDPR 報告スケジューリングに失敗しました: {e}")


# 便利関数
async def detect_and_create_incident(
    db_connection,
    incident_type: IncidentType,
    title: str,
    description: str,
    severity: IncidentSeverity = IncidentSeverity.MEDIUM,
    **kwargs
) -> int:
    """インシデント検知・作成の便利関数
    
    Args:
        db_connection: データベース接続
        incident_type: インシデント種別
        title: タイトル
        description: 説明
        severity: 重要度
        **kwargs: その他のパラメータ
        
    Returns:
        int: 作成されたインシデントID
    """
    incident_manager = SecurityIncidentManager(db_connection)
    return await incident_manager.create_incident(
        incident_type=incident_type,
        severity=severity,
        title=title,
        description=description,
        **kwargs
    )