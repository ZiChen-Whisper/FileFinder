import fnmatch
from datetime import datetime
from typing import List, Tuple
from models import FileItem, SearchQuery
from database.db_manager import DatabaseManager

def fuzzy_match(name: str, pattern: str, case_sensitive: bool = False) -> bool:
    if not case_sensitive:
        name = name.lower()
        pattern = pattern.lower()
    if not pattern:
        return True
    return pattern in name

def wildcard_match(name: str, pattern: str, case_sensitive: bool = False) -> bool:
    if not case_sensitive:
        name = name.lower()
        pattern = pattern.lower()
    return fnmatch.fnmatch(name, pattern)

def _calculate_name_relevance(name: str, pattern: str, case_sensitive: bool = False) -> int:
    if not pattern:
        return 0

    if not case_sensitive:
        name = name.lower()
        pattern = pattern.lower()

    pattern_len = len(pattern)

    if name == pattern:
        return 100 + pattern_len
    if name.startswith(pattern):
        return 80 + pattern_len

    pos = name.find(pattern)
    if pos == -1:
        return 0

    word_boundaries = {'_', '-', '.', ' '}
    if pos > 0 and name[pos - 1] in word_boundaries:
        return 60 + pattern_len
    if pos > 0 and name[pos - 1].islower() and name[pos].isupper():
        return 60 + pattern_len

    return 40 + pattern_len

def _row_to_file_item(row) -> FileItem:
    mod_ts = row["modified_time"]
    if isinstance(mod_ts, (int, float)):
        mod_dt = datetime.fromtimestamp(mod_ts)
    else:
        mod_dt = datetime.now()
    return FileItem(
        path=row["path"],
        name=row["name"],
        extension=row["extension"] or "",
        size=row["size"] or 0,
        modified_time=mod_dt,
        created_time=mod_dt,
        is_directory=bool(row["is_directory"]) if "is_directory" in row.keys() else False
    )

def search_by_name(query: SearchQuery) -> List[Tuple[int, FileItem]]:
    db = DatabaseManager()
    pattern = query.name_query if query.has_name_query else ""

    db_results = db.search_files(
        pattern=pattern,
        case_sensitive=query.name_case_sensitive,
        file_types=query.file_types if query.file_types else None,
        exclude_file_types=query.exclude_file_types if query.exclude_file_types else None,
        size_min=query.size_min,
        size_max=query.size_max,
        max_results=query.max_results * 2
    )

    results = []
    for row in db_results:
        item = _row_to_file_item(row)
        name = item.name

        if query.has_name_query:
            pat = query.name_query
            if query.name_mode == 'exact':
                match = (name == pat) if query.name_case_sensitive else (name.lower() == pat.lower())
            elif query.name_mode == 'wildcard':
                match = wildcard_match(name, pat, query.name_case_sensitive)
            else:
                match = fuzzy_match(name, pat, query.name_case_sensitive)

            if match:
                score = _calculate_name_relevance(name, pat, query.name_case_sensitive)
                results.append((score, item))
        else:
            results.append((0, item))

        if len(results) >= query.max_results:
            break

    results.sort(key=lambda x: x[0], reverse=True)
    return results[:query.max_results]

def get_index_count() -> int:
    db = DatabaseManager()
    return db.get_index_count()
