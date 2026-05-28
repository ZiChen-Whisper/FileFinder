from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from constants import MAX_SEARCH_RESULTS

@dataclass
class SearchQuery:
    name_query: Optional[str] = None
    name_mode: str = 'fuzzy'
    name_case_sensitive: bool = False

    content_query: Optional[str] = None
    content_mode: str = 'keyword'
    content_case_sensitive: bool = False

    file_types: List[str] = field(default_factory=list)
    exclude_file_types: List[str] = field(default_factory=list)
    size_min: Optional[int] = None
    size_max: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_dirs: List[str] = field(default_factory=list)
    exclude_dirs: List[str] = field(default_factory=list)
    max_results: int = MAX_SEARCH_RESULTS

    @property
    def has_name_query(self) -> bool:
        return self.name_query is not None and self.name_query.strip() != ''

    @property
    def has_content_query(self) -> bool:
        return self.content_query is not None and self.content_query.strip() != ''

    @property
    def has_query(self) -> bool:
        return self.has_name_query or self.has_content_query