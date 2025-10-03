"""
カスタムメトリクス収集ユーティリティ

アプリケーション固有のメトリクスを CloudWatch に送信する機能を提供します。
"""

import boto3
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class MetricsCollector:
    """CloudWatch カスタムメトリクス収集クラス"""
    
    def __init__(self, namespace: str = "CSR-Lambda-API"):
        """
        メトリクス収集クラスを初期化
        
        Args:
            namespace: CloudWatch メトリクスの名前空間
        """
        self.namespace = namespace
        self.cloudwatch = boto3.client('cloudwatch')
        self._metrics_buffer: List[Dict[str, Any]] = []
        
    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = 'Count',
        dimensions: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        単一のメトリクスを CloudWatch に送信
        
        Args:
            metric_name: メトリクス名
            value: メトリクス値
            unit: メトリクスの単位
            dimensions: メトリクスのディメンション
            timestamp: メトリクスのタイムスタンプ
        """
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit
            }
            
            if timestamp:
                metric_data['Timestamp'] = timestamp
            
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': key, 'Value': value}
                    for key, value in dimensions.items()
                ]
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[metric_data]
            )
            
            logger.info(f"メトリクス送信成功: {metric_name} = {value} {unit}")
            
        except Exception as e:
            logger.error(f"メトリクス送信エラー: {metric_name} - {str(e)}")
    
    def put_metrics_batch(self, metrics: List[Dict[str, Any]]) -> None:
        """
        複数のメトリクスをバッチで CloudWatch に送信
        
        Args:
            metrics: メトリクスデータのリスト
        """
        try:
            # CloudWatch は一度に最大20個のメトリクスを受け付ける
            batch_size = 20
            for i in range(0, len(metrics), batch_size):
                batch = metrics[i:i + batch_size]
                
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=batch
                )
                
            logger.info(f"バッチメトリクス送信成功: {len(metrics)}個のメトリクス")
            
        except Exception as e:
            logger.error(f"バッチメトリクス送信エラー: {str(e)}")
    
    def add_to_buffer(
        self,
        metric_name: str,
        value: float,
        unit: str = 'Count',
        dimensions: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        メトリクスをバッファに追加（後でバッチ送信用）
        
        Args:
            metric_name: メトリクス名
            value: メトリクス値
            unit: メトリクスの単位
            dimensions: メトリクスのディメンション
            timestamp: メトリクスのタイムスタンプ
        """
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit
        }
        
        if timestamp:
            metric_data['Timestamp'] = timestamp
        
        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': key, 'Value': value}
                for key, value in dimensions.items()
            ]
        
        self._metrics_buffer.append(metric_data)
    
    def flush_buffer(self) -> None:
        """バッファ内のメトリクスをすべて送信"""
        if self._metrics_buffer:
            self.put_metrics_batch(self._metrics_buffer)
            self._metrics_buffer.clear()
    
    @contextmanager
    def timer(self, metric_name: str, dimensions: Optional[Dict[str, str]] = None):
        """
        実行時間を測定するコンテキストマネージャー
        
        Args:
            metric_name: メトリクス名
            dimensions: メトリクスのディメンション
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000  # ミリ秒に変換
            self.put_metric(
                metric_name=metric_name,
                value=duration,
                unit='Milliseconds',
                dimensions=dimensions
            )
    
    def increment_counter(
        self,
        metric_name: str,
        value: int = 1,
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """
        カウンターメトリクスをインクリメント
        
        Args:
            metric_name: メトリクス名
            value: インクリメント値
            dimensions: メトリクスのディメンション
        """
        self.put_metric(
            metric_name=metric_name,
            value=value,
            unit='Count',
            dimensions=dimensions
        )


# グローバルメトリクス収集インスタンス
metrics = MetricsCollector()


def track_api_call(endpoint: str):
    """
    API 呼び出しを追跡するデコレーター
    
    Args:
        endpoint: API エンドポイント名
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # API 呼び出し開始をカウント
            metrics.increment_counter(
                'api_calls_total',
                dimensions={'endpoint': endpoint}
            )
            
            try:
                result = await func(*args, **kwargs)
                
                # 成功メトリクス
                metrics.increment_counter(
                    'api_calls_success',
                    dimensions={'endpoint': endpoint}
                )
                
                return result
                
            except Exception as e:
                # エラーメトリクス
                metrics.increment_counter(
                    'api_calls_error',
                    dimensions={
                        'endpoint': endpoint,
                        'error_type': type(e).__name__
                    }
                )
                raise
                
            finally:
                # レスポンス時間メトリクス
                duration = (time.time() - start_time) * 1000
                metrics.put_metric(
                    'api_response_time',
                    value=duration,
                    unit='Milliseconds',
                    dimensions={'endpoint': endpoint}
                )
        
        return wrapper
    return decorator


