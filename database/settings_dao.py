import json
from datetime import datetime
from typing import Optional
from .db_manager import DatabaseManager

def save_setting(key: str, value: str):
    conn = DatabaseManager().get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value)
        VALUES (?, ?)
    ''', (key, value))
    
    conn.commit()

def load_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    conn = DatabaseManager().get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    
    return row['value'] if row else default

def save_settings_dict(settings: dict):
    for key, value in settings.items():
        save_setting(key, json.dumps(value))

def load_settings_dict() -> dict:
    conn = DatabaseManager().get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT key, value FROM settings')
    rows = cursor.fetchall()
    
    result = {}
    for row in rows:
        try:
            result[row['key']] = json.loads(row['value'])
        except (json.JSONDecodeError, TypeError):
            result[row['key']] = row['value']
    
    return result