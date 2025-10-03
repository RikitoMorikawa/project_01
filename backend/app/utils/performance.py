"""
パフォーマンス最適化ユーティリティ

Lambda コールドスタート対策、データベース最適化、キャッシング戦略を提供する
"""

import time
import logging
import functools
import asyncio
from typing import Any, Dict, Optional, Callable, Union
from datetime import datetime, timedelta
import json
import hashlib
import os
from contextlib import asynccontextmanager

# Redis クライアント（オプション）
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class LambdaColdStartOptimizer:
    """
    Lambda コールドスタート最適化
    
    接続プールの事前初期化、グローバル変数の活用、
    初期化処理の最適化を行う
    """
    
    _initialized = False
    _db_pool = None
    _redis_client = None
    _startup_time = None
    
    @classmethod
    def initialize(cls):
        """Lambda 関数の初期化処理"""
        
        if cls._initialized:
            return
        
        start_time = time.time()
        logger.info("Lambda コールドスタート最適化を開始")
        
        try:
            # データベース接続プールの事前初期化
            cls._initialize_db_pool()
            
            # Redis 接続の事前初期化（利用可能な場合）
            cls._initialize_redis()
            
            # 設定の事前読み込み
            cls._preload_configuration()
            
            cls._startup_time = time.time() - start_time
            cls._initialized = True
            
            logger.info(f"Lambda 初期化完了: {cls._startup_time:.3f}秒")
            
        except Exception as e:
            logger.error(f"Lambda 初期化エラー: {str(e)}")
            raise
    
    @classmethod
    def _initialize_db_pool(cls):
        """データベース接続プールの初期化"""
        
        try:
            from app.database import get_db_pool
            cls._db_pool = get_db_pool()
            logger.info("データベース接続プールを初期化しました")
        except Exception as e:
            logger.warning(f"データベース接続プール初期化エラー: {str(e)}")
    
    @classmethod
    def _initialize_redis(cls):
        """Redis 接続の初期化"""
        
        if not REDIS_AVAILABLE:
            return
        
        try:
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                cls._redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # 接続テスト
                cls._redis_client.ping()
                logger.info("Redis 接続を初期化しました")
        except Exception as e:
            logger.warning(f"Redis 接続初期化エラー: {str(e)}")
            cls._redis_client = None
    
    @classmethod
    def _preload_configuration(cls):
        """設定の事前読み込み"""
        
        try:
            from app.config import settings
            # 設定値を事前に読み込んでキャッシュ
            _ = settings.database_url
            _ = settings.cors_origins
            _ = settings.jwt_secret_key
            logger.info("設定を事前読み込みしました")
        except Exception as e:
            logger.warning(f"設定事前読み込みエラー: {str(e)}")
    
    @classmethod
    def get_db_pool(cls):
        """データベース接続プールを取得"""
        
        if not cls._initialized:
            cls.initialize()
        
        return cls._db_pool
    
    @classmethod
    def get_redis_client(cls):
        """Redis クライアントを取得"""
        
        if not cls._initialized:
            cls.initialize()
        
        return cls._redis_client
    
    @classmethod
    def get_startup_time(cls) -> Optional[float]:
        """起動時間を取得"""
        return cls._startup_time


