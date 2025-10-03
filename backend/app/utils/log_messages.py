"""
日本語ログメッセージ定義

アプリケーション全体で使用される日本語ログメッセージを定義する。
開発者向けの詳細なログ情報を日本語で提供し、デバッグとモニタリングを支援する。
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# ログレベル別の日本語表記
LOG_LEVELS_JP = {
    "DEBUG": "デバッグ",
    "INFO": "情報",
    "WARNING": "警告",
    "ERROR": "エラー",
    "CRITICAL": "重大"
}

# 認証関連ログメッセージ
AUTH_LOG_MESSAGES = {
    "LOGIN_SUCCESS": "ログイン成功: ユーザー {username} (ID: {user_id})",
    "LOGIN_FAILED": "ログイン失敗: {email} - 理由: {reason}",
    "LOGOUT_SUCCESS": "ログアウト成功: ユーザー {username} (ID: {user_id})",
    "TOKEN_VERIFIED": "トークン検証成功: ユーザー {username}",
    "TOKEN_VERIFICATION_FAILED": "トークン検証失敗: {reason}",
    "PASSWORD_RESET_REQUESTED": "パスワードリセット要求: {email}",
    "PASSWORD_RESET_COMPLETED": "パスワードリセット完了: ユーザー {username}",
    "ACCOUNT_CREATED": "アカウント作成: {email} (ユーザー名: {username})",
    "ACCOUNT_DISABLED": "アカウント無効化: ユーザー {username} (理由: {reason})",
    "UNAUTHORIZED_ACCESS": "不正アクセス試行: IP {ip_address} - エンドポイント: {endpoint}",
}

# データベース関連ログメッセージ
DATABASE_LOG_MESSAGES = {
    "CONNECTION_ESTABLISHED": "データベース接続確立: {database_name}",
    "CONNECTION_FAILED": "データベース接続失敗: {error_message}",
    "QUERY_EXECUTED": "クエリ実行: {query_type} - 実行時間: {duration}ms",
    "QUERY_FAILED": "クエリ実行失敗: {query} - エラー: {error_message}",
    "TRANSACTION_STARTED": "トランザクション開始: {transaction_id}",
    "TRANSACTION_COMMITTED": "トランザクションコミット: {transaction_id}",
    "TRANSACTION_ROLLBACK": "トランザクションロールバック: {transaction_id} - 理由: {reason}",
    "RECORD_CREATED": "レコード作成: テーブル {table_name} - ID: {record_id}",
    "RECORD_UPDATED": "レコード更新: テーブル {table_name} - ID: {record_id}",
    "RECORD_DELETED": "レコード削除: テーブル {table_name} - ID: {record_id}",
    "MIGRATION_STARTED": "マイグレーション開始: {migration_name}",
    "MIGRATION_COMPLETED": "マイグレーション完了: {migration_name}",
}

# API関連ログメッセージ
API_LOG_MESSAGES = {
    "REQUEST_RECEIVED": "リクエスト受信: {method} {path} - IP: {ip_address}",
    "REQUEST_PROCESSED": "リクエスト処理完了: {method} {path} - ステータス: {status_code} - 処理時間: {duration}ms",
    "REQUEST_FAILED": "リクエスト処理失敗: {method} {path} - エラー: {error_message}",
    "RATE_LIMIT_EXCEEDED": "レート制限超過: IP {ip_address} - エンドポイント: {endpoint}",
    "VALIDATION_ERROR": "バリデーションエラー: {field_name} - {error_message}",
    "CORS_BLOCKED": "CORS ブロック: オリジン {origin} - エンドポイント: {endpoint}",
    "MIDDLEWARE_ERROR": "ミドルウェアエラー: {middleware_name} - {error_message}",
}

# システム関連ログメッセージ
SYSTEM_LOG_MESSAGES = {
    "APPLICATION_STARTED": "アプリケーション開始: 環境 {environment} - バージョン {version}",
    "APPLICATION_STOPPED": "アプリケーション停止: 稼働時間 {uptime}",
    "HEALTH_CHECK_SUCCESS": "ヘルスチェック成功: 全サービス正常",
    "HEALTH_CHECK_FAILED": "ヘルスチェック失敗: {failed_services}",
    "CONFIGURATION_LOADED": "設定読み込み完了: {config_source}",
    "CONFIGURATION_ERROR": "設定エラー: {error_message}",
    "CACHE_HIT": "キャッシュヒット: キー {cache_key}",
    "CACHE_MISS": "キャッシュミス: キー {cache_key}",
    "CACHE_CLEARED": "キャッシュクリア: パターン {pattern}",
    "EXTERNAL_SERVICE_CALL": "外部サービス呼び出し: {service_name} - エンドポイント: {endpoint}",
    "EXTERNAL_SERVICE_ERROR": "外部サービスエラー: {service_name} - {error_message}",
}

# パフォーマンス関連ログメッセージ
PERFORMANCE_LOG_MESSAGES = {
    "SLOW_QUERY": "遅いクエリ検出: {query} - 実行時間: {duration}ms",
    "SLOW_REQUEST": "遅いリクエスト検出: {method} {path} - 処理時間: {duration}ms",
    "HIGH_MEMORY_USAGE": "高メモリ使用量: {memory_usage}MB - 閾値: {threshold}MB",
    "HIGH_CPU_USAGE": "高CPU使用率: {cpu_usage}% - 閾値: {threshold}%",
    "LAMBDA_COLD_START": "Lambda コールドスタート: 初期化時間 {init_duration}ms",
    "LAMBDA_TIMEOUT_WARNING": "Lambda タイムアウト警告: 残り時間 {remaining_time}ms",
}

# セキュリティ関連ログメッセージ
SECURITY_LOG_MESSAGES = {
    "SUSPICIOUS_ACTIVITY": "不審な活動検出: IP {ip_address} - 活動: {activity}",
    "BRUTE_FORCE_ATTEMPT": "ブルートフォース攻撃検出: IP {ip_address} - 試行回数: {attempts}",
    "SQL_INJECTION_ATTEMPT": "SQL インジェクション試行: IP {ip_address} - パラメータ: {parameter}",
    "XSS_ATTEMPT": "XSS 攻撃試行: IP {ip_address} - 入力値: {input_value}",
    "INVALID_TOKEN_USAGE": "無効トークン使用: IP {ip_address} - トークン: {token_prefix}...",
    "PRIVILEGE_ESCALATION": "権限昇格試行: ユーザー {username} - 要求権限: {requested_permission}",
}

# 全ログメッセージを統合
ALL_LOG_MESSAGES = {
    **AUTH_LOG_MESSAGES,
    **DATABASE_LOG_MESSAGES,
    **API_LOG_MESSAGES,
    **SYSTEM_LOG_MESSAGES,
    **PERFORMANCE_LOG_MESSAGES,
    **SECURITY_LOG_MESSAGES,
}


class JapaneseLogger:
    """
    日本語ログメッセージ用のロガークラス
    
    構造化ログと日本語メッセージを組み合わせて、
    開発者にとって理解しやすいログを出力する。
    """
    
    def __init__(self, name: str):
        """
        ロガーを初期化する
        
        Args:
            name (str): ロガー名
        """
        self.logger = logging.getLogger(name)
    
    def _format_message(self, message_key: str, **kwargs) -> str:
        """
        メッセージテンプレートをフォーマットする
        
        Args:
            message_key (str): メッセージキー
            **kwargs: フォーマット用パラメータ
            
        Returns:
            str: フォーマットされたメッセージ
        """
        template = ALL_LOG_MESSAGES.get(message_key, message_key)
        try:
            return template.format(**kwargs)
        except KeyError as e:
            return f"{template} (フォーマットエラー: {e})"
    
    def _log_with_context(self, level: int, message_key: str, context: Dict[str, Any] = None, **kwargs):
        """
        コンテキスト情報付きでログを出力する
        
        Args:
            level (int): ログレベル
            message_key (str): メッセージキー
            context (Dict[str, Any], optional): 追加コンテキスト
            **kwargs: メッセージフォーマット用パラメータ
        """
        message = self._format_message(message_key, **kwargs)
        
        # 構造化ログ用の追加情報
        extra = {
            "message_key": message_key,
            "timestamp": datetime.utcnow().isoformat(),
            **(context or {}),
            **kwargs
        }
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message_key: str, context: Dict[str, Any] = None, **kwargs):
        """デバッグログを出力"""
        self._log_with_context(logging.DEBUG, message_key, context, **kwargs)
    
    def info(self, message_key: str, context: Dict[str, Any] = None, **kwargs):
        """情報ログを出力"""
        self._log_with_context(logging.INFO, message_key, context, **kwargs)
    
    def warning(self, message_key: str, context: Dict[str, Any] = None, **kwargs):
        """警告ログを出力"""
        self._log_with_context(logging.WARNING, message_key, context, **kwargs)
    
    def error(self, message_key: str, context: Dict[str, Any] = None, **kwargs):
        """エラーログを出力"""
        self._log_with_context(logging.ERROR, message_key, context, **kwargs)
    
    def critical(self, message_key: str, context: Dict[str, Any] = None, **kwargs):
        """重大エラーログを出力"""
        self._log_with_context(logging.CRITICAL, message_key, context, **kwargs)


def get_logger(name: str) -> JapaneseLogger:
    """
    日本語ロガーのインスタンスを取得する
    
    Args:
        name (str): ロガー名
        
    Returns:
        JapaneseLogger: 日本語ロガーインスタンス
    """
    return JapaneseLogger(name)


# よく使用されるログ関数のショートカット
def log_auth_success(username: str, user_id: int, ip_address: str = None):
    """認証成功ログ"""
    logger = get_logger("auth")
    logger.info("LOGIN_SUCCESS", username=username, user_id=user_id, ip_address=ip_address)


def log_auth_failure(email: str, reason: str, ip_address: str = None):
    """認証失敗ログ"""
    logger = get_logger("auth")
    logger.warning("LOGIN_FAILED", email=email, reason=reason, ip_address=ip_address)


def log_api_request(method: str, path: str, ip_address: str, duration: float = None, status_code: int = None):
    """API リクエストログ"""
    logger = get_logger("api")
    if duration is not None and status_code is not None:
        logger.info("REQUEST_PROCESSED", method=method, path=path, ip_address=ip_address, 
                   duration=duration, status_code=status_code)
    else:
        logger.info("REQUEST_RECEIVED", method=method, path=path, ip_address=ip_address)


def log_database_operation(operation: str, table_name: str, record_id: Any = None, duration: float = None):
    """データベース操作ログ"""
    logger = get_logger("database")
    if operation == "CREATE":
        logger.info("RECORD_CREATED", table_name=table_name, record_id=record_id)
    elif operation == "UPDATE":
        logger.info("RECORD_UPDATED", table_name=table_name, record_id=record_id)
    elif operation == "DELETE":
        logger.info("RECORD_DELETED", table_name=table_name, record_id=record_id)


def log_performance_issue(issue_type: str, **kwargs):
    """パフォーマンス問題ログ"""
    logger = get_logger("performance")
    logger.warning(issue_type, **kwargs)


def log_security_event(event_type: str, ip_address: str, **kwargs):
    """セキュリティイベントログ"""
    logger = get_logger("security")
    logger.warning(event_type, ip_address=ip_address, **kwargs)