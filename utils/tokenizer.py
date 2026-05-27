"""中文分词工具模块，基于 jieba 实现 FTS5 全文索引所需的分词功能。"""

import logging
import warnings
from typing import Optional

logger = logging.getLogger(__name__)

# jieba 是否已初始化
_jieba_initialized = False


def _ensure_jieba_initialized():
    """确保 jieba 词典已加载（首次调用时自动加载）。"""
    global _jieba_initialized
    if not _jieba_initialized:
        try:
            # 抑制 jieba 内部 pkg_resources 弃用警告
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message=".*pkg_resources.*", category=UserWarning)
                import jieba
                # 静默加载，不打印初始化信息
                jieba.setLogLevel(logging.WARNING)
                jieba.initialize()
            _jieba_initialized = True
        except ImportError:
            logger.warning("jieba 未安装，中文分词功能不可用。请运行: pip install jieba")


def tokenize_for_fts5(text: str) -> str:
    """对文本进行 jieba 分词，返回以空格连接的分词结果。

    用于 FTS5 全文索引的写入和查询。
    索引时：提取文件内容 → tokenize_for_fts5() → 存入 FTS5
    查询时：用户输入关键词 → tokenize_for_fts5() → FTS5 MATCH 查询

    Args:
        text: 待分词的文本内容

    Returns:
        以空格连接的分词结果字符串，空文本返回空字符串
    """
    if not text or not text.strip():
        return ""

    _ensure_jieba_initialized()

    try:
        import jieba
        words = jieba.cut_for_search(text)
        # 过滤空白字符，保留所有词（包括单字，保证召回率）
        tokens = [w for w in words if w.strip()]
        return " ".join(tokens)
    except Exception as e:
        logger.warning(f"分词失败，回退到原始文本: {type(e).__name__}")
        # 分词失败时，直接用原始文本按空格分割
        return text


def tokenize_query_for_fts5(query_text: str) -> str:
    """对搜索查询文本进行分词，生成 FTS5 MATCH 表达式。

    与 tokenize_for_fts5 不同，此方法会将分词结果用 AND 连接，
    确保搜索结果包含所有查询词。

    Args:
        query_text: 用户输入的搜索关键词

    Returns:
        FTS5 MATCH 兼容的查询字符串
    """
    if not query_text or not query_text.strip():
        return ""

    _ensure_jieba_initialized()

    try:
        import jieba
        words = list(jieba.cut_for_search(query_text))
        # 过滤空白和过短的词（单字在 FTS5 中噪音较大）
        tokens = [w for w in words if w.strip() and len(w.strip()) > 1]
        if not tokens:
            # 如果过滤后为空，保留所有非空词
            tokens = [w for w in words if w.strip()]

        if not tokens:
            return ""

        # 用 AND 连接各词，确保结果包含所有查询词
        return " AND ".join(tokens)
    except Exception as e:
        logger.warning(f"查询分词失败，回退到原始查询: {type(e).__name__}")
        return query_text
