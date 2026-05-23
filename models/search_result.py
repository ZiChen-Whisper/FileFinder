from dataclasses import dataclass, field
from typing import List, Optional
from .file_item import FileItem

@dataclass
class ContentMatch:
    line_number: int
    line_content: str
    match_start: int
    match_end: int
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)
    page_number: int = 0
    page_rect: tuple = ()

@dataclass
class SearchResult:
    file_item: FileItem
    match_reason: str

    content_matches: List[ContentMatch] = field(default_factory=list)
    name_match_score: int = 0

    @property
    def score(self) -> int:
        score = 0
        if self.match_reason in ('name', 'both'):
            score += self.name_match_score * 10
            if self.name_match_score == 0:
                score += 10
        if self.match_reason in ('content', 'both'):
            score += len(self.content_matches) * 5
        return score