class DatabaseQueryOptimizer:
    """
    データベースクエリ最適化
    
    クエリキャッシング、バッチ処理、インデックス最適化を提供する
    """
    
    def __init__(self, cache_ttl: int = 300):
        self.cache_ttl = cache_ttl
        self._query_cache = {}
        self._cache_timestamps = {}
    
    def cached_query(self, cache_key: str = None, ttl: int = None):
        """
        クエリ結果をキャッシュするデコレータ
        
        Args:
            cache_key: キャッシュキー（指定しない場合は関数名と引数から生成）
            ttl: キャッシュ有効期限（秒）
        """
        
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # キャッシュキーの生成
                if cache_key:
                    key = cache_key
                else:
                    # 関数名と引数からキャッシュキーを生成
                    args_str = str(args) + str(sorted(kwargs.items()))
                    key = f"{func.__name__}:{hashlib.md5(args_str.encode()).hexdigest()}"
                
                # キャッシュから取得を試行
                cached_result = await self._get_from_cache(key)
                if cached_result is not None:
                    logger.debug(f"クエリキャッシュヒット: {key}")
                    return cached_result
                
                # キャッシュミスの場合は実際のクエリを実行
                logger.debug(f"クエリキャッシュミス: {key}")
                result = await func(*args, **kwargs)
                
                # 結果をキャッシュに保存
                await self._set_to_cache(key, result, ttl or self.cache_ttl)
                
                return result
            
            return wrapper
        return decorator
    
    async def _get_from_cache(self, key: str) -> Any:
        """キャッシュから値を取得"""
        
        # Redis を優先的に使用
        redis_client = LambdaColdStartOptimizer.get_redis_client()
        if redis_client:
            try:
                cached_data = redis_client.get(f"query:{key}")
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Redis キャッシュ取得エラー: {str(e)}")
        
        # フォールバック: メモリキャッシュ
        if key in self._query_cache:
            timestamp = self._cache_timestamps.get(key, 0)
            if time.time() - timestamp < self.cache_ttl:
                return self._query_cache[key]
            else:
                # 期限切れのキャッシュを削除
                del self._query_cache[key]
                del self._cache_timestamps[key]
        
        return None
    
    async def _set_to_cache(self, key: str, value: Any, ttl: int):
        """キャッシュに値を設定"""
        
        # Redis を優先的に使用
        redis_client = LambdaColdStartOptimizer.get_redis_client()
        if redis_client:
            try:
                redis_client.setex(
                    f"query:{key}",
                    ttl,
                    json.dumps(value, default=str)
                )
                return
            except Exception as e:
                logger.warning(f"Redis キャッシュ設定エラー: {str(e)}")
        
        # フォールバック: メモリキャッシュ
        self._query_cache[key] = value
        self._cache_timestamps[key] = time.time()
    
    async def invalidate_cache(self, pattern: str = None):
        """キャッシュを無効化"""
        
        redis_client = LambdaColdStartOptimizer.get_redis_client()
        if redis_client:
            try:
                if pattern:
                    keys = redis_client.keys(f"query:{pattern}*")
                    if keys:
                        redis_client.delete(*keys)
                else:
                    keys = redis_client.keys("query:*")
                    if keys:
                        redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis キャッシュ無効化エラー: {str(e)}")
        
        # メモリキャッシュも無効化
        if pattern:
            keys_to_delete = [k for k in self._query_cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._query_cache[key]
                del self._cache_timestamps[key]
        else:
            self._query_cache.clear()
            self._cache_timestamps.clear()


class ResponseCacheManager:
    """
    レスポンスキャッシュ管理
    
    API レスポンスのキャッシングとキャッシュ戦略を管理する
    """
    
    def __init__(self):
        self.default_ttl = 300  # 5分
        self.cache_strategies = {
            # エンドポイント別のキャッシュ戦略
            "/api/v1/health": {"ttl": 60, "vary": []},
            "/api/v1/users": {"ttl": 300, "vary": ["Authorization"]},
            "/api/v1/users/me": {"ttl": 600, "vary": ["Authorization"]},
        }
    
    def cache_response(
        self, 
        endpoint_pattern: str = None,
        ttl: int = None,
        vary_headers: list = None,
        cache_control: str = None
    ):
        """
        レスポンスキャッシュデコレータ
        
        Args:
            endpoint_pattern: エンドポイントパターン
            ttl: キャッシュ有効期限（秒）
            vary_headers: キャッシュキーに含めるヘッダー
            cache_control: Cache-Control ヘッダーの値
        """
        
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # リクエストオブジェクトを取得
                request = None
                for arg in args:
                    if hasattr(arg, 'url') and hasattr(arg, 'headers'):
                        request = arg
                        break
                
                if not request:
                    # リクエストオブジェクトが見つからない場合はキャッシュしない
                    return await func(*args, **kwargs)
                
                # キャッシュ戦略を決定
                strategy = self._get_cache_strategy(
                    str(request.url.path), 
                    endpoint_pattern, 
                    ttl, 
                    vary_headers
                )
                
                if not strategy:
                    # キャッシュしない
                    return await func(*args, **kwargs)
                
                # キャッシュキーを生成
                cache_key = self._generate_cache_key(request, strategy["vary"])
                
                # キャッシュから取得を試行
                cached_response = await self._get_cached_response(cache_key)
                if cached_response:
                    logger.debug(f"レスポンスキャッシュヒット: {cache_key}")
                    return cached_response
                
                # キャッシュミスの場合は実際の処理を実行
                logger.debug(f"レスポンスキャッシュミス: {cache_key}")
                response = await func(*args, **kwargs)
                
                # レスポンスをキャッシュに保存
                await self._cache_response(cache_key, response, strategy["ttl"])
                
                # Cache-Control ヘッダーを設定
                if hasattr(response, 'headers') and cache_control:
                    response.headers["Cache-Control"] = cache_control
                elif hasattr(response, 'headers'):
                    response.headers["Cache-Control"] = f"public, max-age={strategy['ttl']}"
                
                return response
            
            return wrapper
        return decorator
    
    def _get_cache_strategy(
        self, 
        path: str, 
        endpoint_pattern: str, 
        ttl: int, 
        vary_headers: list
    ) -> Optional[Dict]:
        """キャッシュ戦略を取得"""
        
        # 明示的に指定された戦略を優先
        if endpoint_pattern and ttl is not None:
            return {
                "ttl": ttl,
                "vary": vary_headers or []
            }
        
        # 事前定義された戦略を確認
        for pattern, strategy in self.cache_strategies.items():
            if path.startswith(pattern):
                return strategy
        
        # デフォルト戦略
        return {
            "ttl": self.default_ttl,
            "vary": []
        }
    
    def _generate_cache_key(self, request, vary_headers: list) -> str:
        """キャッシュキーを生成"""
        
        key_parts = [
            request.method,
            str(request.url.path),
            str(request.url.query)
        ]
        
        # Vary ヘッダーをキーに含める
        for header in vary_headers:
            header_value = request.headers.get(header, "")
            key_parts.append(f"{header}:{header_value}")
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def _get_cached_response(self, cache_key: str):
        """キャッシュされたレスポンスを取得"""
        
        redis_client = LambdaColdStartOptimizer.get_redis_client()
        if redis_client:
            try:
                cached_data = redis_client.get(f"response:{cache_key}")
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"レスポンスキャッシュ取得エラー: {str(e)}")
        
        return None
    
    async def _cache_response(self, cache_key: str, response, ttl: int):
        """レスポンスをキャッシュに保存"""
        
        redis_client = LambdaColdStartOptimizer.get_redis_client()
        if redis_client:
            try:
                # レスポンスをシリアライズ
                if hasattr(response, 'dict'):
                    response_data = response.dict()
                elif hasattr(response, '__dict__'):
                    response_data = response.__dict__
                else:
                    response_data = str(response)
                
                redis_client.setex(
                    f"response:{cache_key}",
                    ttl,
                    json.dumps(response_data, default=str)
                )
            except Exception as e:
                logger.warning(f"レスポンスキャッシュ保存エラー: {str(e)}")


