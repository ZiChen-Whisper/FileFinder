# 实现内容搜索秒出：SQLite FTS5 全文索引方案

## 摘要

根据 `CONTENT_SEARCH_RESEARCH.md` 调研，AnyTXT 等产品实现内容搜索秒出的核心原理是**预建全文索引**：在扫描阶段提取文件内容并构建倒排索引，搜索时直接查询索引而非实时扫描文件。本方案采用 **SQLite FTS5 + jieba 中文分词**，与现有 SQLite 数据库无缝集成，扫描时同时索引文件名和文件内容，实现内容搜索毫秒级响应。

## 当前状态分析

### 现有架构
- **文件名搜索**：`ScanWorker` 扫描目录 → `file_index_cache` 表存储元数据 → `SearchCache` 内存缓存 → `search_by_name()` 查询 → **毫秒级响应**
- **内容搜索**：`ContentSearcher.search()` → 实时遍历目录 → 逐文件打开解析 → 多线程搜索 → **秒级甚至分钟级响应**
- **扫描流程**：`ScanWorker` 只记录文件元数据（路径/名称/扩展名/大小/修改时间），**不提取文件内容**

### 核心差距
内容搜索慢的根本原因是**没有预建索引**，每次搜索都要实时打开文件。AnyTXT 的做法是扫描时就提取内容建倒排索引，搜索时查索引即可。

## 实施方案

### 1. 添加 jieba 依赖

**文件**: `requirements.txt`
- 添加 `jieba>=0.42.1`

### 2. 数据库层：添加 FTS5 全文索引表

**文件**: `database/db_manager.py`

#### 2.1 创建 FTS5 虚拟表
在 `_init_db()` 中添加：
```sql
CREATE VIRTUAL TABLE IF NOT EXISTS file_content_fts
USING fts5(
    file_path,          -- 文件路径（用于关联 file_index_cache）
    file_name,          -- 文件名（可按文件名搜内容）
    content,            -- 分词后的文件内容
    content='file_content_raw',  -- 内容表（外部内容模式）
    content_rowid='id',
    tokenize='unicode61'  -- 内置分词器，jieba 预处理后存入
)
```

同时创建原始内容存储表 `file_content_raw`：
```sql
CREATE TABLE IF NOT EXISTS file_content_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    content_text TEXT,           -- 原始提取的文本内容（用于预览上下文提取）
    content_tokenized TEXT,      -- jieba 分词后的文本（用于 FTS5 索引）
    indexed_at REAL DEFAULT (julianday('now'))
)
```

> **为什么用外部内容模式？** FTS5 的外部内容模式不存储原始内容副本，节省空间。搜索时通过 rowid 关联 `file_content_raw` 获取原始文本用于上下文提取。

#### 2.2 添加内容索引方法
- `insert_content_batch(rows, skip_cache_invalidate=False)` — 批量插入内容索引
- `insert_content_entry(file_path, content_text, content_tokenized)` — 单条插入
- `delete_content_entry(file_path)` — 删除内容索引
- `update_content_entry(file_path, content_text, content_tokenized)` — 更新内容索引
- `search_content(query_text, max_results=1000)` — FTS5 全文搜索，返回匹配的文件路径列表 + BM25 评分
- `get_content_by_path(file_path)` — 获取文件的原始文本内容（用于上下文提取）
- `has_content_index()` — 检查是否有内容索引
- `get_content_index_count()` — 获取内容索引条目数
- `clear_content_index()` — 清除内容索引

#### 2.3 FTS5 搜索实现
```python
def search_content(self, query_text: str, case_sensitive: bool = False,
                   max_results: int = 1000) -> list:
    """使用 FTS5 全文搜索，返回 (file_path, bm25_score) 列表"""
    # 对查询文本做 jieba 分词，用 AND 连接各词
    tokenized = tokenize_for_fts5(query_text)
    if not tokenized:
        return []

    conn = self._get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT fcr.file_path, bm25(file_content_fts) as rank
            FROM file_content_fts fts
            JOIN file_content_raw fcr ON fts.rowid = fcr.id
            WHERE file_content_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        ''', (tokenized, max_results))
        return [(row["file_path"], row["rank"]) for row in cursor.fetchall()]
    finally:
        conn.close()
```

### 3. 分词工具函数

**文件**: 新建 `utils/tokenizer.py`

```python
import jieba

def tokenize_for_fts5(text: str) -> str:
    """jieba 分词后以空格连接，用于 FTS5 索引和查询"""
    if not text or not text.strip():
        return ""
    words = jieba.cut_for_search(text)
    # 过滤空字符串和单字符（减少噪音），用空格连接
    tokens = [w for w in words if w.strip()]
    return " ".join(tokens)
```

> **注意**：jieba 首次加载词典约需 0.5-1 秒，应在程序启动时预加载。

### 4. 扫描层：扫描时同时索引内容

**文件**: `core/scan_worker.py`

#### 4.1 修改扫描流程
在 `run()` 方法中，扫描完文件元数据后，增加内容索引阶段：

```
原有流程：遍历目录 → 收集文件元数据 → 批量写入 file_index_cache
新增流程：遍历目录 → 收集文件元数据 → 批量写入 file_index_cache
         → 遍历已索引文件 → 提取文本内容 → jieba 分词 → 写入 file_content_fts
```

