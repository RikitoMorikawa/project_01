"""
キャッシング戦略設定

Redis、メモリキャッシュ、CloudFront キャッシングの設定を管理する
"""

import os
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass


class CacheStrategy(Enum):
    """キャッシング戦略"""
    NO_CACHE = "no-cache"
    MEMORY_ONLY = "memory-only"
    REDIS_ONLY = "redis-only"
    MEMORY_AND_REDIS = "memory-and-redis"
    CDN_CACHE = "cdn-cache"


@dataclass
class CacheConfig:
    """キャッシュ設定"""
    strategy: CacheStrategy
    ttl: int  # 秒
    max_size: Optional[int] = None  # メモリキャッシュの最大サイズ
    vary_headers: Optional[list] = None  # キャッシュキーに含めるヘッダー
    cache_control: Optional[str] = None  # Cache-Control ヘッダー


class CacheConfigManager:
    """キャッシュ設定管理"""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "dev")
        self.redis_enabled = bool(os.getenv("REDIS_URL"))
        
        # エンドポイント別キャッシュ設定
        self._endpoint_configs = self._initialize_endpoint_configs()
        
        # デフォルト設定
        self._default_config = self._get_default_config()
    
    def _initialize_endpoint_configs(self) -> Dict[str, CacheConfig]:
        """エンドポイント別キャッシュ設定を初期化"""
        
        configs = {}
        
        # ヘルスチェック - 短時間キャッシュ
        configs["/api/v1/health"] = CacheConfig(
            strategy=CacheStrategy.MEMORY_AND_REDIS if self.redis_enabled else CacheStrategy.MEMORY_ONLY,
            ttl=60,  # 1分
            cache_control="public, max-age=60"
        )
        
        # ユーザー一覧 - 認証付きキャッシュ
        configs["/api/v1/users"] = CacheConfig(
            strategy=CacheStrategy.REDIS_ONLY if self.redis_enabled else CacheStrategy.MEMORY_ONLY,
            ttl=300,  # 5分
            vary_headers=["Authorization"],
            cache_control="private, max-age=300"
        )
        
        # ユーザー詳細 - 長時間キャッシュ
        configs["/api/v1/users/{id}"] = CacheConfig(
            strategy=CacheStrategy.MEMORY_AND_REDIS if self.redis_enabled else CacheStrategy.MEMORY_ONLY,
            ttl=600,  # 10分
            vary_headers=["Authorization"],
            cache_control="private, max-age=600"
        )
        
        # 現在のユーザー情報 - 中時間キャッシュ
        configs["/api/v1/users/me"] = CacheConfig(
            strategy=CacheStrategy.REDIS_ONLY if self.redis_enabled else CacheStrategy.MEMORY_ONLY,
            ttl=300,  # 5分
            vary_headers=["Authorization"],
            cache_control="private, max-age=300"
        )
        
        # 認証エンドポイント - キャッシュしない
        configs["/api/v1/auth/login"] = CacheConfig(
            strategy=CacheStrategy.NO_CACHE,
            ttl=0,
            cache_control="no-store, no-cache, must-revalidate"
        )
        
        configs["/api/v1/auth/refresh"] = CacheConfig(
            strategy=CacheStrategy.NO_CACHE,
            ttl=0,
            cache_control="no-store, no-cache, must-revalidate"
        )
        
        configs["/api/v1/auth/logout"] = CacheConfig(
            strategy=CacheStrategy.NO_CACHE,
            ttl=0,
            cache_control="no-store, no-cache, must-revalidate"
        )
        
        # 環境別の調整
        if self.environment == "prod":
            # 本番環境では長めのキャッシュ
            for config in configs.values():
                if config.strategy != CacheStrategy.NO_CACHE:
                    config.ttl = int(config.ttl * 1.5)  # 1.5倍
        
        elif self.environment == "dev":
            # 開発環境では短めのキャッシュ
            for config in configs.values():
                if config.strategy != CacheStrategy.NO_CACHE:
                    config.ttl = max(30, int(config.ttl * 0.5))  # 0.5倍、最低30秒
        
        return configs
    
    def _get_default_config(self) -> CacheConfig:
        """デフォルトキャッシュ設定を取得"""
        
        if self.environment == "prod":
            return CacheConfig(
                strategy=CacheStrategy.MEMORY_AND_REDIS if self.redis_enabled else CacheStrategy.MEMORY_ONLY,
                ttl=300,  # 5分
                cache_control="public, max-age=300"
            )
        elif self.environment == "staging":
            return CacheConfig(
                strategy=CacheStrategy.REDIS_ONLY if self.redis_enabled else CacheStrategy.MEMORY_ONLY,
                ttl=180,  # 3分
                cache_control="public, max-age=180"
            )
        else:  # dev
            return CacheConfig(
                strategy=CacheStrategy.MEMORY_ONLY,
                ttl=60,  # 1分
                cache_control="public, max-age=60"
            )
    
    def get_config(self, endpoint: str) -> CacheConfig:
        """エンドポイントのキャッシュ設定を取得"""
        
        # 完全一致を確認
        if endpoint in self._endpoint_configs:
            return self._endpoint_configs[endpoint]
        
        # パターンマッチングを確認
        for pattern, config in self._endpoint_configs.items():
            if self._match_pattern(endpoint, pattern):
                return config
        
        # デフォルト設定を返す
        return self._default_config
    
    def _match_pattern(self, endpoint: str, pattern: str) -> bool:
        """エンドポイントパターンのマッチング"""
        
        # 単純なパターンマッチング（{id} などのプレースホルダー対応）
        import re
        
        # プレースホルダーを正規表現に変換
        regex_pattern = pattern.replace("{id}", r"[^/]+")
        regex_pattern = regex_pattern.replace("{user_id}", r"[^/]+")
        regex_pattern = f"^{regex_pattern}$"
        
        return bool(re.match(regex_pattern, endpoint))
    
    def should_cache_response(self, endpoint: str, status_code: int) -> bool:
        """レスポンスをキャッシュすべきかどうかを判定"""
        
        config = self.get_config(endpoint)
        
        # キャッシュしない設定の場合
        if config.strategy == CacheStrategy.NO_CACHE:
            return False
        
        # エラーレスポンスはキャッシュしない
        if status_code >= 400:
            return False
        
        # リダイレクトレスポンスは短時間キャッシュ
        if 300 <= status_code < 400:
            return True
        
        # 成功レスポンスはキャッシュ
        return status_code == 200
    
    def get_cache_headers(self, endpoint: str) -> Dict[str, str]:
        """キャッシュ関連ヘッダーを取得"""
        
        config = self.get_config(endpoint)
        headers = {}
        
        if config.cache_control:
            headers["Cache-Control"] = config.cache_control
        
        # ETag の生成（簡単な実装）
        if config.strategy != CacheStrategy.NO_CACHE:
            import hashlib
            etag = hashlib.md5(f"{endpoint}:{config.ttl}".encode()).hexdigest()[:8]
            headers["ETag"] = f'"{etag}"'
        
        # Vary ヘッダー
        if config.vary_headers:
            headers["Vary"] = ", ".join(config.vary_headers)
        
        return headers
    
    def invalidate_pattern(self, pattern: str) -> list:
        """パターンに一致するキャッシュキーを取得（無効化用）"""
        
        # 実際の実装では Redis の KEYS コマンドや
        # より効率的な方法を使用する
        cache_keys = []
        
        for endpoint_pattern in self._endpoint_configs.keys():
            if pattern in endpoint_pattern:
                cache_keys.append(f"response:{endpoint_pattern}:*")
                cache_keys.append(f"query:{endpoint_pattern}:*")
        
        return cache_keys


