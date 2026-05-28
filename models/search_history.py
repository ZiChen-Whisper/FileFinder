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

    @property
    def display_text(self) -> str:
        parts = []
        if self.name_query:
            parts.append(f"文件名: {self.name_query}")
        if self.content_query:
            parts.append(f"内容: {self.content_query}")
        return " | ".join(parts) if parts else ""