#### 4.2 具体实现
- 扫描阶段1（文件元数据）：保持不变
- 扫描阶段2（内容索引）：新增
  - 遍历 `file_index_cache` 中本次扫描路径下的文件
  - 使用 `ParserRegistry.parse()` 提取文本内容
  - 跳过目录条目和超大文件（>10MB）
  - 调用 `tokenize_for_fts5()` 分词
  - 批量写入 `file_content_raw` + `file_content_fts`
  - 发射进度信号（如 "正在索引内容... 123/456"）

#### 4.3 进度信号扩展
新增信号：
- `content_index_progress = Signal(int, int, str)` — (已索引文件数, 总文件数, 当前文件)

修改 `progress` 信号或新增阶段标识，让 UI 能区分"扫描文件"和"索引内容"两个阶段。

### 5. 搜索层：优先使用 FTS5 索引搜索

**文件**: `core/content_searcher.py`

#### 5.1 新增 FTS5 搜索方法
```python
def search_by_index(self, query: SearchQuery) -> List[SearchResult]:
    """使用 FTS5 全文索引搜索，毫秒级响应"""
    db = DatabaseManager()
    # 1. FTS5 搜索获取匹配文件路径
    matched = db.search_content(query.content_query, max_results=query.max_results)
    # 2. 对每个匹配文件，获取原始内容提取上下文行
    results = []
    for file_path, score in matched:
        content_text = db.get_content_by_path(file_path)
        if not content_text:
            continue
        content_matches = self._search_text_in_content(content_text, query)
        file_info = get_file_info(file_path)
        if file_info:
            results.append(SearchResult(
                file_item=file_info,
                match_reason='content',
                content_matches=content_matches
            ))
    return results
```

#### 5.2 修改搜索入口
```python
def search(self, query: SearchQuery) -> List[SearchResult]:
    self._canceled = False
    db = DatabaseManager()

    # 优先使用 FTS5 索引
    if db.has_content_index():
        return self.search_by_index(query)

    # 回退到实时扫描
    return self.search_realtime(query)  # 原有 search 逻辑
```

### 6. 搜索引擎层：适配索引搜索

**文件**: `core/search_engine.py`

修改 `search()` 方法，当内容索引存在时，联合搜索的逻辑需要调整：
- 文件名搜索：仍从 `file_index_cache` 查询
- 内容搜索：从 `file_content_fts` 查询
- 联合搜索：取两者交集

### 7. 增量索引：文件变更时更新内容索引

**文件**: `ui/main_window.py` 中的 `_on_fs_directory_changed` / `_on_fs_refresh_timeout`

当 `QFileSystemWatcher` 检测到文件变更时：
- 新增文件：提取内容 → 分词 → 写入 FTS5
- 修改文件：重新提取内容 → 更新 FTS5
- 删除文件：从 FTS5 删除

### 8. UI 层调整

**文件**: `ui/main_window.py`

- 扫描进度页面需显示两个阶段："扫描文件" 和 "索引内容"
- 状态栏显示内容索引状态（如 "已索引 12,345 个文件内容"）
- 搜索时如果走 FTS5 索引，不需要显示实时搜索进度（因为毫秒级完成）

### 9. 配置层

**文件**: `config.py`

- 添加 `content_index_status` 配置项，跟踪内容索引状态
- 添加 `is_content_indexed()` / `set_content_index_status()` 方法

## 实施步骤

1. **添加 jieba 依赖** — `requirements.txt`
2. **创建分词工具** — `utils/tokenizer.py`
3. **数据库层改造** — `database/db_manager.py`（FTS5 表 + 内容索引方法）
4. **扫描层改造** — `core/scan_worker.py`（增加内容索引阶段）
5. **搜索层改造** — `core/content_searcher.py`（FTS5 索引搜索 + 回退）
6. **搜索引擎适配** — `core/search_engine.py`
7. **增量索引** — `main_window.py` 文件监控回调
8. **UI 适配** — 扫描进度 + 状态栏

## 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 全文索引方案 | SQLite FTS5 | 与现有 SQLite 无缝集成，C 实现性能极高，内置 BM25 |
| 中文分词 | jieba 预处理 | 最成熟的 Python 中文分词库，`cut_for_search` 适合搜索场景 |
| 内容存储 | 外部内容模式 + file_content_raw 表 | 节省 FTS5 存储空间，保留原始文本用于上下文提取 |
| 扫描流程 | 两阶段（元数据 → 内容索引） | 先快速完成文件名索引，再逐步索引内容，用户可中途取消 |
| 回退策略 | 无索引时回退到实时扫描 | 保证功能可用性，用户未扫描时仍能搜索内容 |
| 索引更新 | 与文件系统监控联动 | 文件变更时增量更新内容索引，保持索引时效性 |

## 验证步骤

1. 运行扫描，确认两阶段进度正常显示
2. 扫描完成后，搜索文件内容，验证毫秒级响应
3. 搜索中文内容，验证 jieba 分词效果
4. 搜索 PDF/Word/Excel 内容，验证文档解析器 + FTS5 联合工作
5. 修改文件后，验证增量索引更新
6. 删除文件后，验证索引清理
7. 未扫描时搜索内容，验证回退到实时扫描
8. 检查数据库文件大小，确认索引空间合理