# CloudFront キャッシング設定
CLOUDFRONT_CACHE_BEHAVIORS = {
    # 静的アセット - 長期キャッシュ
    "/static/*": {
        "ttl": 31536000,  # 1年
        "cache_control": "public, max-age=31536000, immutable",
        "compress": True,
    },
    
    # API エンドポイント - 短期キャッシュ
    "/api/v1/health": {
        "ttl": 60,  # 1分
        "cache_control": "public, max-age=60",
        "compress": True,
    },
    
    # 認証エンドポイント - キャッシュしない
    "/api/v1/auth/*": {
        "ttl": 0,
        "cache_control": "no-store, no-cache, must-revalidate",
        "compress": False,
    },
    
    # ユーザーデータ - 認証付きキャッシュ
    "/api/v1/users/*": {
        "ttl": 300,  # 5分
        "cache_control": "private, max-age=300",
        "compress": True,
        "vary_headers": ["Authorization"],
    },
}


# データベースクエリキャッシング設定
DATABASE_CACHE_CONFIG = {
    # ユーザー関連クエリ
    "user_queries": {
        "ttl": 600,  # 10分
        "max_size": 1000,  # 最大1000件
        "strategy": CacheStrategy.REDIS_ONLY,
    },
    
    # 統計クエリ
    "stats_queries": {
        "ttl": 1800,  # 30分
        "max_size": 100,
        "strategy": CacheStrategy.MEMORY_AND_REDIS,
    },
    
    # 設定データ
    "config_queries": {
        "ttl": 3600,  # 1時間
        "max_size": 50,
        "strategy": CacheStrategy.MEMORY_AND_REDIS,
    },
}


# グローバルインスタンス
cache_config_manager = CacheConfigManager()


def get_cache_config(endpoint: str) -> CacheConfig:
    """エンドポイントのキャッシュ設定を取得"""
    return cache_config_manager.get_config(endpoint)


def should_cache_response(endpoint: str, status_code: int) -> bool:
    """レスポンスをキャッシュすべきかどうかを判定"""
    return cache_config_manager.should_cache_response(endpoint, status_code)


def get_cache_headers(endpoint: str) -> Dict[str, str]:
    """キャッシュ関連ヘッダーを取得"""
    return cache_config_manager.get_cache_headers(endpoint)


def invalidate_cache_pattern(pattern: str) -> list:
    """パターンに一致するキャッシュを無効化"""
    return cache_config_manager.invalidate_pattern(pattern)