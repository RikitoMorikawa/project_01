"""
Base repository class with common CRUD operations using raw SQL
生SQLを使用した共通CRUD操作を持つベースリポジトリクラス
"""
from typing import Optional, List, Dict, Any
import pymysql
import logging
from datetime import datetime

from app.database import execute_query, execute_update, execute_insert, execute_transaction
from app.exceptions import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)


class BaseRepository:
    """
    Base repository class with common CRUD operations using raw SQL
    生SQLを使用した共通CRUD操作を持つベースリポジトリクラス
    """
    
    def __init__(self, connection: pymysql.Connection, table_name: str):
        self.connection = connection  # データベース接続
        self.table_name = table_name  # 対象テーブル名
    
    def get(self, id: int) -> Optional[Dict[str, Any]]:
        """Get a single record by ID / IDで単一レコードを取得"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE id = %s"
            results = execute_query(self.connection, query, (id,))
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Database error in get({id}): {str(e)}")
            raise DatabaseError(f"Failed to retrieve record from {self.table_name}")
    
    def get_by_field(self, field_name: str, value: Any) -> Optional[Dict[str, Any]]:
        """Get a single record by field value / フィールド値で単一レコードを取得"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE {field_name} = %s"
            results = execute_query(self.connection, query, (value,))
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Database error in get_by_field({field_name}={value}): {str(e)}")
            raise DatabaseError(f"Failed to retrieve record from {self.table_name}")
    
    def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get multiple records with pagination and filtering / ページネーションとフィルタリングで複数レコードを取得"""
        try:
            query = f"SELECT * FROM {self.table_name}"
            params = []
            
            # Apply filters / フィルタを適用
            if filters:
                where_conditions = []
                for field_name, value in filters.items():
                    if isinstance(value, list):
                        placeholders = ','.join(['%s'] * len(value))
                        where_conditions.append(f"{field_name} IN ({placeholders})")
                        params.extend(value)
                    else:
                        where_conditions.append(f"{field_name} = %s")
                        params.append(value)
                
                if where_conditions:
                    query += " WHERE " + " AND ".join(where_conditions)
            
            # Apply ordering / ソート順を適用
            if order_by:
                query += f" ORDER BY {order_by}"
            
            # Apply pagination / ページネーションを適用
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, skip])
            
            return execute_query(self.connection, query, tuple(params))
            
        except Exception as e:
            logger.error(f"Database error in get_multi: {str(e)}")
            raise DatabaseError(f"Failed to retrieve records from {self.table_name}")
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering"""
        try:
            query = f"SELECT COUNT(*) as count FROM {self.table_name}"
            params = []
            
            # Apply filters
            if filters:
                where_conditions = []
                for field_name, value in filters.items():
                    if isinstance(value, list):
                        placeholders = ','.join(['%s'] * len(value))
                        where_conditions.append(f"{field_name} IN ({placeholders})")
                        params.extend(value)
                    else:
                        where_conditions.append(f"{field_name} = %s")
                        params.append(value)
                
                if where_conditions:
                    query += " WHERE " + " AND ".join(where_conditions)
            
            results = execute_query(self.connection, query, tuple(params) if params else None)
            return results[0]['count'] if results else 0
            
        except Exception as e:
            logger.error(f"Database error in count: {str(e)}")
            raise DatabaseError(f"Failed to count records from {self.table_name}")
    
    def create(self, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record / 新しいレコードを作成"""
        try:
            # Add timestamps / タイムスタンプを追加
            now = datetime.utcnow()
            obj_in['created_at'] = now
            obj_in['updated_at'] = now
            
            # Build INSERT query / INSERTクエリを構築
            fields = list(obj_in.keys())
            placeholders = ', '.join(['%s'] * len(fields))
            query = f"INSERT INTO {self.table_name} ({', '.join(fields)}) VALUES ({placeholders})"
            
            # Execute insert and get the new ID / 挿入を実行して新しいIDを取得
            new_id = execute_insert(self.connection, query, tuple(obj_in.values()))
            
            # Return the created record / 作成されたレコードを返す
            return self.get(new_id)
            
        except Exception as e:
            logger.error(f"Database error in create: {str(e)}")
            raise DatabaseError(f"Failed to create record in {self.table_name}")
    
    def update(self, id: int, obj_in: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing record"""
        try:
            # Check if record exists
            existing = self.get(id)
            if not existing:
                raise NotFoundError(self.table_name, str(id))
            
            # Add updated timestamp
            obj_in['updated_at'] = datetime.utcnow()
            
            # Build UPDATE query
            set_clauses = [f"{field} = %s" for field in obj_in.keys()]
            query = f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE id = %s"
            
            # Execute update
            params = list(obj_in.values()) + [id]
            execute_update(self.connection, query, tuple(params))
            
            # Return updated record
            return self.get(id)
            
        except Exception as e:
            logger.error(f"Database error in update({id}): {str(e)}")
            raise DatabaseError(f"Failed to update record in {self.table_name}")
    
    def delete(self, id: int) -> bool:
        """Delete a record by ID"""
        try:
            # Check if record exists
            existing = self.get(id)
            if not existing:
                raise NotFoundError(self.table_name, str(id))
            
            query = f"DELETE FROM {self.table_name} WHERE id = %s"
            affected_rows = execute_update(self.connection, query, (id,))
            
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"Database error in delete({id}): {str(e)}")
            raise DatabaseError(f"Failed to delete record from {self.table_name}")
    
    def exists(self, id: int) -> bool:
        """Check if a record exists by ID"""
        try:
            query = f"SELECT 1 FROM {self.table_name} WHERE id = %s LIMIT 1"
            results = execute_query(self.connection, query, (id,))
            return len(results) > 0
        except Exception as e:
            logger.error(f"Database error in exists({id}): {str(e)}")
            raise DatabaseError(f"Failed to check existence in {self.table_name}")
    
    def bulk_create(self, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple records in bulk"""
        try:
            created_records = []
            now = datetime.utcnow()
            
            for obj in objects:
                obj['created_at'] = now
                obj['updated_at'] = now
                created_record = self.create(obj)
                created_records.append(created_record)
            
            return created_records
            
        except Exception as e:
            logger.error(f"Database error in bulk_create: {str(e)}")
            raise DatabaseError(f"Failed to bulk create records in {self.table_name}")