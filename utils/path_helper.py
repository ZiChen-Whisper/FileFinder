import os
import string
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from models.file_item import FileItem

def normalize_path(path: str) -> str:
    """
    规范化路径，展开用户目录并标准化分隔符。
    
    Args:
        path: 原始路径
    
    Returns:
        规范化后的路径
    """
    return os.path.normpath(os.path.expanduser(path))

def get_file_info(file_path: str) -> Optional[FileItem]:
    """
    获取文件信息，创建FileItem对象。
    
    Args:
        file_path: 文件路径
    
    Returns:
        FileItem对象，如果获取失败返回None
    """
    try:
        stat = os.stat(file_path)
        path = Path(file_path)
        return FileItem(
            path=str(path.resolve()),
            name=path.name,
            extension=path.suffix.lower(),
            size=stat.st_size,
            modified_time=datetime.fromtimestamp(stat.st_mtime),
            created_time=datetime.fromtimestamp(stat.st_ctime),
            is_directory=os.path.isdir(file_path)
        )
    except Exception:
        return None

def is_excluded_directory(dir_name: str, exclude_dirs: list) -> bool:
    """
    判断目录是否在排除列表中。
    
    Args:
        dir_name: 目录名称
        exclude_dirs: 排除目录列表
    
    Returns:
        是否需要排除
    """
    return any(excluded.lower() == dir_name.lower() for excluded in exclude_dirs)

def is_excluded_extension(ext: str, exclude_extensions: list) -> bool:
    """
    判断文件扩展名是否在排除列表中。
    
    Args:
        ext: 文件扩展名
        exclude_extensions: 排除扩展名列表
    
    Returns:
        是否需要排除
    """
    return ext.lower() in [e.lower() for e in exclude_extensions]

def is_binary_file(file_path: str) -> bool:
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\x00' in chunk:
                return True
            text_characters = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
            if chunk.translate(None, text_characters):
                return False
            return True
    except Exception:
        return True

def get_all_drives() -> List[str]:
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives

def get_user_directories() -> List[str]:
    home = os.path.expanduser("~")
    candidates = [
        home,
        os.path.join(home, "Desktop"),
        os.path.join(home, "Documents"),
        os.path.join(home, "Downloads"),
    ]
    return [d for d in candidates if os.path.isdir(d)]