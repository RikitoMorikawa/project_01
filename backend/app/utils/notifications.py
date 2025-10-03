"""
エラー通知とアラート機能

システムエラーやビジネスイベントの通知を管理します。
"""

import boto3
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from app.config import settings

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """アラートの重要度レベル"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """通知チャネル"""
    EMAIL = "email"
    SLACK = "slack"
    SNS = "sns"
    PAGERDUTY = "pagerduty"


class NotificationManager:
    """通知管理クラス"""
    
    def __init__(self):
        """通知管理クラスを初期化"""
        self.sns_client = None
        self.cloudwatch_client = None
        
        try:
            self.sns_client = boto3.client('sns', region_name=settings.aws_region)
            self.cloudwatch_client = boto3.client('cloudwatch', region_name=settings.aws_region)
        except Exception as e:
            logger.warning(f"AWS クライアント初期化エラー: {str(e)}")
    
    def send_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        channels: Optional[List[NotificationChannel]] = None
    ) -> bool:
        """
        アラートを送信
        
        Args:
            title: アラートタイトル
            message: アラートメッセージ
            severity: 重要度レベル
            details: 追加詳細情報
            channels: 送信チャネル（指定なしの場合はデフォルト）
        
        Returns:
            bool: 送信成功フラグ
        """
        try:
            # デフォルトチャネルを設定
            if channels is None:
                channels = [NotificationChannel.SNS]
                if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
                    channels.append(NotificationChannel.SLACK)
            
            # アラートデータを構築
            alert_data = {
                "title": title,
                "message": message,
                "severity": severity.value,
                "timestamp": datetime.utcnow().isoformat(),
                "environment": settings.environment,
                "service": "CSR-Lambda-API",
                "details": details or {}
            }
            
            success = True
            
            # 各チャネルに送信
            for channel in channels:
                try:
                    if channel == NotificationChannel.SNS:
                        success &= self._send_sns_alert(alert_data)
                    elif channel == NotificationChannel.SLACK:
                        success &= self._send_slack_alert(alert_data)
                    # 他のチャネルも必要に応じて実装
                    
                except Exception as e:
                    logger.error(f"チャネル {channel.value} への送信エラー: {str(e)}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"アラート送信エラー: {str(e)}")
            return False
    
    def _send_sns_alert(self, alert_data: Dict[str, Any]) -> bool:
        """SNS 経由でアラートを送信"""
        try:
            if not self.sns_client:
                logger.warning("SNS クライアントが利用できません")
                return False
            
            # 重要度に応じてトピックを選択
            topic_arn = self._get_sns_topic_arn(alert_data["severity"])
            if not topic_arn:
                logger.warning("適切な SNS トピックが見つかりません")
                return False
            
            # SNS メッセージを構築
            sns_message = {
                "default": alert_data["message"],
                "email": self._format_email_message(alert_data),
                "sms": f"{alert_data['title']}: {alert_data['message']}"
            }
            
            # SNS に送信
            response = self.sns_client.publish(
                TopicArn=topic_arn,
                Message=json.dumps(sns_message),
                MessageStructure='json',
                Subject=f"[{alert_data['severity'].upper()}] {alert_data['title']}"
            )
            
            logger.info(f"SNS アラート送信成功: MessageId={response.get('MessageId')}")
            return True
            
        except Exception as e:
            logger.error(f"SNS アラート送信エラー: {str(e)}")
            return False
    
    def _send_slack_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Slack 経由でアラートを送信（SNS + Lambda 経由）"""
        try:
            # Slack 通知は SNS + Lambda で実装されているため、
            # 専用の SNS トピックに送信
            slack_topic_arn = self._get_slack_topic_arn()
            if not slack_topic_arn:
                logger.warning("Slack 通知用 SNS トピックが見つかりません")
                return False
            
            # Slack 用のメッセージフォーマット
            slack_message = {
                "AlarmName": alert_data["title"],
                "NewStateValue": "ALARM" if alert_data["severity"] in ["high", "critical"] else "WARNING",
                "NewStateReason": alert_data["message"],
                "StateChangeTime": alert_data["timestamp"],
                "Region": settings.aws_region,
                "AlarmDescription": json.dumps(alert_data["details"])
            }
            
            response = self.sns_client.publish(
                TopicArn=slack_topic_arn,
                Message=json.dumps(slack_message)
            )
            
            logger.info(f"Slack アラート送信成功: MessageId={response.get('MessageId')}")
            return True
            
        except Exception as e:
            logger.error(f"Slack アラート送信エラー: {str(e)}")
            return False
    
    def _get_sns_topic_arn(self, severity: str) -> Optional[str]:
        """重要度に応じた SNS トピック ARN を取得"""
        try:
            # CloudFormation エクスポートから取得
            if severity in ["high", "critical"]:
                # クリティカルアラート用トピック
                return f"arn:aws:sns:{settings.aws_region}:{settings.aws_account_id}:{settings.project_name}-{settings.environment}-alerts"
            else:
                # 警告レベル用トピック
                return f"arn:aws:sns:{settings.aws_region}:{settings.aws_account_id}:{settings.project_name}-{settings.environment}-warnings"
                
        except Exception as e:
            logger.error(f"SNS トピック ARN 取得エラー: {str(e)}")
            return None
    
    def _get_slack_topic_arn(self) -> Optional[str]:
        """Slack 通知用 SNS トピック ARN を取得"""
        try:
            return f"arn:aws:sns:{settings.aws_region}:{settings.aws_account_id}:{settings.project_name}-{settings.environment}-alerts"
        except Exception as e:
            logger.error(f"Slack トピック ARN 取得エラー: {str(e)}")
            return None
    
    def _format_email_message(self, alert_data: Dict[str, Any]) -> str:
        """メール用のメッセージフォーマット"""
        return f"""
{alert_data['title']}

重要度: {alert_data['severity'].upper()}
時刻: {alert_data['timestamp']}
環境: {alert_data['environment']}
サービス: {alert_data['service']}

メッセージ:
{alert_data['message']}

詳細情報:
{json.dumps(alert_data['details'], indent=2, ensure_ascii=False)}

---
このアラートは {alert_data['service']} から自動送信されました。
        """.strip()
    
    def send_system_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: AlertSeverity = AlertSeverity.HIGH
    ) -> bool:
        """
        システムエラーの通知を送信
        
        Args:
            error: 発生したエラー
            context: エラーコンテキスト
            severity: 重要度レベル
        
        Returns:
            bool: 送信成功フラグ
        """
        try:
            error_details = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {}
            }
            
            return self.send_alert(
                title=f"システムエラー: {type(error).__name__}",
                message=f"予期しないエラーが発生しました: {str(error)}",
                severity=severity,
                details=error_details
            )
            
        except Exception as e:
            logger.error(f"システムエラー通知送信エラー: {str(e)}")
            return False
    
    def send_business_event(
        self,
        event_type: str,
        description: str,
        data: Optional[Dict[str, Any]] = None,
        severity: AlertSeverity = AlertSeverity.LOW
    ) -> bool:
        """
        ビジネスイベントの通知を送信
        
        Args:
            event_type: イベントタイプ
            description: イベント説明
            data: イベントデータ
            severity: 重要度レベル
        
        Returns:
            bool: 送信成功フラグ
        """
        try:
            return self.send_alert(
                title=f"ビジネスイベント: {event_type}",
                message=description,
                severity=severity,
                details=data or {},
                channels=[NotificationChannel.SNS]  # ビジネスイベントは SNS のみ
            )
            
        except Exception as e:
            logger.error(f"ビジネスイベント通知送信エラー: {str(e)}")
            return False
    
    def send_security_alert(
        self,
        alert_type: str,
        description: str,
        user_info: Optional[Dict[str, Any]] = None,
        severity: AlertSeverity = AlertSeverity.HIGH
    ) -> bool:
        """
        セキュリティアラートの送信
        
        Args:
            alert_type: アラートタイプ
            description: アラート説明
            user_info: ユーザー情報
            severity: 重要度レベル
        
        Returns:
            bool: 送信成功フラグ
        """
        try:
            security_details = {
                "alert_type": alert_type,
                "user_info": user_info or {},
                "timestamp": datetime.utcnow().isoformat(),
                "source_ip": user_info.get("ip_address") if user_info else None
            }
            
            return self.send_alert(
                title=f"セキュリティアラート: {alert_type}",
                message=description,
                severity=severity,
                details=security_details,
                channels=[NotificationChannel.SNS, NotificationChannel.SLACK]
            )
            
        except Exception as e:
            logger.error(f"セキュリティアラート送信エラー: {str(e)}")
            return False


