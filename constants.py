WINDOW_TITLE = "FileFinder"
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 500
DEFAULT_WINDOW_WIDTH = 900
DEFAULT_WINDOW_HEIGHT = 600

SEARCH_DEBOUNCE_MS = 300
MAX_WORKERS = 4
BATCH_SIZE = 500

TEXT_EXTENSIONS = {
    '.txt', '.md', '.log', '.csv', '.json', '.xml',
    '.yaml', '.yml', '.ini', '.cfg', '.conf', '.toml', '.env', '.gitignore'
}

CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.html', '.css', '.java',
    '.c', '.cpp', '.h', '.go', '.rs', '.rb', '.php',
    '.sh', '.bat', '.ps1', '.sql'
}

DOCUMENT_EXTENSIONS = {
    '.pdf', '.docx', '.xlsx', '.pptx', '.rtf', '.epub'
}

IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.ico'
}

VIDEO_EXTENSIONS = {
    '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv'
}

AUDIO_EXTENSIONS = {
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'
}

ARCHIVE_EXTENSIONS = {
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'
}

EXCLUDED_EXTENSIONS = {
    '.dll', '.exe', '.sys', '.obj', '.lib', '.pdb', '.so', '.dylib'
}

FILE_TYPE_CATEGORIES = {
    'all': '全部类型',
    'folder': '文件夹',
    'document': '文档',
    'code': '代码',
    'image': '图片',
    'video': '视频',
    'audio': '音频',
    'archive': '压缩包',
    'other': '其他'
}

def get_category_extensions(category: str) -> set:
    if category == 'document':
        return TEXT_EXTENSIONS | DOCUMENT_EXTENSIONS
    elif category == 'code':
        return CODE_EXTENSIONS
    elif category == 'image':
        return IMAGE_EXTENSIONS
    elif category == 'video':
        return VIDEO_EXTENSIONS
    elif category == 'audio':
        return AUDIO_EXTENSIONS
    elif category == 'archive':
        return ARCHIVE_EXTENSIONS
    else:
        return set()