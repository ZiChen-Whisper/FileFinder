import os
import logging

from PySide6.QtCore import QThread, Signal

from config import SCAN_STATUS_COMPLETE, SCAN_STATUS_INCOMPLETE, SCAN_STATUS_FAILED, SCAN_STATUS_SCANNING, set_scan_status
from constants import SKIP_DIR_NAMES, BATCH_SIZE, CONTENT_INDEX_BATCH_SIZE, SCAN_PROGRESS_INTERVAL, FILE_LOG_INTERVAL, FILE_LOG_BATCH_SIZE

logger = logging.getLogger(__name__)


class ScanWorker(QThread):
    progress = Signal(int, int, str)
    finished = Signal(int, float)
    error = Signal(str)
    dir_completed = Signal(str)
    dir_scanned = Signal(str)
    file_found = Signal(str)
    # 内容索引阶段信号：(已索引文件数, 总文件数, 当前文件路径)
    content_index_progress = Signal(int, int, str)

    def __init__(self, search_dirs, exclude_dirs, parent=None):
        super().__init__(parent)
        self._search_dirs = search_dirs
        self._exclude_dirs = set(
            os.path.normpath(d).lower() for d in (exclude_dirs or [])
        )
        self._cancelled = False
        self._last_progress_time = 0
        self._progress_interval = SCAN_PROGRESS_INTERVAL
        self._batch_size = BATCH_SIZE
        self._total_dirs = 0
        self._file_log_batch = []
        self._file_log_interval = FILE_LOG_INTERVAL
        self._last_file_log_time = 0

    def cancel(self):
        self._cancelled = True

    def _should_skip_dir(self, name, full_path):
        if name in SKIP_DIR_NAMES:
            return True
        if name.startswith('.') or name.startswith('$'):
            return True
        normalized = os.path.normpath(full_path).lower()
        for exc in self._exclude_dirs:
            if normalized == exc or normalized.startswith(exc + os.sep):
                return True
        return False

    def _pre_scan_count_dirs(self, normalized_dirs):
        total = 0
        for base_dir in normalized_dirs:
            if self._cancelled:
                return 0
            if not os.path.isdir(base_dir):
                continue
            for root, dirs, _ in os.walk(base_dir, onerror=lambda e: None):
                if self._cancelled:
                    return 0
                dirs[:] = [
                    d for d in dirs
                    if not self._should_skip_dir(d, os.path.join(root, d))
                ]
                total += len(dirs) + 1
        return total

    def _index_file_contents(self, db, normalized_dirs):
        """阶段2：为已扫描的文件建立内容全文索引。

        遍历 file_index_cache 中本次扫描路径下的文件，
        使用 ParserRegistry 提取文本内容，jieba 分词后写入 FTS5。

        Args:
            db: DatabaseManager 实例
            normalized_dirs: 已规范化的扫描目录列表
        """
        import time
        from core.file_parser import ParserRegistry
        from utils.tokenizer import tokenize_for_fts5

        parser_registry = ParserRegistry()
        supported_exts = parser_registry.get_all_supported_extensions()

        # 获取需要索引的文件列表（排除已有索引的文件）
        files_to_index = []
        for d in normalized_dirs:
            if self._cancelled:
                return
            rows = db.get_files_for_content_indexing(d)
            for row in rows:
                ext = row["extension"] or ""
                if ext.lower() in supported_exts:
                    files_to_index.append((row["path"], row["name"]))

        total = len(files_to_index)
        if total == 0:
            return

        self.content_index_progress.emit(0, total, "正在准备内容索引...")

        indexed = 0
        batch = []
        batch_size = CONTENT_INDEX_BATCH_SIZE  # 内容索引批量大小（每条内容较大，不宜过大）
        last_progress_time = time.time()

        for file_path, file_name in files_to_index:
            if self._cancelled:
                break

            try:
                # 使用 ParserRegistry 提取文本内容
                content_text = parser_registry.parse(file_path)
                if not content_text or not content_text.strip():
                    indexed += 1
                    continue

                # jieba 分词
                content_tokenized = tokenize_for_fts5(content_text)
                if not content_tokenized:
                    indexed += 1
                    continue

                batch.append((file_path, file_name, content_text, content_tokenized))

                if len(batch) >= batch_size:
                    db.insert_content_batch(batch)
                    batch.clear()

                indexed += 1
                now = time.time()
                if now - last_progress_time >= self._progress_interval:
                    last_progress_time = now
                    self.content_index_progress.emit(indexed, total, file_path)

            except Exception as e:
                logger.debug(f"内容索引失败: {file_path}, {type(e).__name__}")
                indexed += 1
                continue

        # 写入剩余批次
        if batch:
            db.insert_content_batch(batch)

        self.content_index_progress.emit(indexed, total, "内容索引完成")

    def run(self):
        import time
        start_time = time.time()
        try:
            from database.db_manager import DatabaseManager
            from utils.path_helper import normalize_path

            db = DatabaseManager()

            normalized_dirs = [normalize_path(d) for d in self._search_dirs]

            # 只清除当前扫描目录的索引，保留其他目录的索引
            for d in normalized_dirs:
                db.delete_entries_by_prefix(d)

            for d in normalized_dirs:
                set_scan_status(d, SCAN_STATUS_SCANNING)

            self.progress.emit(0, 0, "准备扫描...")

            self.progress.emit(0, 0, "正在统计目录数量...")
            self._total_dirs = self._pre_scan_count_dirs(normalized_dirs)
            if self._cancelled:
                for d in normalized_dirs:
                    set_scan_status(d, SCAN_STATUS_INCOMPLETE)
                # 取消时只清除当前扫描目录的索引
                for d in normalized_dirs:
                    db.delete_entries_by_prefix(d)
                return

            total_files = 0
            visited_dirs = 0
            batch = []
            dir_sizes = {}
            dir_count = 0
            file_count = 0
            current_dir_display = ""

            # ===== 阶段1：扫描文件元数据 =====
            for base_dir in normalized_dirs:
                if self._cancelled:
                    break
                if not os.path.isdir(base_dir):
                    logger.warning(f"扫描目录不存在，跳过: {base_dir}")
                    continue

                for root, dirs, files in os.walk(base_dir, onerror=lambda e: None):
                    if self._cancelled:
                        break
                    dirs[:] = [
                        d for d in dirs
                        if not self._should_skip_dir(d, os.path.join(root, d))
                    ]

                    visited_dirs += 1
                    current_dir_display = root

                    if self._total_dirs > 0:
                        pct = min(int(visited_dirs / self._total_dirs * 100), 99)
                    else:
                        pct = 0

                    for d in dirs:
                        if self._cancelled:
                            break
                        try:
                            dir_path = os.path.join(root, d)
                            try:
                                dir_items = os.listdir(dir_path)
                                item_count = len(dir_items)
                            except (PermissionError, OSError):
                                item_count = 0
                            try:
                                dir_stat = os.stat(dir_path)
                                dir_mtime = dir_stat.st_mtime
                            except (PermissionError, OSError):
                                dir_mtime = 0
                            batch.append((dir_path, d, None, 0, dir_mtime, 1, item_count))
                            dir_count += 1
                            dir_sizes.setdefault(dir_path, 0)
                        except Exception:
                            continue

                    for filename in files:
                        if self._cancelled:
                            break
                        # 跳过 Office 临时文件（以 ~$ 开头）
                        if filename.startswith('~$'):
                            continue
                        try:
                            file_path = os.path.join(root, filename)
                            stat = os.stat(file_path)
                            _, ext = os.path.splitext(filename)

                            batch.append((
                                file_path,
                                filename,
                                ext.lower() if ext else None,
                                stat.st_size,
                                stat.st_mtime,
                                0,
                                0
                            ))
                            file_count += 1
                            self._file_log_batch.append(file_path)
                            now = time.time()
                            if len(self._file_log_batch) >= FILE_LOG_BATCH_SIZE or now - self._last_file_log_time >= self._file_log_interval:
                                for fp in self._file_log_batch:
                                    self.file_found.emit(fp)
                                self._file_log_batch.clear()
                                self._last_file_log_time = now

                            parent = root
                            dir_sizes.setdefault(parent, 0)
                            dir_sizes[parent] += stat.st_size

                            if len(batch) >= self._batch_size:
                                db.insert_file_batch(batch, skip_cache_invalidate=True)
                                batch.clear()
                                total_files = dir_count + file_count
                                now = time.time()
                                if now - self._last_progress_time >= self._progress_interval:
                                    self._last_progress_time = now
                                    self.progress.emit(total_files, pct, current_dir_display)
                                    self.dir_scanned.emit(current_dir_display)
                        except Exception:
                            continue

                if not self._cancelled:
                    self.dir_completed.emit(base_dir)

            if self._cancelled:
                for d in normalized_dirs:
                    set_scan_status(d, SCAN_STATUS_INCOMPLETE)
                # 取消时只清除当前扫描目录的索引
                for d in normalized_dirs:
                    db.delete_entries_by_prefix(d)
                return

            if batch:
                db.insert_file_batch(batch, skip_cache_invalidate=True)

            all_dirs_sorted = sorted(dir_sizes.keys(), key=lambda p: -p.count(os.sep))
            for dir_path in all_dirs_sorted:
                parent = os.path.dirname(dir_path)
                if parent and parent != dir_path:
                    dir_sizes.setdefault(parent, 0)
                    dir_sizes[parent] += dir_sizes[dir_path]

            if dir_sizes:
                db.update_folder_sizes(dir_sizes, skip_cache_invalidate=True)

            db._search_cache.invalidate()

            # 刷新剩余的文件日志
            if self._file_log_batch:
                for fp in self._file_log_batch:
                    self.file_found.emit(fp)
                self._file_log_batch.clear()

            total_files = dir_count + file_count

            # ===== 阶段2：建立内容全文索引 =====
            if not self._cancelled:
                self.progress.emit(total_files, 99, "正在建立内容索引...")
                self._index_file_contents(db, normalized_dirs)

            if self._cancelled:
                for d in normalized_dirs:
                    set_scan_status(d, SCAN_STATUS_INCOMPLETE)
                for d in normalized_dirs:
                    db.delete_entries_by_prefix(d)
                return

            for d in normalized_dirs:
                set_scan_status(d, SCAN_STATUS_COMPLETE)

            elapsed = time.time() - start_time
            self.progress.emit(total_files, 100, "扫描完成")
            self.finished.emit(total_files, elapsed)
        except Exception as e:
            logger.error(f"扫描异常: {e}", exc_info=True)
            if not self._cancelled:
                for d in self._search_dirs:
                    set_scan_status(d, SCAN_STATUS_FAILED)
                self.error.emit(str(e))
