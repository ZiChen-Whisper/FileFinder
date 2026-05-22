import os
import logging

from PySide6.QtCore import QThread, Signal

from config import SCAN_STATUS_COMPLETE, SCAN_STATUS_INCOMPLETE, SCAN_STATUS_FAILED, SCAN_STATUS_SCANNING, set_scan_status

logger = logging.getLogger(__name__)


class ScanWorker(QThread):
    progress = Signal(int, int, str)
    finished = Signal(int, float)
    error = Signal(str)
    dir_completed = Signal(str)
    dir_scanned = Signal(str)
    file_found = Signal(str)

    SKIP_DIR_NAMES = frozenset({
        'node_modules', '__pycache__', '.git', '.svn', '.hg',
        '.venv', 'venv', '.tox', '.eggs', 'build', 'dist',
        '.idea', '.vscode', '.vs', '$RECYCLE.BIN',
        'System Volume Information', 'Windows',
        'Program Files', 'Program Files (x86)', 'ProgramData'
    })

    def __init__(self, search_dirs, exclude_dirs, parent=None):
        super().__init__(parent)
        self._search_dirs = search_dirs
        self._exclude_dirs = set(
            os.path.normpath(d).lower() for d in (exclude_dirs or [])
        )
        self._cancelled = False
        self._last_progress_time = 0
        self._progress_interval = 0.3
        self._batch_size = 500
        self._total_dirs = 0
        self._file_log_batch = []
        self._file_log_interval = 0.1
        self._last_file_log_time = 0

    def cancel(self):
        self._cancelled = True

    def _should_skip_dir(self, name, full_path):
        if name in self.SKIP_DIR_NAMES:
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
                            if len(self._file_log_batch) >= 50 or now - self._last_file_log_time >= self._file_log_interval:
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
