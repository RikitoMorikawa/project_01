"""
最適化されたベースリポジトリ

データベースクエリの最適化、バッチ処理、キャッシングを提供する
"""

from typing import List, Dict, Any, Optional, Union, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, update, delete, func, text
from sqlalchemy.sql import Select
import logging
from datetime import datetime, timedelta

from app.repositories.base import BaseRepository
from app.utils.performance import cached_query, monitor_performance

logger = logging.getLogger(__name__)

T = TypeVar('T')


class OptimizedBaseRepository(BaseRepository[T], Generic[T]):
    """
    最適化されたベースリポジトリ
    
    クエリ最適化、バッチ処理、キャッシングを提供する
    """
    
    def __init__(self, model_class: type, session: AsyncSession):
        super().__init__(model_class, session)
        self._batch_size = 100
        self._cache_ttl = 300  # 5分
    
    @monitor_performance("repository_find_by_id")
    @cached_query(ttl=300)
    async def find_by_id_cached(self, id: Any) -> Optional[T]:
        """
        ID による検索（キャッシュ付き）
        
        Args:
            id: エンティティID
            
        Returns:
            エンティティまたは None
        """
        return await super().find_by_id(id)
    
    @monitor_performance("repository_find_all_optimized")
    async def find_all_optimized(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = None,
        filters: Dict[str, Any] = None,
        include_relations: List[str] = None
    ) -> List[T]:
        """
        最適化された全件検索
        
        Args:
            limit: 取得件数制限
            offset: オフセット
            order_by: ソート条件
            filters: フィルタ条件
            include_relations: 含めるリレーション
            
        Returns:
            エンティティリスト
        """
        
        query = select(self.model_class)
        
        # フィルタ条件を適用
        if filters:
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    column = getattr(self.model_class, field)
                    if isinstance(value, list):
                        query = query.where(column.in_(value))
                    elif isinstance(value, dict):
                        # 範囲検索など
                        if 'gte' in value:
                            query = query.where(column >= value['gte'])
                        if 'lte' in value:
                            query = query.where(column <= value['lte'])
                        if 'like' in value:
                            query = query.where(column.like(f"%{value['like']}%"))
                    else:
                        query = query.where(column == value)
        
        # リレーションの事前読み込み
        if include_relations:
            for relation in include_relations:
                if hasattr(self.model_class, relation):
                    # N+1 問題を回避するため selectinload を使用
                    query = query.options(selectinload(getattr(self.model_class, relation)))
        
        # ソート条件を適用
        if order_by:
            if order_by.startswith('-'):
                # 降順
                field = order_by[1:]
                if hasattr(self.model_class, field):
                    query = query.order_by(getattr(self.model_class, field).desc())
            else:
                # 昇順
                if hasattr(self.model_class, order_by):
                    query = query.order_by(getattr(self.model_class, order_by))
        
        # ページネーション
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    @monitor_performance("repository_count_optimized")
    @cached_query(ttl=60)  # カウントは短時間キャッシュ
    async def count_optimized(self, filters: Dict[str, Any] = None) -> int:
        """
        最適化されたカウント取得
        
        Args:
            filters: フィルタ条件
            
        Returns:
            件数
        """
        
        query = select(func.count(self.model_class.id))
        
        # フィルタ条件を適用
        if filters:
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    column = getattr(self.model_class, field)
                    if isinstance(value, list):
                        query = query.where(column.in_(value))
                    elif isinstance(value, dict):
                        if 'gte' in value:
                            query = query.where(column >= value['gte'])
                        if 'lte' in value:
                            query = query.where(column <= value['lte'])
                        if 'like' in value:
                            query = query.where(column.like(f"%{value['like']}%"))
                    else:
                        query = query.where(column == value)
        
        result = await self.session.execute(query)
        return result.scalar()
    
    @monitor_performance("repository_batch_create")
    async def batch_create(self, entities_data: List[Dict[str, Any]]) -> List[T]:
        """
        バッチ作成
        
        Args:
            entities_data: エンティティデータのリスト
            
        Returns:
            作成されたエンティティのリスト
        """
        
        if not entities_data:
            return []
        
        entities = []
        
        # バッチサイズごとに分割して処理
        for i in range(0, len(entities_data), self._batch_size):
            batch = entities_data[i:i + self._batch_size]
            
            batch_entities = []
            for data in batch:
                entity = self.model_class(**data)
                batch_entities.append(entity)
            
            self.session.add_all(batch_entities)
            entities.extend(batch_entities)
        
        await self.session.flush()
        
        logger.info(f"バッチ作成完了: {len(entities)} 件")
        return entities
    
    @monitor_performance("repository_batch_update")
    async def batch_update(
        self, 
        updates: List[Dict[str, Any]], 
        id_field: str = "id"
    ) -> int:
        """
        バッチ更新
        
        Args:
            updates: 更新データのリスト（ID を含む）
            id_field: ID フィールド名
            
        Returns:
            更新された件数
        """
        
        if not updates:
            return 0
        
        updated_count = 0
        
        # バッチサイズごとに分割して処理
        for i in range(0, len(updates), self._batch_size):
            batch = updates[i:i + self._batch_size]
            
            for update_data in batch:
                if id_field not in update_data:
                    continue
                
                entity_id = update_data.pop(id_field)
                
                query = (
                    update(self.model_class)
                    .where(getattr(self.model_class, id_field) == entity_id)
                    .values(**update_data)
                )
                
                result = await self.session.execute(query)
                updated_count += result.rowcount
        
        logger.info(f"バッチ更新完了: {updated_count} 件")
        return updated_count
    
    @monitor_performance("repository_batch_delete")
    async def batch_delete(self, ids: List[Any]) -> int:
        """
        バッチ削除
        
        Args:
            ids: 削除する ID のリスト
            
        Returns:
            削除された件数
        """
        
        if not ids:
            return 0
        
        deleted_count = 0
        
        # バッチサイズごとに分割して処理
        for i in range(0, len(ids), self._batch_size):
            batch_ids = ids[i:i + self._batch_size]
            
            query = delete(self.model_class).where(
                self.model_class.id.in_(batch_ids)
            )
            
            result = await self.session.execute(query)
            deleted_count += result.rowcount
        
        logger.info(f"バッチ削除完了: {deleted_count} 件")
        return deleted_count
    
    @monitor_performance("repository_find_with_pagination")
    async def find_with_pagination(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Dict[str, Any] = None,
        order_by: str = None,
        include_relations: List[str] = None
    ) -> Dict[str, Any]:
        """
        ページネーション付き検索
        
        Args:
            page: ページ番号（1から開始）
            per_page: 1ページあたりの件数
            filters: フィルタ条件
            order_by: ソート条件
            include_relations: 含めるリレーション
            
        Returns:
            ページネーション情報を含む結果
        """
        
        # 総件数を取得
        total_count = await self.count_optimized(filters)
        
        # オフセットを計算
        offset = (page - 1) * per_page
        
        # データを取得
        items = await self.find_all_optimized(
            limit=per_page,
            offset=offset,
            filters=filters,
            order_by=order_by,
            include_relations=include_relations
        )
        
        # ページネーション情報を計算
        total_pages = (total_count + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "items": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }
    
    @monitor_performance("repository_search_optimized")
    async def search_optimized(
        self,
        search_term: str,
        search_fields: List[str],
        limit: int = 50,
        filters: Dict[str, Any] = None
    ) -> List[T]:
        """
        最適化された検索
        
        Args:
            search_term: 検索語
            search_fields: 検索対象フィールド
            limit: 取得件数制限
            filters: 追加フィルタ条件
            
        Returns:
            検索結果
        """
        
        query = select(self.model_class)
        
        # 検索条件を構築
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model_class, field):
                column = getattr(self.model_class, field)
                search_conditions.append(
                    column.like(f"%{search_term}%")
                )
        
        if search_conditions:
            from sqlalchemy import or_
            query = query.where(or_(*search_conditions))
        
        # 追加フィルタ条件を適用
        if filters:
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    column = getattr(self.model_class, field)
                    query = query.where(column == value)
        
        # 関連性でソート（検索語の出現頻度など）
        # 実際の実装では全文検索エンジンの使用を推奨
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    @monitor_performance("repository_aggregate")
    async def aggregate(
        self,
        aggregations: Dict[str, str],
        group_by: List[str] = None,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        集計クエリ
        
        Args:
            aggregations: 集計関数の辞書 {"field": "function"}
            group_by: グループ化フィールド
            filters: フィルタ条件
            
        Returns:
            集計結果
        """
        
        # 集計フィールドを構築
        select_fields = []
        
        if group_by:
            for field in group_by:
                if hasattr(self.model_class, field):
                    select_fields.append(getattr(self.model_class, field))
        
        for field, function in aggregations.items():
            if hasattr(self.model_class, field):
                column = getattr(self.model_class, field)
                
                if function.lower() == 'count':
                    select_fields.append(func.count(column).label(f"{field}_{function}"))
                elif function.lower() == 'sum':
                    select_fields.append(func.sum(column).label(f"{field}_{function}"))
                elif function.lower() == 'avg':
                    select_fields.append(func.avg(column).label(f"{field}_{function}"))
                elif function.lower() == 'max':
                    select_fields.append(func.max(column).label(f"{field}_{function}"))
                elif function.lower() == 'min':
                    select_fields.append(func.min(column).label(f"{field}_{function}"))
        
        query = select(*select_fields)
        
        # フィルタ条件を適用
        if filters:
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    column = getattr(self.model_class, field)
                    query = query.where(column == value)
        
        # グループ化
        if group_by:
            for field in group_by:
                if hasattr(self.model_class, field):
                    query = query.group_by(getattr(self.model_class, field))
        
        result = await self.session.execute(query)
        
        # 結果を辞書形式に変換
        results = []
        for row in result:
            row_dict = {}
            for i, column in enumerate(result.keys()):
                row_dict[column] = row[i]
            results.append(row_dict)
        
        return results
    
    async def explain_query(self, query: Select) -> str:
        """
        クエリの実行計画を取得
        
        Args:
            query: SQLAlchemy クエリ
            
        Returns:
            実行計画
        """
        
        # クエリを文字列に変換
        compiled_query = query.compile(
            dialect=self.session.bind.dialect,
            compile_kwargs={"literal_binds": True}
        )
        
        # EXPLAIN を実行
        explain_query = text(f"EXPLAIN {compiled_query}")
        result = await self.session.execute(explain_query)
        
        explain_result = []
        for row in result:
            explain_result.append(str(row[0]))
        
        return "\n".join(explain_result)
    
    async def optimize_table(self):
        """
        テーブルの最適化を実行
        
        注意: 本番環境では慎重に実行すること
        """
        
        table_name = self.model_class.__tablename__
        
        try:
            # MySQL の場合
            optimize_query = text(f"OPTIMIZE TABLE {table_name}")
            await self.session.execute(optimize_query)
            
            logger.info(f"テーブル最適化完了: {table_name}")
            
        except Exception as e:
            logger.warning(f"テーブル最適化エラー: {table_name} - {str(e)}")
    
    def set_batch_size(self, batch_size: int):
        """バッチサイズを設定"""
        self._batch_size = max(1, min(batch_size, 1000))  # 1-1000 の範囲で制限
    
    def set_cache_ttl(self, ttl: int):
        """キャッシュ TTL を設定"""
        self._cache_ttl = max(0, ttl)