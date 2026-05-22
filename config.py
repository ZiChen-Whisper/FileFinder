import os
import json
from typing import Dict, List, Optional

DEFAULT_CONFIG = {
    "general": {
        "theme": "system",
        "language": "zh_CN",
        "auto_start": False,
        "minimize_to_tray": True,
        "global_shortcut": "Ctrl+Shift+F"
    },
    "search": {
        "default_dirs": [],
        "scanned_dirs": [],
        "scan_status": {},
        "exclude_dirs": [
            "C:\\Windows",
            "C:\\Program Files",
            "node_modules",
            "__pycache__",
            ".git",
            ".venv"
        ],
        "exclude_extensions": [".dll", ".exe", ".sys"],
        "case_sensitive": False,
        "max_results": 1000,
        "content_max_size_mb": 10
    },
    "ui": {
        "window_width": 900,
        "window_height": 600,
        "preview_panel_width": 350,
        "show_status_bar": True
    }
}

SCAN_STATUS_COMPLETE = "complete"
SCAN_STATUS_INCOMPLETE = "incomplete"
SCAN_STATUS_FAILED = "failed"
SCAN_STATUS_SCANNING = "scanning"

def get_config_dir() -> str:
    home = os.path.expanduser("~")
    config_dir = os.path.join(home, ".filefinder")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

def get_config_path() -> str:
    return os.path.join(get_config_dir(), "config.json")

def load_config() -> Dict:
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                return deep_merge(DEFAULT_CONFIG, loaded)
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config: Dict) -> None:
    config_path = get_config_path()
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def deep_merge(default: Dict, override: Dict) -> Dict:
    result = default.copy()
    for key, value in override.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def get_default_search_dirs() -> List[str]:
    config = load_config()
    dirs = config.get("search", {}).get("default_dirs", [])
    if not dirs:
        from utils.path_helper import get_all_drives
        return get_all_drives()
    return dirs

def get_exclude_dirs() -> List[str]:
    config = load_config()
    return config.get("search", {}).get("exclude_dirs", [])

def get_max_results() -> int:
    config = load_config()
    return config.get("search", {}).get("max_results", 1000)

def get_content_max_size_mb() -> int:
    config = load_config()
    return config.get("search", {}).get("content_max_size_mb", 10)

def get_scanned_dirs() -> List[str]:
    config = load_config()
    return config.get("search", {}).get("scanned_dirs", [])

def save_scanned_dirs(dirs: List[str]) -> None:
    config = load_config()
    config["search"]["scanned_dirs"] = list(dirs)
    save_config(config)

def get_scan_status(dir_path: str) -> Optional[str]:
    """
    获取指定目录的扫描状态。

    Args:
        dir_path: 目录路径

    Returns:
        扫描状态字符串（complete/incomplete/failed/scanning），如果无记录返回 None
    """
    config = load_config()
    status_map = config.get("search", {}).get("scan_status", {})
    normalized = os.path.normpath(dir_path)
    return status_map.get(normalized)

def set_scan_status(dir_path: str, status: str) -> None:
    """
    设置指定目录的扫描状态。

    Args:
        dir_path: 目录路径
        status: 扫描状态（SCAN_STATUS_COMPLETE/INCOMPLETE/FAILED/SCANNING）
    """
    config = load_config()
    config.setdefault("search", {}).setdefault("scan_status", {})
    normalized = os.path.normpath(dir_path)
    config["search"]["scan_status"][normalized] = status
    save_config(config)

def set_scan_status_batch(dir_status_map: Dict[str, str]) -> None:
    """
    批量设置多个目录的扫描状态。

    Args:
        dir_status_map: 目录路径到扫描状态的映射
    """
    config = load_config()
    config.setdefault("search", {}).setdefault("scan_status", {})
    for dir_path, status in dir_status_map.items():
        normalized = os.path.normpath(dir_path)
        config["search"]["scan_status"][normalized] = status
    save_config(config)

def get_incomplete_scan_dirs() -> List[str]:
    """
    获取所有扫描未完成或失败的目录列表。

    Returns:
        未完成扫描的目录路径列表
    """
    config = load_config()
    status_map = config.get("search", {}).get("scan_status", {})
    return [d for d, s in status_map.items() if s in (SCAN_STATUS_INCOMPLETE, SCAN_STATUS_FAILED, SCAN_STATUS_SCANNING)]

def clear_scan_status() -> None:
    """清除所有扫描状态记录。"""
    config = load_config()
    config.setdefault("search", {})["scan_status"] = {}
    save_config(config)

def get_theme() -> str:
    """获取界面主题设置"""
    config = load_config()
    return config.get("general", {}).get("theme", "system")

def set_theme(theme: str) -> None:
    """设置界面主题"""
    config = load_config()
    config.setdefault("general", {})["theme"] = theme
    save_config(config)

def get_language() -> str:
    """获取语言设置"""
    config = load_config()
    return config.get("general", {}).get("language", "zh_CN")

def set_language(lang: str) -> None:
    """设置语言"""
    config = load_config()
    config.setdefault("general", {})["language"] = lang
    save_config(config)

def get_global_shortcut() -> str:
    """获取全局快捷键设置"""
    config = load_config()
    return config.get("general", {}).get("global_shortcut", "Ctrl+Shift+F")

def set_global_shortcut(shortcut: str) -> None:
    """设置全局快捷键"""
    config = load_config()
    config.setdefault("general", {})["global_shortcut"] = shortcut
    save_config(config)

def set_max_results(max_results: int) -> None:
    """设置最大搜索结果数"""
    config = load_config()
    config.setdefault("search", {})["max_results"] = max_results
    save_config(config)

def set_content_max_size_mb(size_mb: int) -> None:
    """设置内容搜索最大文件大小"""
    config = load_config()
    config.setdefault("search", {})["content_max_size_mb"] = size_mb
    save_config(config)

def is_first_launch() -> bool:
    config = load_config()
    scanned = config.get("search", {}).get("scanned_dirs", [])
    default_dirs = config.get("search", {}).get("default_dirs", [])
    return not scanned and not default_dirs

def reset_all_settings() -> None:
    config_path = get_config_path()
    if os.path.exists(config_path):
        os.remove(config_path)
    db_path = os.path.join(get_config_dir(), "filefinder.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    from database.db_manager import DatabaseManager
    if DatabaseManager._instance is not None:
        DatabaseManager._instance._search_cache.invalidate()
        DatabaseManager._instance = None
        DatabaseManager._db_path = None
