import os
import sqlite3
from typing import Optional
from config import get_config_dir

class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connection = None
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            db_path = self._get_db_path()
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self._connection = sqlite3.connect(db_path)
            self._connection.row_factory = sqlite3.Row
            self._init_db()
        return self._connection

    def _get_db_path(self) -> str:
        return os.path.join(get_config_dir(), "filefinder.db")

    def _init_db(self):
        conn = self._connection
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_query TEXT,
                content_query TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                result_count INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_history_created ON search_history(created_at DESC)
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None