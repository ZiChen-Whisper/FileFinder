import os
import sqlite3
from config import get_config_dir

class DatabaseManager:
    _instance = None
    _db_path = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._db_path = os.path.join(get_config_dir(), "filefinder.db")
            os.makedirs(os.path.dirname(cls._db_path), exist_ok=True)
            cls._instance._init_db()
        return cls._instance

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=-8000")
        return conn

    def _init_db(self):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_index_cache (
                    path TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    extension TEXT,
                    size INTEGER,
                    modified_time REAL,
                    is_directory INTEGER DEFAULT 0,
                    indexed_at REAL DEFAULT (julianday('now'))
                )
            ''')
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_index_name ON file_index_cache(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_index_ext ON file_index_cache(extension)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_index_size ON file_index_cache(size)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_index_modified ON file_index_cache(modified_time)")
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

    def insert_file_batch(self, rows: list):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT OR REPLACE INTO file_index_cache (path, name, extension, size, modified_time, is_directory) VALUES (?, ?, ?, ?, ?, ?)",
                rows
            )
            conn.commit()
        finally:
            conn.close()

    def search_files(self, pattern: str, case_sensitive: bool = False,
                     file_types: list = None, exclude_file_types: list = None,
                     size_min: int = None,
                     size_max: int = None, max_results: int = 1000) -> list:
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            conditions = []
            params = []

            if pattern:
                conditions.append("name LIKE ?")
                params.append(f"%{pattern}%")

            if file_types:
                placeholders = ','.join(['?' for _ in file_types])
                conditions.append(f"extension IN ({placeholders})")
                params.extend(file_types)
                conditions.append("is_directory = 0")

            if exclude_file_types:
                placeholders = ','.join(['?' for _ in exclude_file_types])
                conditions.append(f"(extension NOT IN ({placeholders}) OR extension IS NULL)")
                params.extend(exclude_file_types)
                conditions.append("is_directory = 0")

            if size_min is not None:
                conditions.append("size >= ?")
                params.append(size_min)
            if size_max is not None:
                conditions.append("size <= ?")
                params.append(size_max)

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query_sql = f"SELECT path, name, extension, size, modified_time, is_directory FROM file_index_cache WHERE {where_clause} LIMIT ?"
            params.append(max_results)

            cursor.execute(query_sql, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def close(self):
        pass