def track_database_operation(operation: str):
    """
    データベース操作を追跡するデコレーター
    
    Args:
        operation: データベース操作名
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # データベース操作開始をカウント
            metrics.increment_counter(
                'db_operations_total',
                dimensions={'operation': operation}
            )
            
            try:
                result = await func(*args, **kwargs)
                
                # 成功メトリクス
                metrics.increment_counter(
                    'db_operations_success',
                    dimensions={'operation': operation}
                )
                
                return result
                
            except Exception as e:
                # エラーメトリクス
                metrics.increment_counter(
                    'db_operations_error',
                    dimensions={
                        'operation': operation,
                        'error_type': type(e).__name__
                    }
                )
                raise
                
            finally:
                # 実行時間メトリクス
                duration = (time.time() - start_time) * 1000
                metrics.put_metric(
                    'db_operation_time',
                    value=duration,
                    unit='Milliseconds',
                    dimensions={'operation': operation}
                )
        
        return wrapper
    return decorator


class BusinessMetrics:
    """ビジネスメトリクス収集クラス"""
    
    @staticmethod
    def track_user_registration():
        """ユーザー登録をトラッキング"""
        metrics.increment_counter('user_registrations')
    
    @staticmethod
    def track_user_login():
        """ユーザーログインをトラッキング"""
        metrics.increment_counter('user_logins')
    
    @staticmethod
    def track_user_logout():
        """ユーザーログアウトをトラッキング"""
        metrics.increment_counter('user_logouts')
    
    @staticmethod
    def track_authentication_failure(reason: str):
        """認証失敗をトラッキング"""
        metrics.increment_counter(
            'authentication_failures',
            dimensions={'reason': reason}
        )
    
    @staticmethod
    def track_data_validation_error(field: str):
        """データバリデーションエラーをトラッキング"""
        metrics.increment_counter(
            'validation_errors',
            dimensions={'field': field}
        )
    
    @staticmethod
    def track_external_api_call(service: str, success: bool, response_time: float):
        """外部API呼び出しをトラッキング"""
        status = 'success' if success else 'error'
        
        metrics.increment_counter(
            'external_api_calls',
            dimensions={'service': service, 'status': status}
        )
        
        metrics.put_metric(
            'external_api_response_time',
            value=response_time * 1000,  # ミリ秒に変換
            unit='Milliseconds',
            dimensions={'service': service}
        )


def log_custom_metric(
    metric_name: str,
    value: float,
    unit: str = 'Count',
    dimensions: Optional[Dict[str, str]] = None
):
    """
    カスタムメトリクスをログに記録（CloudWatch Logs Insights用）
    
    Args:
        metric_name: メトリクス名
        value: メトリクス値
        unit: メトリクスの単位
        dimensions: メトリクスのディメンション
    """
    metric_log = {
        'metric_name': metric_name,
        'value': value,
        'unit': unit,
        'timestamp': datetime.utcnow().isoformat(),
        'dimensions': dimensions or {}
    }
    
    logger.info(f"CUSTOM_METRIC: {metric_log}")


# 使用例とテスト用関数
def test_metrics():
    """メトリクス機能のテスト"""
    
    # 基本的なメトリクス送信
    metrics.put_metric('test_metric', 1.0)
    
    # ディメンション付きメトリクス
    metrics.put_metric(
        'test_metric_with_dimensions',
        5.0,
        unit='Count',
        dimensions={'environment': 'test', 'component': 'api'}
    )
    
    # タイマーの使用例
    with metrics.timer('test_operation_duration'):
        time.sleep(0.1)  # 100ms の処理をシミュレート
    
    # カウンターのインクリメント
    metrics.increment_counter('test_counter')
    
    # ビジネスメトリクス
    BusinessMetrics.track_user_login()
    BusinessMetrics.track_authentication_failure('invalid_password')
    
    # バッファを使用したバッチ送信
    metrics.add_to_buffer('buffered_metric_1', 10.0)
    metrics.add_to_buffer('buffered_metric_2', 20.0)
    metrics.flush_buffer()
    
    logger.info("メトリクステスト完了")


if __name__ == "__main__":
    # テスト実行
    test_metrics()