class PerformanceMonitor:
    """
    パフォーマンス監視
    
    レスポンス時間、メモリ使用量、データベースクエリ時間を監視する
    """
    
    def __init__(self):
        self.metrics = {}
    
    def monitor_performance(self, operation_name: str = None):
        """パフォーマンス監視デコレータ"""
        
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                op_name = operation_name or func.__name__
                
                start_time = time.time()
                start_memory = self._get_memory_usage()
                
                try:
                    result = await func(*args, **kwargs)
                    
                    end_time = time.time()
                    end_memory = self._get_memory_usage()
                    
                    # メトリクスを記録
                    execution_time = end_time - start_time
                    memory_delta = end_memory - start_memory
                    
                    self._record_metrics(op_name, {
                        "execution_time": execution_time,
                        "memory_delta": memory_delta,
                        "timestamp": datetime.now().isoformat(),
                        "status": "success"
                    })
                    
                    # 遅い処理を警告
                    if execution_time > 1.0:  # 1秒以上
                        logger.warning(
                            f"遅い処理を検出: {op_name} - {execution_time:.3f}秒"
                        )
                    
                    # メモリ使用量の増加を警告
                    if memory_delta > 50 * 1024 * 1024:  # 50MB以上
                        logger.warning(
                            f"大きなメモリ使用量を検出: {op_name} - {memory_delta / 1024 / 1024:.1f}MB"
                        )
                    
                    return result
                    
                except Exception as e:
                    end_time = time.time()
                    execution_time = end_time - start_time
                    
                    self._record_metrics(op_name, {
                        "execution_time": execution_time,
                        "timestamp": datetime.now().isoformat(),
                        "status": "error",
                        "error": str(e)
                    })
                    
                    raise
            
            return wrapper
        return decorator
    
    def _get_memory_usage(self) -> int:
        """現在のメモリ使用量を取得（バイト）"""
        
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            # psutil が利用できない場合は 0 を返す
            return 0
        except Exception:
            return 0
    
    def _record_metrics(self, operation_name: str, metrics: Dict):
        """メトリクスを記録"""
        
        if operation_name not in self.metrics:
            self.metrics[operation_name] = []
        
        self.metrics[operation_name].append(metrics)
        
        # 古いメトリクスを削除（最新100件のみ保持）
        if len(self.metrics[operation_name]) > 100:
            self.metrics[operation_name] = self.metrics[operation_name][-100:]
        
        # CloudWatch にメトリクスを送信
        self._send_to_cloudwatch(operation_name, metrics)
    
    def _send_to_cloudwatch(self, operation_name: str, metrics: Dict):
        """CloudWatch にメトリクスを送信"""
        
        try:
            from app.utils.metrics import metrics as cloudwatch_metrics
            
            # 実行時間メトリクス
            if "execution_time" in metrics:
                cloudwatch_metrics.put_metric(
                    f"performance.{operation_name}.execution_time",
                    metrics["execution_time"],
                    "Seconds"
                )
            
            # メモリ使用量メトリクス
            if "memory_delta" in metrics:
                cloudwatch_metrics.put_metric(
                    f"performance.{operation_name}.memory_delta",
                    metrics["memory_delta"],
                    "Bytes"
                )
            
            # エラー率メトリクス
            if metrics.get("status") == "error":
                cloudwatch_metrics.increment_counter(
                    f"performance.{operation_name}.errors"
                )
            else:
                cloudwatch_metrics.increment_counter(
                    f"performance.{operation_name}.success"
                )
                
        except Exception as e:
            logger.warning(f"CloudWatch メトリクス送信エラー: {str(e)}")
    
    def get_performance_summary(self) -> Dict:
        """パフォーマンスサマリーを取得"""
        
        summary = {}
        
        for operation_name, operation_metrics in self.metrics.items():
            if not operation_metrics:
                continue
            
            execution_times = [
                m["execution_time"] for m in operation_metrics 
                if "execution_time" in m
            ]
            
            if execution_times:
                summary[operation_name] = {
                    "count": len(execution_times),
                    "avg_execution_time": sum(execution_times) / len(execution_times),
                    "max_execution_time": max(execution_times),
                    "min_execution_time": min(execution_times),
                    "error_count": len([
                        m for m in operation_metrics 
                        if m.get("status") == "error"
                    ])
                }
        
        return summary


