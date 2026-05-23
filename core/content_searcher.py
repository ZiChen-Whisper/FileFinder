import os
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import QObject, Signal
from typing import List, Optional, Tuple
from models import FileItem, SearchQuery, SearchResult, ContentMatch
from utils.path_helper import get_file_info, is_excluded_directory
from .file_parser import ParserRegistry

logger = logging.getLogger(__name__)

# 内容搜索文件大小限制 (10MB)
MAX_CONTENT_FILE_SIZE = 10 * 1024 * 1024

# 搜索批次大小
BATCH_SIZE = 50


class ContentSearcher(QObject):
    """文件内容搜索引擎，支持 FTS5 索引搜索和实时扫描两种模式。

    搜索策略：
    1. 优先使用 FTS5 全文索引搜索（毫秒级响应）
    2. 无索引时回退到实时扫描（多线程逐文件搜索）

    实时扫描优化策略：
    1. 使用 os.scandir 替代 os.walk + os.path.getsize，利用 DirEntry 缓存的 stat 信息
    2. 字面量预过滤：先用简单字符串包含检查快速排除不匹配文件
    3. 逐文件粒度提交任务，实现更均衡的负载分配和更精确的进度报告
    4. 实时发射搜索进度信号，包括当前正在搜索的文件路径
    """

    progress_updated = Signal(int, int)       # (已处理文件数, 总文件数)
    result_found = Signal(object)             # 单个 SearchResult
    file_searching = Signal(str)              # 当前正在搜索的文件路径
    search_completed = Signal(int)            # 搜索的文件总数

    def __init__(self):
        super().__init__()
        self._parser_registry = ParserRegistry()
        self._canceled = False

    def cancel(self):
        """取消正在进行的搜索"""
        self._canceled = True

    def _collect_files(self, directory: str, query: SearchQuery) -> List[str]:
        """收集指定目录下所有待搜索的文件。

        使用 os.scandir 递归遍历，利用 DirEntry 缓存的 stat 信息
        避免重复系统调用，比 os.walk + os.path.getsize 更高效。

        Args:
            directory: 目录路径
            query: 搜索查询条件

        Returns:
            待搜索文件路径列表
        """
        files = []
        exclude_dirs = query.exclude_dirs
        searchable_exts = self._parser_registry.get_all_supported_extensions()

        try:
            self._collect_files_recursive(
                directory, exclude_dirs, searchable_exts,
                query.max_results, files
            )
        except Exception as e:
            logger.warning(f"遍历目录失败: {directory}, {type(e).__name__}")

        return files

    def _collect_files_recursive(
        self,
        directory: str,
        exclude_dirs: list,
        searchable_exts: set,
        max_results: int,
        files: List[str]
    ) -> None:
        """递归收集文件（使用 os.scandir 提高性能）

        Args:
            directory: 当前遍历的目录
            exclude_dirs: 排除的目录名列表
            searchable_exts: 可搜索的扩展名集合
            max_results: 最大结果数
            files: 收集到的文件路径列表（就地修改）
        """
        try:
            with os.scandir(directory) as it:
                for entry in it:
                    if self._canceled:
                        return

                    try:
                        if entry.is_dir(follow_symlinks=False):
                            if not is_excluded_directory(entry.name, exclude_dirs):
                                self._collect_files_recursive(
                                    entry.path, exclude_dirs, searchable_exts,
                                    max_results, files
                                )
                        elif entry.is_file(follow_symlinks=False):
                            # 跳过 Office 临时文件（以 ~$ 开头）
                            if entry.name.startswith('~$'):
                                continue
                            ext = os.path.splitext(entry.name)[1].lower()
                            if ext not in searchable_exts:
                                continue

                            # 利用 DirEntry 缓存的 stat 信息，避免额外系统调用
                            try:
                                stat = entry.stat(follow_symlinks=False)
                                if stat.st_size > MAX_CONTENT_FILE_SIZE:
                                    continue
                            except OSError:
                                continue

                            files.append(entry.path)
                            if len(files) >= max_results:
                                return
                    except OSError:
                        continue
        except PermissionError:
            logger.debug(f"无权限访问目录: {directory}")
        except OSError as e:
            logger.debug(f"遍历目录失败: {directory}, {type(e).__name__}")

    def _quick_text_check(self, content: str, pattern: str, case_sensitive: bool) -> bool:
        """快速检查文本是否可能包含关键词，避免不必要的正则搜索。

        使用 Python 内置的 in 操作符进行预过滤，比正则匹配快 5-10 倍。

        Args:
            content: 文件文本内容
            pattern: 搜索关键词
            case_sensitive: 是否区分大小写

        Returns:
            文本是否可能包含关键词
        """
        if case_sensitive:
            return pattern in content
        return pattern.lower() in content.lower()

    def _search_text_in_content(self, content: str, query: SearchQuery) -> List[ContentMatch]:
        """在文本内容中搜索关键词，返回匹配列表（用于 FTS5 索引搜索的上下文提取）。

        Args:
            content: 文件文本内容
            query: 搜索查询条件

        Returns:
            匹配列表
        """
        pattern = query.content_query

        # 快速预过滤
        if not self._quick_text_check(content, pattern, query.content_case_sensitive):
            return []

        matches = []
        flags = re.IGNORECASE if not query.content_case_sensitive else 0
        regex = re.compile(re.escape(pattern), flags)

        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for match in regex.finditer(line):
                context_before = lines[max(0, line_num - 4):line_num - 1]
                context_after = lines[line_num:min(line_num + 3, len(lines))]

                matches.append(ContentMatch(
                    line_number=line_num,
                    line_content=line,
                    match_start=match.start(),
                    match_end=match.end(),
                    context_before=context_before,
                    context_after=context_after
                ))

                if len(matches) >= 10:
                    return matches

        return matches

    def _search_text_file(self, file_path: str, content: str,
                          query: SearchQuery) -> List[ContentMatch]:
        """在纯文本内容中搜索关键词，返回匹配列表。

        先用快速字符串检查过滤不包含关键词的文件，
        再用正则逐行精确匹配并提取上下文。

        Args:
            file_path: 文件路径
            content: 文件文本内容
            query: 搜索查询条件

        Returns:
            匹配列表
        """
        return self._search_text_in_content(content, query)

    def _search_pdf_file(self, file_path: str,
                         query: SearchQuery) -> List[ContentMatch]:
        """在 PDF 文件中逐页搜索关键词，返回匹配列表。

        使用 fitz 原生 search_for() 进行 C 级别快速搜索，
        仅对匹配页面提取文本用于上下文展示。

        Args:
            file_path: PDF 文件路径
            query: 搜索查询条件

        Returns:
            匹配列表
        """
        matches = []
        try:
            import fitz
        except ImportError:
            return matches

        pattern = query.content_query

        try:
            doc = fitz.open(file_path)
        except Exception as e:
            logger.warning(f"PDF 打开失败: {file_path}, {type(e).__name__}: {e}")
            return matches

        try:
            for page_idx in range(len(doc)):
                if self._canceled:
                    break

                try:
                    page = doc[page_idx]
                except Exception as e:
                    logger.debug(f"PDF 页面读取失败: {file_path} 页{page_idx}, {e}")
                    continue

                # 使用 fitz 原生 search_for 进行 C 级别快速搜索
                try:
                    found_rects = page.search_for(pattern)
                except Exception:
                    found_rects = []

                if not found_rects:
                    continue

                # 仅在匹配页面提取文本，用于上下文展示
                try:
                    page_text = page.get_text("text")
                except Exception:
                    page_text = ""

                rects = [(r.x0, r.y0, r.x1, r.y1) for r in found_rects]

                if not page_text:
                    # 无法提取文本时，仅记录矩形坐标
                    for i, rect in enumerate(rects):
                        matches.append(ContentMatch(
                            line_number=i + 1,
                            line_content="",
                            match_start=0,
                            match_end=0,
                            context_before=[],
                            context_after=[],
                            page_number=page_idx + 1,
                            page_rect=rect
                        ))
                        if len(matches) >= 10:
                            doc.close()
                            return matches
                    continue

                # 在提取的文本中逐行匹配，获取精确位置和上下文
                flags = re.IGNORECASE if not query.content_case_sensitive else 0
                regex = re.compile(re.escape(pattern), flags)

                lines = page_text.split('\n')
                rect_idx = 0
                for line_num, line in enumerate(lines, 1):
                    for match in regex.finditer(line):
                        rect = ()
                        if rect_idx < len(rects):
                            rect = rects[rect_idx]
                            rect_idx += 1

                        context_before = lines[max(0, line_num - 4):line_num - 1]
                        context_after = lines[line_num:min(line_num + 3, len(lines))]

                        matches.append(ContentMatch(
                            line_number=line_num,
                            line_content=line,
                            match_start=match.start(),
                            match_end=match.end(),
                            context_before=context_before,
                            context_after=context_after,
                            page_number=page_idx + 1,
                            page_rect=rect
                        ))

                        if len(matches) >= 10:
                            doc.close()
                            return matches
        except Exception as e:
            logger.warning(f"PDF 搜索异常: {file_path}, {type(e).__name__}: {e}")
        finally:
            try:
                doc.close()
            except Exception:
                pass

        return matches

    def _search_file(self, file_path: str, query: SearchQuery) -> Optional[SearchResult]:
        """在单个文件中搜索内容。

        优化：确认匹配后再获取文件信息，
        避免对不匹配文件执行昂贵的 stat 调用。

        Args:
            file_path: 文件路径
            query: 搜索查询条件

        Returns:
            搜索结果，如果不匹配返回None
        """
        ext = os.path.splitext(file_path)[1].lower()

        # PDF 文件使用专门的逐页搜索
        if ext == '.pdf':
            content_matches = self._search_pdf_file(file_path, query)
        else:
            content = self._parser_registry.parse(file_path)
            if not content:
                return None
            content_matches = self._search_text_file(file_path, content, query)

        if not content_matches:
            return None

        # 确认匹配后才获取文件信息，避免对不匹配文件的 stat 开销
        file_info = get_file_info(file_path)
        if not file_info:
            return None

        return SearchResult(
            file_item=file_info,
            match_reason='content',
            content_matches=content_matches
        )

    def _search_single(self, file_path: str, query: SearchQuery) -> Tuple[Optional[SearchResult], str]:
        """搜索单个文件，返回结果和文件路径（用于进度追踪）

        Args:
            file_path: 文件路径
            query: 搜索查询条件

        Returns:
            (搜索结果或None, 文件路径)
        """
        try:
            result = self._search_file(file_path, query)
            return result, file_path
        except Exception as e:
            logger.debug(f"搜索文件失败: {file_path}, {type(e).__name__}: {e}")
            return None, file_path

    def search_by_index(self, query: SearchQuery) -> List[SearchResult]:
        """使用 FTS5 全文索引搜索，毫秒级响应。

        流程：
        1. 对查询文本做 jieba 分词
        2. FTS5 MATCH 搜索获取匹配文件路径
        3. 对每个匹配文件，从索引中获取原始内容提取上下文行

        Args:
            query: 搜索查询条件

        Returns:
            搜索结果列表
        """
        from database.db_manager import DatabaseManager
        from utils.tokenizer import tokenize_query_for_fts5

        db = DatabaseManager()

        # 对查询文本分词
        query_tokenized = tokenize_query_for_fts5(query.content_query)
        if not query_tokenized:
            self.search_completed.emit(0)
            return []

        # FTS5 搜索
        matched = db.search_content(query_tokenized, max_results=query.max_results)
        if not matched:
            self.search_completed.emit(0)
            return []

        results = []
        total = len(matched)
        for i, (file_path, fts_score) in enumerate(matched):
            if self._canceled:
                break

            self.file_searching.emit(file_path)

            # 从索引中获取原始内容
            content_text = db.get_content_by_path(file_path)

            content_matches = []
            if content_text:
                # 提取上下文行
                content_matches = self._search_text_in_content(content_text, query)

            # 如果索引中没有原始内容，尝试实时解析
            if not content_text:
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.pdf':
                    content_matches = self._search_pdf_file(file_path, query)
                else:
                    parsed = self._parser_registry.parse(file_path)
                    if parsed:
                        content_matches = self._search_text_file(file_path, parsed, query)

            if not content_matches and not content_text:
                # FTS5 匹配但无法提取上下文，仍然返回结果（无上下文）
                pass

            file_info = get_file_info(file_path)
            if not file_info:
                continue

            result = SearchResult(
                file_item=file_info,
                match_reason='content',
                content_matches=content_matches
            )
            results.append(result)

            self.progress_updated.emit(i + 1, total)
            self.result_found.emit(result)

        self.search_completed.emit(total)
        return results

    def search_realtime(self, query: SearchQuery) -> List[SearchResult]:
        """实时扫描搜索（无索引时的回退方案）。

        多线程逐文件搜索，支持纯文本/代码文件和 PDF 文件的关键词搜索。

        Args:
            query: 搜索查询条件

        Returns:
            搜索结果列表
        """
        # 收集待搜索文件
        all_files = []
        for directory in query.include_dirs:
            if self._canceled:
                break
            all_files.extend(self._collect_files(directory, query))

        total_files = len(all_files)
        processed = 0
        all_results: List[SearchResult] = []

        if total_files == 0:
            self.search_completed.emit(0)
            return all_results

        # 使用 CPU 核心数作为线程数，至少4个，最多不超过8个
        max_workers = min(max(os.cpu_count() or 4, 4), 8)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 逐文件提交任务，实现更均衡的负载分配和更精确的进度
            futures = {}
            for file_path in all_files:
                if self._canceled:
                    break
                future = executor.submit(self._search_single, file_path, query)
                futures[future] = file_path

            try:
                for future in as_completed(futures, timeout=120):
                    if self._canceled:
                        executor.shutdown(wait=False, cancel_futures=True)
                        break

                    try:
                        result, file_path = future.result(timeout=30)
                    except Exception as e:
                        logger.warning(f"搜索文件异常: {type(e).__name__}: {e}")
                        processed += 1
                        self.progress_updated.emit(processed, total_files)
                        continue

                    # 发射当前正在搜索的文件路径信号
                    self.file_searching.emit(file_path)

                    if result:
                        self.result_found.emit(result)
                        all_results.append(result)

                    processed += 1
                    self.progress_updated.emit(processed, total_files)
            except TimeoutError:
                logger.warning("内容搜索超时，返回已获取的结果")
                executor.shutdown(wait=False, cancel_futures=True)

        self.search_completed.emit(total_files)
        return all_results

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """执行内容搜索，优先使用 FTS5 索引，无索引时回退到实时扫描。

        Args:
            query: 搜索查询条件

        Returns:
            搜索结果列表
        """
        self._canceled = False

        from database.db_manager import DatabaseManager
        db = DatabaseManager()

        # 优先使用 FTS5 索引
        if db.has_content_index():
            logger.info("使用 FTS5 全文索引搜索")
            return self.search_by_index(query)

        # 回退到实时扫描
        logger.info("无内容索引，使用实时扫描搜索")
        return self.search_realtime(query)
