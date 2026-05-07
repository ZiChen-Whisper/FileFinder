import os
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import QObject, Signal
from typing import List, Optional
from models import FileItem, SearchQuery, SearchResult, ContentMatch
from utils.path_helper import get_file_info, is_excluded_directory, is_binary_file
from .file_parser import ParserRegistry

logger = logging.getLogger(__name__)

class ContentSearcher(QObject):
    """文件内容搜索引擎（P0阶段仅支持纯文本关键词搜索）"""
    
    progress_updated = Signal(int, int)
    result_found = Signal(object)
    search_completed = Signal(int)

    def __init__(self):
        super().__init__()
        self._parser_registry = ParserRegistry()
        self._canceled = False

    def cancel(self):
        """取消正在进行的搜索"""
        self._canceled = True

    def _collect_files(self, directory: str, query: SearchQuery) -> List[str]:
        """
        收集指定目录下所有待搜索的文件。
        
        Args:
            directory: 目录路径
            query: 搜索查询条件
        
        Returns:
            待搜索文件路径列表
        """
        files = []
        exclude_dirs = query.exclude_dirs
        
        try:
            for root, dirs, filenames in os.walk(directory):
                dirs[:] = [d for d in dirs if not is_excluded_directory(d, exclude_dirs)]
                
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    if is_binary_file(file_path):
                        continue
                    files.append(file_path)
                    
                    if len(files) >= query.max_results:
                        return files
        except Exception as e:
            logger.warning(f"遍历目录失败: {directory}, {type(e).__name__}")
        
        return files

    def _search_file(self, file_path: str, query: SearchQuery) -> Optional[SearchResult]:
        """
        在单个文件中搜索内容。
        
        Args:
            file_path: 文件路径
            query: 搜索查询条件
        
        Returns:
            搜索结果，如果不匹配返回None
        """
        content = self._parser_registry.parse(file_path)
        if not content:
            return None
        
        file_info = get_file_info(file_path)
        if not file_info:
            return None
        
        content_matches = []
        pattern = query.content_query
        flags = re.IGNORECASE if not query.content_case_sensitive else 0
        
        regex = re.compile(re.escape(pattern), flags)
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for match in regex.finditer(line):
                context_before = lines[max(0, line_num - 4):line_num - 1]
                context_after = lines[line_num:min(line_num + 3, len(lines))]
                
                content_matches.append(ContentMatch(
                    line_number=line_num,
                    line_content=line,
                    match_start=match.start(),
                    match_end=match.end(),
                    context_before=context_before,
                    context_after=context_after
                ))
                
                if len(content_matches) >= 10:
                    break
        
        if content_matches:
            return SearchResult(
                file_item=file_info,
                match_reason='content',
                content_matches=content_matches
            )
        
        return None

    def _search_batch(self, files: List[str], query: SearchQuery) -> List[SearchResult]:
        """
        批量搜索文件。
        
        Args:
            files: 文件路径列表
            query: 搜索查询条件
        
        Returns:
            搜索结果列表
        """
        results = []
        if self._canceled:
            return results
        
        for file_path in files:
            if self._canceled:
                break
            if result := self._search_file(file_path, query):
                results.append(result)
        return results

    def search(self, query: SearchQuery):
        """
        执行内容搜索（P0阶段仅支持关键词搜索，正则表达式为P1功能）。
        
        Args:
            query: 搜索查询条件
        """
        self._canceled = False
        
        all_files = []
        for directory in query.include_dirs:
            all_files.extend(self._collect_files(directory, query))
        
        total_files = len(all_files)
        processed = 0
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i in range(0, len(all_files), 100):
                batch = all_files[i:i+100]
                future = executor.submit(self._search_batch, batch, query)
                futures.append(future)
            
            for future in as_completed(futures):
                if self._canceled:
                    executor.shutdown(wait=False)
                    break
                
                results = future.result()
                for result in results:
                    self.result_found.emit(result)
                
                processed += 100
                self.progress_updated.emit(min(processed, total_files), total_files)
        
        self.search_completed.emit(total_files)