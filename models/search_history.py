from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class SearchHistory:
    id: int
    name_query: Optional[str]
    content_query: Optional[str]
    created_at: datetime
    result_count: int = 0
    name_mode: str = 'fuzzy'

    @property
    def display_text(self) -> str:
        parts = []
        if self.name_query:
            parts.append(f"文件名: {self.name_query}")
        if self.content_query:
            parts.append(f"内容: {self.content_query}")
        return " | ".join(parts) if parts else ""

    @property
    def search_type(self) -> str:
        """返回搜索类型：'name' 或 'content'"""
        if self.name_query and self.name_query.strip():
            return 'name'
        return 'content'

    @property
    def mode_display(self) -> str:
        """返回搜索模式的中文展示文本"""
        mode_labels = {'fuzzy': '模糊', 'exact': '精确', 'wildcard': '通配符', 'regex': '正则', 'keyword': '关键词'}
        return mode_labels.get(self.name_mode, self.name_mode)