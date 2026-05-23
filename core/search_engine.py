from typing import List
from models import SearchQuery, SearchResult
from database.db_manager import DatabaseManager
from .name_searcher import search_by_name, get_index_count
from .content_searcher import ContentSearcher


class SearchEngine:
    """搜索调度引擎，支持文件名搜索、内容搜索和联合搜索。

    内容搜索策略：
    - 有 FTS5 全文索引时：使用索引搜索（毫秒级）
    - 无索引时：回退到实时扫描（多线程逐文件搜索）
    """

    def __init__(self):
        self._content_searcher = ContentSearcher()
        self._canceled = False

    def cancel(self):
        self._canceled = True
        self._content_searcher.cancel()

    def has_index(self) -> bool:
        return get_index_count() > 0

    def has_content_index(self) -> bool:
        """检查是否存在内容全文索引。"""
        db = DatabaseManager()
        return db.has_content_index()

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """执行搜索，支持文件名搜索、内容搜索和联合搜索。

        联合搜索（同时有文件名和内容查询）时：
        - 有内容索引：分别搜索文件名和内容，取交集
        - 无内容索引：先搜索文件名缩小范围，再在结果中搜索内容

        Args:
            query: 搜索查询条件

        Returns:
            搜索结果列表
        """
        self._canceled = False
        results = []

        if not query.has_query:
            return results

        name_results = []
        if query.has_name_query or not query.has_content_query:
            name_results = search_by_name(query)

        if self._canceled:
            return results

        if query.has_content_query:
            # 直接获取返回值，避免信号跨线程导致结果丢失
            content_results = self._content_searcher.search(query)

            if query.has_name_query:
                name_paths = {item.path for _, item in name_results}
                filtered = [r for r in content_results if r.file_item.path in name_paths]
                results = filtered
            else:
                results = content_results
        else:
            results = [SearchResult(file_item=item, match_reason='name', name_match_score=score)
                       for score, item in name_results]

        if self._canceled:
            return []

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:query.max_results]
