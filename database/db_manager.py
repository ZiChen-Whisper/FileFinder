import os
import sys
import sqlite3
import logging
import threading
from config import get_config_dir

logger = logging.getLogger(__name__)


class SearchCache:
    def __init__(self):
        self._entries = []
        self._loaded = False
        self._lock = threading.Lock()

    def load(self, db_path: str):
        with self._lock:
            if self._loaded:
                return
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT path, name, name_stem, extension, size, modified_time, is_directory, item_count FROM file_index_cache")
                self._entries = [dict(row) for row in cursor.fetchall()]
                self._loaded = True
            finally:
                conn.close()

    def invalidate(self):
        with self._lock:
            self._entries = []
            self._loaded = False

    def is_loaded(self) -> bool:
        return self._loaded

    def search(self, pattern: str, case_sensitive: bool = False,
               file_types: list = None, exclude_file_types: list = None,
               size_min: int = None, size_max: int = None,
               max_results: int = 1000) -> list:
        with self._lock:
            if not self._loaded:
                return []

            pattern_lower = pattern.lower() if pattern and not case_sensitive else pattern
            file_types_set = set(file_types) if file_types else None
            exclude_types_set = set(exclude_file_types) if exclude_file_types else None

            results = []
            for entry in self._entries:
                if file_types_set:
                    ext = entry.get("extension", "") or ""
                    if ext not in file_types_set:
                        continue
                    if entry.get("is_directory", 0):
                        continue

                if exclude_types_set:
                    ext = entry.get("extension", "") or ""
                    if ext in exclude_types_set:
                        continue
                    if entry.get("is_directory", 0):
                        continue

                if size_min is not None and entry.get("size", 0) < size_min:
                    continue
                if size_max is not None and entry.get("size", 0) > size_max:
                    continue

                if pattern:
                    name_stem = entry.get("name_stem", "") or entry.get("name", "")
                    if not case_sensitive:
                        if pattern_lower not in name_stem.lower():
                            continue
                    else:
                        if pattern not in name_stem:
                            continue

                results.append(entry)
                if len(results) >= max_results:
                    break

            return results


