from dataclasses import dataclass
from datetime import datetime
from typing import Optional

FILE_TYPE_MAP = {
    '.txt': 'document', '.md': 'document', '.log': 'document', '.csv': 'document',
    '.json': 'document', '.xml': 'document', '.yaml': 'document', '.yml': 'document',
    '.ini': 'document', '.cfg': 'document', '.conf': 'document', '.toml': 'document',
    '.pdf': 'document', '.docx': 'document', '.doc': 'document',
    '.xlsx': 'document', '.xls': 'document', '.pptx': 'document', '.ppt': 'document',
    '.py': 'code', '.js': 'code', '.ts': 'code', '.html': 'code', '.css': 'code',
    '.java': 'code', '.c': 'code', '.cpp': 'code', '.h': 'code', '.go': 'code',
    '.rs': 'code', '.rb': 'code', '.php': 'code', '.sh': 'code', '.bat': 'code',
    '.ps1': 'code', '.sql': 'code',
    '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.gif': 'image',
    '.bmp': 'image', '.tiff': 'image', '.svg': 'image', '.ico': 'image',
    '.mp4': 'video', '.mkv': 'video', '.avi': 'video', '.mov': 'video',
    '.wmv': 'video', '.flv': 'video',
    '.mp3': 'audio', '.wav': 'audio', '.flac': 'audio', '.aac': 'audio',
    '.ogg': 'audio', '.wma': 'audio',
    '.zip': 'archive', '.rar': 'archive', '.7z': 'archive', '.tar': 'archive',
    '.gz': 'archive', '.bz2': 'archive',
}

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
        if self.is_directory:
            return ""
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
        if self.is_directory:
            return ""
        return self.modified_time.strftime("%Y-%m-%d %H:%M")

    @property
    def file_type(self) -> str:
        if self.is_directory:
            return 'folder'
        ext = self.extension.lower()
        return FILE_TYPE_MAP.get(ext, 'other')
