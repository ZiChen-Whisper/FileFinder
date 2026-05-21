from typing import List
from models import SearchQuery, SearchResult
from database.db_manager import DatabaseManager
from .name_searcher import search_by_name, get_index_count
from .content_searcher import ContentSearcher

class SearchEngine:
    def __init__(self):
        self._content_searcher = ContentSearcher()
        self._canceled = False

    def cancel(self):
        self._canceled = True
        self._content_searcher.cancel()

    def has_index(self) -> bool:
        return get_index_count() > 0

    def search(self, query: SearchQuery) -> List[SearchResult]:
        self._canceled = False
        results = []

        if not query.has_query:
            return results

        name_results = []
        if query.has_name_query or not query.has_content_query:
            name_results = search_by_name(query)

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

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:query.max_results]
