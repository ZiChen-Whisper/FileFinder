import os
import fnmatch
from typing import List, Optional
from models import FileItem, SearchQuery
from utils.path_helper import get_file_info, is_excluded_directory

def fuzzy_match(name: str, pattern: str, case_sensitive: bool = False) -> bool:
    """
    模糊匹配文件名。
    
    Args:
        name: 文件名
        pattern: 搜索模式
        case_sensitive: 是否区分大小写
    
    Returns:
        是否匹配
    """
    if not case_sensitive:
        name = name.lower()
        pattern = pattern.lower()
    
    if not pattern:
        return True
    
    return pattern in name

def wildcard_match(name: str, pattern: str, case_sensitive: bool = False) -> bool:
    """
    通配符匹配文件名。
    
    Args:
        name: 文件名
        pattern: 搜索模式（支持*和?）
        case_sensitive: 是否区分大小写
    
    Returns:
        是否匹配
    """
    if not case_sensitive:
        name = name.lower()
        pattern = pattern.lower()
    return fnmatch.fnmatch(name, pattern)

def search_by_name(directory: str, query: SearchQuery) -> List[FileItem]:
    """
    在指定目录中按文件名搜索。
    
    Args:
        directory: 要搜索的目录路径
        query: 搜索查询条件
    
    Returns:
        匹配的文件列表
    """
    results = []
    exclude_dirs = query.exclude_dirs
    
    try:
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not is_excluded_directory(d, exclude_dirs)]
            
            for filename in files:
                file_path = os.path.join(root, filename)
                try:
                    file_info = get_file_info(file_path)
                    if file_info:
                        if query.has_name_query:
                            pattern = query.name_query
                            if query.name_mode == 'exact':
                                match = (file_info.name == pattern) if query.name_case_sensitive \
                                        else (file_info.name.lower() == pattern.lower())
                            elif query.name_mode == 'wildcard':
                                match = wildcard_match(file_info.name, pattern, query.name_case_sensitive)
                            else:
                                match = fuzzy_match(file_info.name, pattern, query.name_case_sensitive)
                            
                            if match:
                                results.append(file_info)
                        else:
                            results.append(file_info)
                except Exception:
                    continue
                
                if len(results) >= query.max_results:
                    return results
    except Exception:
        pass
    
    return results