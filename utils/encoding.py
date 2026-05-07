import os
from typing import Optional
import charset_normalizer

def detect_file_encoding(file_path: str) -> str:
    """
    自动检测文件编码。
    
    优先级：UTF-8 > GBK > 其他
    
    Args:
        file_path: 文件路径
    
    Returns:
        检测到的编码名称
    """
    try:
        with open(file_path, 'rb') as f:
            raw = f.read(4)
            if raw.startswith(b'\xff\xfe'):
                return 'utf-16-le'
            if raw.startswith(b'\xfe\xff'):
                return 'utf-16-be'
            if raw.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
    except (OSError, PermissionError):
        return 'utf-8'

    try:
        result = charset_normalizer.from_path(file_path)
        best_match = result.best()
        if best_match:
            return best_match.encoding
    except Exception:
        pass

    return 'utf-8'

def read_text_file(file_path: str, max_size_mb: int = 10) -> Optional[str]:
    """
    安全读取文本文件。
    
    Args:
        file_path: 文件路径
        max_size_mb: 最大文件大小（MB），超过则返回None
    
    Returns:
        文件内容，如果读取失败或文件过大返回None
    """
    if os.path.isdir(file_path):
        return None

    try:
        file_size = os.path.getsize(file_path)
    except OSError:
        return None

    if file_size > max_size_mb * 1024 * 1024:
        return None

    encoding = detect_file_encoding(file_path)
    try:
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            return f.read()
    except Exception:
        return None