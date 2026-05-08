import os
import sys
import sqlite3
import threading
from config import get_config_dir

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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    result_count INTEGER DEFAULT 0
                )
            ''')
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_created ON search_history(created_at DESC)")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
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
            conn.commit()
        finally:
            conn.close()
        self._search_cache.invalidate()

    def insert_file_batch(self, rows: list):
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
        self._search_cache.invalidate()

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

    def update_folder_sizes(self, dir_sizes: dict):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            for dir_path, total_size in dir_sizes.items():
                cursor.execute("UPDATE file_index_cache SET size = ? WHERE path = ? AND is_directory = 1", (total_size, dir_path))
            conn.commit()
        finally:
            conn.close()
        self._search_cache.invalidate()

    def close(self):
        self._search_cache.invalidate()