# グローバル通知管理インスタンス
notification_manager = NotificationManager()


# 便利な関数群
def send_error_notification(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    severity: AlertSeverity = AlertSeverity.HIGH
) -> bool:
    """エラー通知の送信"""
    return notification_manager.send_system_error(error, context, severity)


def send_security_notification(
    alert_type: str,
    description: str,
    user_info: Optional[Dict[str, Any]] = None
) -> bool:
    """セキュリティ通知の送信"""
    return notification_manager.send_security_alert(
        alert_type, description, user_info, AlertSeverity.HIGH
    )


def send_business_notification(
    event_type: str,
    description: str,
    data: Optional[Dict[str, Any]] = None
) -> bool:
    """ビジネスイベント通知の送信"""
    return notification_manager.send_business_event(
        event_type, description, data, AlertSeverity.LOW
    )


def send_critical_alert(title: str, message: str, details: Optional[Dict[str, Any]] = None) -> bool:
    """クリティカルアラートの送信"""
    return notification_manager.send_alert(
        title, message, AlertSeverity.CRITICAL, details,
        [NotificationChannel.SNS, NotificationChannel.SLACK]
    )


# デコレーター関数
def notify_on_error(
    severity: AlertSeverity = AlertSeverity.HIGH,
    include_context: bool = True
):
    """
    エラー発生時に自動通知するデコレーター
    
    Args:
        severity: 通知の重要度
        include_context: コンテキスト情報を含めるかどうか
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = None
                if include_context:
                    context = {
                        "function_name": func.__name__,
                        "args": str(args)[:200],  # 長すぎる場合は切り詰め
                        "kwargs": str(kwargs)[:200]
                    }
                
                send_error_notification(e, context, severity)
                raise  # 元の例外を再発生
        
        return wrapper
    return decorator


# 使用例とテスト用関数
def test_notifications():
    """通知機能のテスト"""
    
    # 基本的なアラート
    notification_manager.send_alert(
        "テストアラート",
        "これはテスト用のアラートです",
        AlertSeverity.LOW
    )
    
    # システムエラー通知
    try:
        raise ValueError("テスト用エラー")
    except Exception as e:
        send_error_notification(e, {"test": True})
    
    # セキュリティアラート
    send_security_notification(
        "suspicious_login",
        "疑わしいログイン試行が検出されました",
        {"user_id": "test_user", "ip_address": "192.168.1.1"}
    )
    
    # ビジネスイベント
    send_business_notification(
        "user_registration_spike",
        "ユーザー登録数が急増しています",
        {"registrations_per_hour": 100}
    )
    
    # クリティカルアラート
    send_critical_alert(
        "データベース接続エラー",
        "データベースへの接続が失敗しました",
        {"error_count": 5, "last_error": "Connection timeout"}
    )
    
    logger.info("通知テスト完了")


if __name__ == "__main__":
    # テスト実行
    test_notifications()