class DatabaseManager:
    _instance = None
    _db_path = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            try:
                db_dir = get_config_dir()
                test_path = os.path.join(db_dir, ".write_test")
                with open(test_path, "w") as f:
                    f.write("test")
                os.remove(test_path)
            except (OSError, PermissionError):
                if getattr(sys, 'frozen', False):
                    db_dir = os.path.dirname(sys.executable)
                else:
                    db_dir = os.path.dirname(os.path.abspath(__file__))
                db_dir = os.path.join(db_dir, "..", "data")
                os.makedirs(db_dir, exist_ok=True)
            else:
                db_dir = get_config_dir()
            cls._db_path = os.path.join(db_dir, "filefinder.db")
            os.makedirs(os.path.dirname(cls._db_path), exist_ok=True)
            cls._instance._init_db()
            cls._instance._migrate_name_stem()
            cls._instance._search_cache = SearchCache()
        return cls._instance

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-16000")
            conn.execute("PRAGMA mmap_size=67108864")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA page_size=4096")
        except sqlite3.OperationalError:
            pass
        return conn

    def _init_db(self):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_index_cache (
                    path TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    name_stem TEXT,
                    extension TEXT,
                    size INTEGER,
                    modified_time REAL,
                    is_directory INTEGER DEFAULT 0,
                    item_count INTEGER DEFAULT 0,
                    indexed_at REAL DEFAULT (julianday('now'))
                )
            ''')
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_index_name ON file_index_cache(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_index_ext ON file_index_cache(extension)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_index_size ON file_index_cache(size)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_index_modified ON file_index_cache(modified_time)")

            try:
                cursor.execute("ALTER TABLE file_index_cache ADD COLUMN item_count INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE file_index_cache ADD COLUMN name_stem TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_index_name_stem ON file_index_cache(name_stem)")
            except sqlite3.OperationalError:
                pass

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name_query TEXT,
                    content_query TEXT,
                    name_mode TEXT DEFAULT 'fuzzy',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    result_count INTEGER DEFAULT 0
                )
            ''')
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_created ON search_history(created_at DESC)")
            try:
                cursor.execute("ALTER TABLE search_history ADD COLUMN name_mode TEXT DEFAULT 'fuzzy'")
            except sqlite3.OperationalError:
                pass
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # --- 内容全文索引表 ---
            # 原始内容存储表（用于上下文提取）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_content_raw (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    content_text TEXT,
                    indexed_at REAL DEFAULT (julianday('now'))
                )
            ''')
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_raw_path ON file_content_raw(file_path)")

            # FTS5 全文索引虚拟表
            # 使用 standalone 模式（非外部内容），简单可靠
            try:
                cursor.execute('''
                    CREATE VIRTUAL TABLE IF NOT EXISTS file_content_fts
                    USING fts5(
                        file_path,
                        file_name,
                        content,
                        tokenize='unicode61'
                    )
                ''')
            except sqlite3.OperationalError as e:
                logger.warning(f"FTS5 虚拟表创建失败（可能不支持）: {e}")

            conn.commit()
        finally:
            conn.close()

    def _migrate_name_stem(self):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM file_index_cache WHERE name_stem IS NULL")
            null_count = cursor.fetchone()[0]
            if null_count == 0:
                return
            cursor.execute("SELECT path, name, is_directory FROM file_index_cache WHERE name_stem IS NULL")
            rows = cursor.fetchall()
            for row in rows:
                if row["is_directory"]:
                    name_stem = row["name"]
                else:
                    name_stem = os.path.splitext(row["name"])[0]
                cursor.execute("UPDATE file_index_cache SET name_stem = ? WHERE path = ?", (name_stem, row["path"]))
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def get_index_count(self) -> int:
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM file_index_cache")
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def clear_index(self):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM file_index_cache")
            # 同时清除内容索引
            cursor.execute("DELETE FROM file_content_raw")
            try:
                cursor.execute("DELETE FROM file_content_fts")
            except sqlite3.OperationalError:
                pass
            conn.commit()
        finally:
            conn.close()
        self._search_cache.invalidate()

    def insert_file_batch(self, rows: list, skip_cache_invalidate: bool = False):
        """
        批量插入文件索引记录。

        Args:
            rows: 文件记录列表，每条格式为 (path, name, ext, size, mtime, is_dir, item_count)
            skip_cache_invalidate: 为 True 时跳过缓存失效（扫描期间使用，避免反复重建缓存）
        """
        if not rows:
            return
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            enriched = []
            for row in rows:
                path, name, ext, size, mtime, is_dir, item_count = row
                if is_dir:
                    name_stem = name
                else:
                    name_stem = os.path.splitext(name)[0]
                enriched.append((path, name, name_stem, ext, size, mtime, is_dir, item_count))
            cursor.executemany(
                "INSERT OR REPLACE INTO file_index_cache (path, name, name_stem, extension, size, modified_time, is_directory, item_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                enriched
            )
            conn.commit()
        finally:
            conn.close()
        if not skip_cache_invalidate:
            self._search_cache.invalidate()

    def update_folder_sizes(self, dir_sizes: dict, skip_cache_invalidate: bool = False):
        """
        批量更新目录大小。

        Args:
            dir_sizes: 目录路径到大小的映射
            skip_cache_invalidate: 为 True 时跳过缓存失效（扫描期间使用）
        """
        if not dir_sizes:
            return
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.executemany(
                "UPDATE file_index_cache SET size = ? WHERE path = ? AND is_directory = 1",
                [(total_size, dir_path) for dir_path, total_size in dir_sizes.items()]
            )
            conn.commit()
        finally:
            conn.close()
        if not skip_cache_invalidate:
            self._search_cache.invalidate()

    def delete_entries_by_prefix(self, prefix: str) -> int:
        """
        删除指定路径前缀下的所有索引条目（包括内容索引）。

        Args:
            prefix: 路径前缀

        Returns:
            删除的行数
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            # 规范化前缀路径
            norm_prefix = os.path.normpath(prefix)
            # 构建 LIKE 模式：转义路径中的特殊字符（\, %, _）
            # ESCAPE '\\' 表示 \\ 为转义符，所以 \\% 匹配字面 %，\\\\ 匹配字义 \
            escaped_prefix = norm_prefix.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
            like_pattern = escaped_prefix + '\\\\%'
            cursor.execute(
                "DELETE FROM file_index_cache WHERE path LIKE ? ESCAPE '\\'",
                (like_pattern,)
            )
            deleted = cursor.rowcount
            cursor.execute(
                "DELETE FROM file_index_cache WHERE path = ?",
                (norm_prefix,)
            )
            deleted += cursor.rowcount

            # 同时删除内容索引
            cursor.execute(
                "DELETE FROM file_content_raw WHERE file_path LIKE ? ESCAPE '\\' OR file_path = ?",
                (like_pattern, norm_prefix)
            )
            try:
                cursor.execute(
                    "DELETE FROM file_content_fts WHERE file_path LIKE ? ESCAPE '\\' OR file_path = ?",
                    (like_pattern, norm_prefix)
                )
            except sqlite3.OperationalError:
                pass

            conn.commit()
            self._search_cache.invalidate()
            return deleted
        finally:
            conn.close()

    def get_paths_by_parent(self, parent_dir: str) -> list:
        """
        获取指定父目录下的所有条目路径（用于增量同步）。

        Args:
            parent_dir: 父目录路径

        Returns:
            该目录下所有条目的路径列表
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            norm_dir = os.path.normpath(parent_dir)
            escaped_dir = norm_dir.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
            like_pattern = escaped_dir + '\\\\%'
            cursor.execute(
                "SELECT path FROM file_index_cache WHERE path LIKE ? ESCAPE '\\' OR path = ?",
                (like_pattern, norm_dir)
            )
            return [row["path"] for row in cursor.fetchall()]
        finally:
            conn.close()

    def search_files(self, pattern: str, case_sensitive: bool = False,
                     file_types: list = None, exclude_file_types: list = None,
                     size_min: int = None,
                     size_max: int = None, max_results: int = 1000) -> list:
        if not self._search_cache.is_loaded():
            self._search_cache.load(self._db_path)

        cached_results = self._search_cache.search(
            pattern=pattern,
            case_sensitive=case_sensitive,
            file_types=file_types,
            exclude_file_types=exclude_file_types,
            size_min=size_min,
            size_max=size_max,
            max_results=max_results
        )

        if not cached_results:
            return []

        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            paths = [r["path"] for r in cached_results]
            placeholders = ','.join(['?' for _ in paths])
            cursor.execute(
                f"SELECT path, name, extension, size, modified_time, is_directory, item_count FROM file_index_cache WHERE path IN ({placeholders})",
                paths
            )
            return cursor.fetchall()
        finally:
            conn.close()

    def update_file_entry(self, old_path: str, new_path: str = None, new_name: str = None,
                          new_ext: str = None, new_size: int = None, new_mtime: float = None):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            if new_path is not None:
                name_stem = os.path.splitext(new_name)[0] if new_name and not new_path.endswith(os.sep) else new_name
                cursor.execute(
                    "UPDATE file_index_cache SET path = ?, name = ?, name_stem = ?, extension = ?, size = ?, modified_time = ? WHERE path = ?",
                    (new_path, new_name, name_stem, new_ext, new_size, new_mtime, old_path)
                )
            elif new_name is not None:
                name_stem = os.path.splitext(new_name)[0]
                cursor.execute(
                    "UPDATE file_index_cache SET name = ?, name_stem = ? WHERE path = ?",
                    (new_name, name_stem, old_path)
                )
            conn.commit()
        finally:
            conn.close()
        self._search_cache.invalidate()

    def delete_file_entry(self, path: str):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM file_index_cache WHERE path = ?", (path,))
            # 同时删除内容索引
            cursor.execute("DELETE FROM file_content_raw WHERE file_path = ?", (path,))
            try:
                cursor.execute("DELETE FROM file_content_fts WHERE file_path = ?", (path,))
            except sqlite3.OperationalError:
                pass
            conn.commit()
        finally:
            conn.close()
        self._search_cache.invalidate()

    def add_file_entry(self, path: str, name: str, ext: str, size: int, mtime: float, is_dir: int = 0, item_count: int = 0):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            name_stem = name if is_dir else os.path.splitext(name)[0]
            cursor.execute(
                "INSERT OR REPLACE INTO file_index_cache (path, name, name_stem, extension, size, modified_time, is_directory, item_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (path, name, name_stem, ext, size, mtime, is_dir, item_count)
            )
            conn.commit()
        finally:
            conn.close()
        self._search_cache.invalidate()

    def get_file_entry(self, path: str):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM file_index_cache WHERE path = ?", (path,))
            return cursor.fetchone()
        finally:
            conn.close()

    def close(self):
        if hasattr(self, '_search_cache'):
            self._search_cache.invalidate()

    # ========== 内容全文索引方法 ==========

    def has_content_index(self) -> bool:
        """检查是否存在内容索引。"""
        return self.get_content_index_count() > 0

    def get_content_index_count(self) -> int:
        """获取内容索引条目数。"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT COUNT(*) FROM file_content_raw")
                return cursor.fetchone()[0]
            except sqlite3.OperationalError:
                return 0
        finally:
            conn.close()

    def insert_content_batch(self, rows: list, skip_cache_invalidate: bool = False):
        """批量插入内容索引记录。

        同时写入 file_content_raw（原始文本）和 file_content_fts（FTS5 索引）。

        Args:
            rows: 内容记录列表，每条格式为 (file_path, file_name, content_text, content_tokenized)
            skip_cache_invalidate: 为 True 时跳过缓存失效
        """
        if not rows:
            return
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            for file_path, file_name, content_text, content_tokenized in rows:
                # 写入原始内容表
                cursor.execute(
                    "INSERT OR REPLACE INTO file_content_raw (file_path, content_text) VALUES (?, ?)",
                    (file_path, content_text)
                )
                # 写入 FTS5 索引（先删除旧记录避免重复）
                try:
                    cursor.execute(
                        "DELETE FROM file_content_fts WHERE file_path = ?",
                        (file_path,)
                    )
                    cursor.execute(
                        "INSERT INTO file_content_fts (file_path, file_name, content) VALUES (?, ?, ?)",
                        (file_path, file_name, content_tokenized)
                    )
                except sqlite3.OperationalError as e:
                    logger.debug(f"FTS5 写入失败: {file_path}, {e}")
            conn.commit()
        finally:
            conn.close()

    def insert_content_entry(self, file_path: str, file_name: str,
                             content_text: str, content_tokenized: str):
        """插入单条内容索引记录。

        Args:
            file_path: 文件路径
            file_name: 文件名
            content_text: 原始提取的文本内容
            content_tokenized: jieba 分词后的文本
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO file_content_raw (file_path, content_text) VALUES (?, ?)",
                (file_path, content_text)
            )
            try:
                cursor.execute(
                    "DELETE FROM file_content_fts WHERE file_path = ?",
                    (file_path,)
                )
                cursor.execute(
                    "INSERT INTO file_content_fts (file_path, file_name, content) VALUES (?, ?, ?)",
                    (file_path, file_name, content_tokenized)
                )
            except sqlite3.OperationalError as e:
                logger.debug(f"FTS5 写入失败: {file_path}, {e}")
            conn.commit()
        finally:
            conn.close()

    def delete_content_entry(self, file_path: str):
        """删除指定文件的内容索引。

        Args:
            file_path: 文件路径
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM file_content_raw WHERE file_path = ?", (file_path,))
            try:
                cursor.execute("DELETE FROM file_content_fts WHERE file_path = ?", (file_path,))
            except sqlite3.OperationalError:
                pass
            conn.commit()
        finally:
            conn.close()

    def delete_content_by_prefix(self, prefix: str) -> int:
        """删除指定路径前缀下的所有内容索引。

        Args:
            prefix: 路径前缀

        Returns:
            删除的行数
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            norm_prefix = os.path.normpath(prefix)
            escaped_prefix = norm_prefix.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
            like_pattern = escaped_prefix + '\\\\%'
            cursor.execute(
                "DELETE FROM file_content_raw WHERE file_path LIKE ? ESCAPE '\\' OR file_path = ?",
                (like_pattern, norm_prefix)
            )
            deleted = cursor.rowcount
            try:
                cursor.execute(
                    "DELETE FROM file_content_fts WHERE file_path LIKE ? ESCAPE '\\' OR file_path = ?",
                    (like_pattern, norm_prefix)
                )
            except sqlite3.OperationalError:
                pass
            conn.commit()
            return deleted
        finally:
            conn.close()

    def update_content_entry(self, file_path: str, file_name: str,
                             content_text: str, content_tokenized: str):
        """更新指定文件的内容索引。

        Args:
            file_path: 文件路径
            file_name: 文件名
            content_text: 原始提取的文本内容
            content_tokenized: jieba 分词后的文本
        """
        self.insert_content_entry(file_path, file_name, content_text, content_tokenized)

    def get_content_by_path(self, file_path: str) -> str:
        """获取文件的原始文本内容（用于上下文提取）。

        Args:
            file_path: 文件路径

        Returns:
            原始文本内容，不存在返回 None
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT content_text FROM file_content_raw WHERE file_path = ?",
                (file_path,)
            )
            row = cursor.fetchone()
            return row["content_text"] if row else None
        finally:
            conn.close()

    def search_content(self, query_tokenized: str, max_results: int = 1000) -> list:
        """使用 FTS5 全文搜索，返回匹配的文件路径列表 + BM25 评分。

        Args:
            query_tokenized: 已分词的查询字符串（由 tokenize_query_for_fts5 生成）
            max_results: 最大返回结果数

        Returns:
            [(file_path, bm25_score), ...] 列表
        """
        if not query_tokenized:
            return []

        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    SELECT file_path, bm25(file_content_fts) as rank
                    FROM file_content_fts
                    WHERE file_content_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                ''', (query_tokenized, max_results))
                return [(row["file_path"], row["rank"]) for row in cursor.fetchall()]
            except sqlite3.OperationalError as e:
                logger.warning(f"FTS5 搜索失败: {e}")
                return []
        finally:
            conn.close()

    def clear_content_index(self):
        """清除所有内容索引。"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM file_content_raw")
            try:
                cursor.execute("DELETE FROM file_content_fts")
            except sqlite3.OperationalError:
                pass
            conn.commit()
        finally:
            conn.close()

    def get_files_for_content_indexing(self, path_prefix: str = None) -> list:
        """获取需要建立内容索引的文件列表。

        从 file_index_cache 中查询非目录、非超大文件的记录，
        排除已有内容索引的文件（用于增量索引）。

        Args:
            path_prefix: 路径前缀过滤（可选）

        Returns:
            [(path, name, extension, size), ...] 列表
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            # 查询非目录、大小 <= 10MB 的文件
            max_size = 10 * 1024 * 1024
            if path_prefix:
                norm_prefix = os.path.normpath(path_prefix)
                escaped_prefix = norm_prefix.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
                like_pattern = escaped_prefix + '\\\\%'
                cursor.execute('''
                    SELECT path, name, extension, size
                    FROM file_index_cache
                    WHERE is_directory = 0
                      AND size <= ?
                      AND (path LIKE ? ESCAPE '\\' OR path = ?)
                      AND path NOT IN (SELECT file_path FROM file_content_raw)
                ''', (max_size, like_pattern, norm_prefix))
            else:
                cursor.execute('''
                    SELECT path, name, extension, size
                    FROM file_index_cache
                    WHERE is_directory = 0
                      AND size <= ?
                      AND path NOT IN (SELECT file_path FROM file_content_raw)
                ''', (max_size,))
            return cursor.fetchall()
        finally:
            conn.close()
