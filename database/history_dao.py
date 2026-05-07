from datetime import datetime
from typing import List, Optional
from models import SearchHistory
from .db_manager import DatabaseManager

def add_history(name_query: Optional[str], content_query: Optional[str], result_count: int = 0):
    conn = DatabaseManager().get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO search_history (name_query, content_query, result_count)
        VALUES (?, ?, ?)
    ''', (name_query, content_query, result_count))
    
    conn.commit()

def get_histories(limit: int = 100) -> List[SearchHistory]:
    conn = DatabaseManager().get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name_query, content_query, created_at, result_count
        FROM search_history
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    return [
        SearchHistory(
            id=row['id'],
            name_query=row['name_query'],
            content_query=row['content_query'],
            created_at=datetime.fromisoformat(row['created_at']),
            result_count=row['result_count']
        ) for row in rows
    ]

def delete_history(history_id: int):
    conn = DatabaseManager().get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM search_history WHERE id = ?', (history_id,))
    conn.commit()

def clear_histories():
    conn = DatabaseManager().get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM search_history')
    conn.commit()