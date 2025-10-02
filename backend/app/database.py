"""
Database configuration and connection management for Aurora MySQL
Raw SQL implementation without ORM
Aurora MySQL用のデータベース設定と接続管理（生SQL実装、ORMなし）
"""
import logging
from typing import Generator, Optional, Dict, Any, List
import pymysql
from pymysql.cursors import DictCursor
import asyncio
from contextlib import contextmanager
import time

from app.config import settings

logger = logging.getLogger(__name__)

# Connection pool settings / コネクションプール設定
_connection_pool = None
_pool_size = 1 if settings.environment in ["staging", "prod"] else 5


def get_database_config() -> Dict[str, Any]:
    """
    Get database connection configuration
    データベース接続設定を取得
    """
    if not all([settings.db_host, settings.db_name, settings.db_user, settings.db_password]):
        raise ValueError("Database configuration is incomplete")
    
    return {
        'host': settings.db_host,
        'port': settings.db_port,
        'user': settings.db_user,
        'password': settings.db_password,
        'database': settings.db_name,
        'charset': 'utf8mb4',
        'cursorclass': DictCursor,  # 辞書形式でレコードを取得
        'autocommit': False,  # 自動コミット無効
        'connect_timeout': 10,  # 接続タイムアウト
        'read_timeout': 30,  # 読み取りタイムアウト
        'write_timeout': 30  # 書き込みタイムアウト
    }


def create_connection() -> pymysql.Connection:
    """
    Create a new database connection
    新しいデータベース接続を作成
    """
    try:
        config = get_database_config()
        connection = pymysql.connect(**config)
        logger.debug("Database connection created successfully")
        return connection
    except Exception as e:
        logger.error(f"Failed to create database connection: {str(e)}")
        raise


@contextmanager
def get_db_connection():
    """
    Context manager for database connections
    データベース接続用のコンテキストマネージャー
    """
    connection = None
    try:
        connection = create_connection()
        yield connection
    except Exception as e:
        if connection:
            connection.rollback()  # エラー時はロールバック
        logger.error(f"Database connection error: {str(e)}")
        raise
    finally:
        if connection:
            connection.close()  # 必ず接続を閉じる


def get_db():
    """
    FastAPI dependency to get database connection
    """
    with get_db_connection() as connection:
        yield connection


async def check_database_health() -> dict:
    """
    Check database connectivity and return health status
    """
    try:
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 as health_check")
                result = cursor.fetchone()
                
                if result and result['health_check'] == 1:
                    return {
                        "status": "healthy",
                        "message": "Database connection is working"
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "message": "Database query returned unexpected result"
                    }
                    
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }


def execute_query(connection: pymysql.Connection, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """
    Execute a SELECT query and return results
    SELECTクエリを実行して結果を返す
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Query execution failed: {query}, params: {params}, error: {str(e)}")
        raise


def execute_update(connection: pymysql.Connection, query: str, params: Optional[tuple] = None) -> int:
    """
    Execute an INSERT, UPDATE, or DELETE query and return affected rows
    INSERT、UPDATE、DELETEクエリを実行して影響を受けた行数を返す
    """
    try:
        with connection.cursor() as cursor:
            affected_rows = cursor.execute(query, params)
            connection.commit()  # 変更をコミット
            return affected_rows
    except Exception as e:
        connection.rollback()  # エラー時はロールバック
        logger.error(f"Update execution failed: {query}, params: {params}, error: {str(e)}")
        raise


def execute_insert(connection: pymysql.Connection, query: str, params: Optional[tuple] = None) -> int:
    """
    Execute an INSERT query and return the last insert ID
    INSERTクエリを実行して最後に挿入されたIDを返す
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            connection.commit()
            return cursor.lastrowid  # 自動生成されたIDを返す
    except Exception as e:
        connection.rollback()  # エラー時はロールバック
        logger.error(f"Insert execution failed: {query}, params: {params}, error: {str(e)}")
        raise


def execute_transaction(connection: pymysql.Connection, queries: List[tuple]) -> List[Any]:
    """
    Execute multiple queries in a transaction
    queries: List of (query, params) tuples
    """
    results = []
    try:
        with connection.cursor() as cursor:
            for query, params in queries:
                if query.strip().upper().startswith('SELECT'):
                    cursor.execute(query, params)
                    results.append(cursor.fetchall())
                else:
                    affected_rows = cursor.execute(query, params)
                    results.append(affected_rows)
            
            connection.commit()
            return results
    except Exception as e:
        connection.rollback()
        logger.error(f"Transaction execution failed: {str(e)}")
        raise