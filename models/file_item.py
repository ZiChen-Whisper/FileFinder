from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class FileItem:
    path: str
    name: str
    extension: str
    size: int
    modified_time: datetime
    created_time: datetime
    is_directory: bool = False

    @property
    def size_display(self) -> str:
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        elif self.size < 1024 * 1024 * 1024:
            return f"{self.size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.size / (1024 * 1024 * 1024):.1f} GB"

    @property
    def modified_date(self) -> str:
        return self.modified_time.strftime("%Y-%m-%d %H:%M")

    @property
    def file_type(self) -> str:
        ext = self.extension.lower()
        if ext in {'.txt', '.md', '.log', '.csv', '.json', '.xml', '.yaml', '.yml', 
                   '.ini', '.cfg', '.conf', '.toml', '.pdf', '.docx', '.xlsx', '.pptx'}:
            return 'document'
        elif ext in {'.py', '.js', '.ts', '.html', '.css', '.java', '.c', '.cpp', 
                     '.h', '.go', '.rs', '.rb', '.php', '.sh', '.bat', '.ps1', '.sql'}:
            return 'code'
        elif ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.ico'}:
            return 'image'
        elif ext in {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv'}:
            return 'video'
        elif ext in {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'}:
            return 'audio'
        elif ext in {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'}:
            return 'archive'
        else:
            return 'other'