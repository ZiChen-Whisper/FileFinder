import os
import json
from typing import Dict, List

DEFAULT_CONFIG = {
    "general": {
        "theme": "system",
        "language": "zh_CN",
        "auto_start": False,
        "minimize_to_tray": True,
        "global_shortcut": "Ctrl+Alt+F"
    },
    "search": {
        "default_dirs": [],
        "scanned_dirs": [],
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