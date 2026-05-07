from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List
from utils.encoding import read_text_file

class FileParser(ABC):
    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """判断是否能够解析此文件"""
        pass

    @abstractmethod
    def parse(self, file_path: str) -> Optional[str]:
        """解析文件并返回文本内容"""
        pass

class TextParser(FileParser):
    """纯文本解析器（P0 MVP阶段支持）"""
    
    def __init__(self):
        self._text_exts = {'.txt', '.md', '.log', '.csv', '.json', '.xml',
                           '.yaml', '.yml', '.ini', '.cfg', '.conf', '.toml', '.env', '.gitignore',
                           '.py', '.js', '.ts', '.html', '.css', '.java',
                           '.c', '.cpp', '.h', '.go', '.rs', '.rb', '.php',
                           '.sh', '.bat', '.ps1', '.sql'}

    def can_parse(self, file_path: str) -> bool:
        """判断文件是否为纯文本文件"""
        return Path(file_path).suffix.lower() in self._text_exts

    def parse(self, file_path: str) -> Optional[str]:
        """解析纯文本文件内容"""
        return read_text_file(file_path)

class ParserRegistry:
    """文件解析器注册表（P0阶段仅支持纯文本）"""
    
    def __init__(self):
        self._parsers: List[FileParser] = [
            TextParser(),
        ]

    def parse(self, file_path: str) -> Optional[str]:
        """根据文件类型选择合适的解析器"""
        for parser in self._parsers:
            if parser.can_parse(file_path):
                return parser.parse(file_path)
        return None