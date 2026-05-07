from typing import List, Optional
from models import FileItem, SearchQuery, SearchResult
from .name_searcher import search_by_name
from .content_searcher import ContentSearcher

class SearchEngine:
    def __init__(self):
        self._content_searcher = ContentSearcher()
        self._canceled = False

    def cancel(self):
        self._canceled = True
        self._content_searcher.cancel()

    def search(self, query: SearchQuery) -> List[SearchResult]:
        self._canceled = False
        results = []
        
        if not query.has_query:
            return results
        
        if not query.include_dirs:
            query.include_dirs = ['~']
        
        name_results = []
        if query.has_name_query:
            for directory in query.include_dirs:
                if self._canceled:
                    break
                files = search_by_name(directory, query)
                name_results.extend(files)
        
        if query.has_content_query:
            content_results = []
            self._content_searcher.result_found.connect(
                lambda r: content_results.append(r) if not self._canceled else None
            )
            self._content_searcher.search(query)
            
            if query.has_name_query:
                name_paths = {f.path for f in name_results}
                filtered = [r for r in content_results if r.file_item.path in name_paths]
                results = filtered
            else:
                results = content_results
        else:
            results = [SearchResult(file_item=f, match_reason='name') for f in name_results]
        
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:query.max_results]