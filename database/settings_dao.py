import json
import logging
from typing import Optional
from .db_manager import DatabaseManager

logger = logging.getLogger(__name__)


def save_setting(key: str, value: str):
    """
    保存一条设置项。

    Args:
        key: 设置项键名
        value: 设置项值
    """
    db = DatabaseManager()
    conn = db._get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
        ''', (key, value))
        conn.commit()
    except Exception as e:
        logger.error(f"保存设置失败: {e}")
    finally:
        conn.close()


def load_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    读取一条设置项。

    Args:
        key: 设置项键名
        default: 键不存在时的默认值

    Returns:
        设置项的值，如果不存在则返回默认值
    """
    db = DatabaseManager()
    conn = db._get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        return row['value'] if row else default
    except Exception as e:
        logger.error(f"读取设置失败: {e}")
        return default
    finally:
        conn.close()


def save_settings_dict(settings: dict):
    """
    批量保存设置项（字典形式）。

    Args:
        settings: 键值对字典，值会被序列化为 JSON
    """
    for key, value in settings.items():
        save_setting(key, json.dumps(value, ensure_ascii=False))


def load_settings_dict() -> dict:
    """
    读取所有设置项为字典。

    Returns:
        所有设置项的键值对字典
    """
    db = DatabaseManager()
    conn = db._get_conn()
    try:
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
    except Exception as e:
        logger.error(f"读取所有设置失败: {e}")
        return {}
    finally:
        conn.close()
