import logging
from datetime import datetime
from typing import List, Optional
from models import SearchHistory
from .db_manager import DatabaseManager

logger = logging.getLogger(__name__)


def add_history(name_query: Optional[str], content_query: Optional[str], result_count: int = 0):
    """
    添加一条搜索历史记录。

    Args:
        name_query: 文件名搜索关键词
        content_query: 内容搜索关键词
        result_count: 搜索结果数量
    """
    db = DatabaseManager()
    conn = db._get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO search_history (name_query, content_query, result_count)
            VALUES (?, ?, ?)
        ''', (name_query, content_query, result_count))
        conn.commit()
    except Exception as e:
        logger.error(f"添加搜索历史失败: {e}")
    finally:
        conn.close()


def get_histories(limit: int = 100) -> List[SearchHistory]:
    """
    获取最近的搜索历史记录。

    Args:
        limit: 返回的最大记录数

    Returns:
        搜索历史列表，按时间倒序排列
    """
    db = DatabaseManager()
    conn = db._get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name_query, content_query, created_at, result_count
            FROM search_history
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        results = []
        for row in rows:
            try:
                created_at_val = row['created_at']
                if isinstance(created_at_val, str):
                    created_at = datetime.fromisoformat(created_at_val)
                elif isinstance(created_at_val, (int, float)):
                    created_at = datetime.fromtimestamp(created_at_val)
                else:
                    created_at = datetime.now()
                results.append(SearchHistory(
                    id=row['id'],
                    name_query=row['name_query'],
                    content_query=row['content_query'],
                    created_at=created_at,
                    result_count=row['result_count']
                ))
            except Exception as e:
                logger.warning(f"解析搜索历史记录失败: {e}")
                continue
        return results
    except Exception as e:
        logger.error(f"获取搜索历史失败: {e}")
        return []
    finally:
        conn.close()


def delete_history(history_id: int):
    """
    删除指定ID的搜索历史记录。

    Args:
        history_id: 要删除的历史记录ID
    """
    db = DatabaseManager()
    conn = db._get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM search_history WHERE id = ?', (history_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"删除搜索历史失败: {e}")
    finally:
        conn.close()


def clear_histories():
    """清除所有搜索历史记录。"""
    db = DatabaseManager()
    conn = db._get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM search_history')
        conn.commit()
    except Exception as e:
        logger.error(f"清除搜索历史失败: {e}")
    finally:
        conn.close()