# グローバルインスタンス
db_optimizer = DatabaseQueryOptimizer()
response_cache = ResponseCacheManager()
performance_monitor = PerformanceMonitor()


# 便利な関数
def optimize_lambda_startup():
    """Lambda 起動時の最適化を実行"""
    LambdaColdStartOptimizer.initialize()


def get_performance_summary():
    """パフォーマンスサマリーを取得"""
    return performance_monitor.get_performance_summary()


async def warm_up_connections():
    """接続のウォームアップ"""
    
    try:
        # データベース接続のウォームアップ
        db_pool = LambdaColdStartOptimizer.get_db_pool()
        if db_pool:
            # 簡単なクエリを実行して接続をウォームアップ
            async with db_pool.acquire() as connection:
                await connection.execute("SELECT 1")
            logger.info("データベース接続をウォームアップしました")
        
        # Redis 接続のウォームアップ
        redis_client = LambdaColdStartOptimizer.get_redis_client()
        if redis_client:
            redis_client.ping()
            logger.info("Redis 接続をウォームアップしました")
            
    except Exception as e:
        logger.warning(f"接続ウォームアップエラー: {str(e)}")


# デコレータのエイリアス
cached_query = db_optimizer.cached_query
cache_response = response_cache.cache_response
monitor_performance = performance_monitor.monitor_performance