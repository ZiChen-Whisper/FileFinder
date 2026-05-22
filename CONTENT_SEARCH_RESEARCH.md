# FileFinder 文件内容搜索技术调研报告

> 版本：v1.0 | 调研日期：2026-05-22
> 目的：调研 AnyTXT 等竞品的内容搜索实现方案，为 FileFinder 的 P1/P2 功能开发提供技术参考

---

## 目录

- [一、调研背景与范围](#一调研背景与范围)
- [二、竞品分析](#二竞品分析)
  - [2.1 AnyTXT Searcher](#21-anytxt-searcher)
  - [2.2 Everything (voidtools)](#22-everything-voidtools)
  - [2.3 DocFetcher](#23-docfetcher)
  - [2.4 ripgrep (rg)](#24-ripgrep-rg)
  - [2.5 Recoll](#25-recoll)
  - [2.6 Agent Ransack / FileSeek](#26-agent-ransack--fileseek)
  - [2.7 系统级搜索：Spotlight / Windows Search](#27-系统级搜索spotlight--windows-search)
  - [2.8 竞品综合对比](#28-竞品综合对比)
- [三、核心技术方案](#三核心技术方案)
  - [3.1 倒排索引](#31-倒排索引)
  - [3.2 mmap 流式搜索](#32-mmap-流式搜索)
  - [3.3 文档格式内容解析](#33-文档格式内容解析)
  - [3.4 正则表达式内容搜索](#34-正则表达式内容搜索)
  - [3.5 SQLite FTS5 全文搜索](#35-sqlite-fts5-全文搜索)
- [四、对 FileFinder 的实施建议](#四对-filefinder-的实施建议)
- [五、参考资源](#五参考资源)

---

## 一、调研背景与范围

### 1.1 调研目标

FileFinder 当前已实现文件名搜索（SQLite 索引 + 内存缓存）和纯文本内容搜索（多线程实时扫描）。根据 AGENTS.md 中的未完成功能清单，以下功能需要技术方案支撑：

| 功能 | 当前状态 | 调研重点 |
|------|---------|---------|
| PDF/Word/Excel 内容搜索 | ❌ 未实现 | 文档解析方案 |
| 内容正则搜索 | ❌ 未实现 | 正则搜索实现 |
| mmap 流式搜索 | ❌ P2 | 大文件搜索优化 |
| 倒排索引（全文索引） | ❌ P2 | 索引架构选型 |
| 中文分词 | ❌ 未实现 | 分词方案选型 |

### 1.2 调研范围

- **竞品**：AnyTXT Searcher、Everything、DocFetcher、ripgrep、Recoll、Agent Ransack/FileSeek、Spotlight、Windows Search
- **核心技术**：倒排索引、mmap、文档解析、正则搜索、SQLite FTS5、中文分词

---

## 二、竞品分析

### 2.1 AnyTXT Searcher

**定位**：本地全文搜索引擎，号称"本地磁盘的 Google"。支持 Windows/Linux/macOS，活跃用户 50 万+。

> ⚠️ **重要声明**：AnyTXT 是**闭源商业软件**，无公开源码。以下技术分析基于官方文档和第三方逆向分析文章。

#### 架构特点

AnyTXT 采用**双模式架构**：全文索引模式（主要）+ 无索引流式模式（辅助）。

**全文索引模式：**
- 首次启动扫描指定目录，构建自研 anydb 倒排索引数据库
- SSD 环境索引速度约 1 GB/分钟（实测 100K 文件/20GB 约 7 分 52 秒）
- 检索延迟：100 万文档平均 78ms
- 索引支持 AES-256 加密

**无索引流式模式（1.2.165 版本）：**
- 不预先建索引，直接 mmap 映射文件 → UTF-8 解码 → BM/KMP 匹配
- 适用于 UTF-8 编码文本文件的毫秒级搜索

#### mmap 流式搜索实现

这是 AnyTXT 最具特色的技术：

```
mmap 映射 → UTF-8 解码器 → Unicode 码点流 → BM/KMP 匹配引擎 → 命中记录
```

- **零拷贝**：`PROT_READ` + `MAP_PRIVATE`，绕过 read() 系统调用
- **双缓冲预加载**：当前块扫描完毕时异步读取下一块，隐藏 I/O 延迟
- **自适应分块**：小文件全量映射，大文件 64MB 固定块或自适应滑动窗口
- **懒加载结果**：匹配时仅记录偏移量，预览时才提取内容

#### 文件格式支持

内置 100+ 种格式解析引擎，采用**注册表模式**（Registry Pattern）：

| 分类 | 格式 |
|------|------|
| 纯文本/代码 | txt, py, js, html, cpp, md, log 等 |
| Microsoft Office | doc, docx, xls, xlsx, ppt, pptx |
| PDF | pdf（含扫描版 OCR） |
| 电子书 | mobi, epub, azw, chm, djvu |
| WPS Office | wps, et, dps |
| 思维导图 | xmind, mm, emmx |
| 国产格式 | OFD（开放版式文档） |
| 图片 OCR | png, jpg, bmp（内嵌 CPU/GPU 双引擎） |
| 二进制 | exe, dll（提取字符串） |
| 压缩包 | zip, rar 内部文件 |

#### 文件监控与增量索引

- **Windows**：`ReadDirectoryChangesW` API（内核级文件变更通知）
- **Linux**：`inotify`
- **macOS**：`FSEvents`
- 增量更新：新增 500 个 Word 文件约 3 秒完成

#### 搜索性能优化

| 优化维度 | 策略 |
|---------|------|
| 字符串匹配 | 长关键词用 Boyer-Moore，正则用轻量级 NFA |
| 并发处理 | 线程池（默认 CPU 核心数），共享无锁任务队列 |
| 内存保护 | 软限制 10,000 条结果，硬限制 512MB 内存触发 GC |
| 后台常驻 | 系统托盘 + 全局快捷键，避免重复建索引 |

#### 中文分词

AnyTXT 未公开其分词方案，推测采用 **N-Gram（Bigram 双字切分）** 或 **词典分词** 的混合方案。

---

### 2.2 Everything (voidtools)

**定位**：极致文件名搜索引擎，**不支持内容搜索**。

#### 核心技术

- **MFT 直接读取**：直接解析 NTFS 的 Master File Table，绕过 Windows API 遍历
- **USN Journal**：利用 NTFS 更新序列号日志实时追踪文件变更
- **内存索引**：百万文件约 1 分钟完成索引

| 指标 | 数值 |
|------|------|
| 百万文件索引时间 | ~1 分钟 |
| 搜索响应 | 毫秒级 |
| 内存占用 | 10-20MB |
| 安装包大小 | ~1.5MB |

**开源情况**：非开源（专有免费软件）。

**借鉴意义**：Everything 的 MFT 方案是 Windows 文件名搜索的极致优化，但实现复杂度极高，不适合 Python 项目直接借鉴。其"内存索引 + USN Journal 增量更新"的架构理念与 FileFinder 一致。

---

### 2.3 DocFetcher

**定位**：开源桌面全文搜索工具，基于 Apache Lucene。

#### 核心技术

- **Apache Lucene 倒排索引**：完整的倒排索引、分词、BM25 评分
- **增量索引**：检测文件变更，仅重新索引修改过的文件
- **便携式索引**：索引可存储在 USB 设备上

#### 文件格式支持

PDF, DOCX, XLSX, PPTX, ODT, HTML, EPUB, CHM, RTF, mbox 等，支持自动解压 ZIP/TAR/RAR 内部文件。

**开源情况**：完全开源（Apache 2.0），GitHub: https://github.com/docfetcher/DocFetcher

**借鉴意义**：
- 证明了 Lucene 可作为桌面搜索的可靠后端（Python 对应库为 Whoosh）
- 每种文件格式独立 Parser 的设计与 FileFinder 的 ParserRegistry 一致
- 压缩包内容搜索值得借鉴

---

### 2.4 ripgrep (rg)

**定位**：命令行内容搜索工具，采用**无索引实时扫描**方案，通过极致工程优化实现高性能。

#### 核心技术

1. **Rust regex 引擎**：基于有限自动机 (DFA/NFA)，内置 SIMD 加速（SSE2/AVX2）
2. **智能搜索策略**：单文件用 mmap，多文件用增量缓冲（避免大量 mmap 的 TLB 冲突）
3. **无锁并行遍历**：Chase-Lev work-stealing deque 实现工作窃取调度
4. **字面量预过滤**：从正则中提取字面量前缀，快速过滤候选行

#### 性能数据

| 场景 | ripgrep | GNU grep | 提升 |
|------|---------|----------|------|
| Linux 内核搜索（字面量） | 0.063s | 0.674s | 10x |
| 13GB 单文件搜索（Unicode） | 1.042s | 6.577s | 6x |

**开源情况**：完全开源（MIT/Unlicense），GitHub: https://github.com/BurntSushi/ripgrep

**借鉴意义**：
- **mmap 策略**：单文件 mmap + 多文件增量缓冲的区分值得借鉴
- **字面量预过滤**：FileFinder 的 `name_searcher.py` 已有类似实现，`content_searcher.py` 也可引入
- **编码支持**：ripgrep 支持 UTF-8/UTF-16/GBK 等多种编码，与 FileFinder 的 `charset-normalizer` 方案一致

---

### 2.5 Recoll

**定位**：Linux 桌面全文搜索工具，基于 Xapian 搜索引擎。

#### 核心技术

- **Xapian 全文索引**：C++ 信息检索库，BM25 权重排序
- **文本提取层**：支持调用外部程序解析各种文档格式
- **嵌套文档**：可索引压缩包内邮件附件中的文档
- **OCR**：通过 Tesseract OCR 支持扫描版 PDF

**开源情况**：完全开源（GPL），源码：https://framagit.org/medoc93/recoll

**借鉴意义**：Xapian 的 Python 绑定 (`python-xapian`) 可作为 FileFinder 未来全文索引的可选方案。

---

### 2.6 Agent Ransack / FileSeek

**定位**：Windows 桌面搜索工具（Mythicsoft 出品）。

#### 核心特点

- **Agent Ransack**：无索引实时扫描，零预处理
- **FileSeek**：支持**双模式切换**——无索引模式（实时扫描）+ 索引模式（预建索引）
- 支持搜索压缩包内部文件内容（ZIP, RAR, 7z）
- 支持 SQL-like 高级查询语法

**开源情况**：非开源（专有免费软件）。

**借鉴意义**：
- **双模式设计**：允许用户在"即时性"和"速度"之间选择，是值得借鉴的 UX 设计
- **压缩包内容搜索**：FileFinder 未来可扩展的方向

---

### 2.7 系统级搜索：Spotlight / Windows Search

#### macOS Spotlight

- **架构**：mds (metadata server) + mdworker (导入器) + FSEvents (文件监控)
- **插件系统**：mdimporter 插件，每种文件类型一个
- **流程**：Protocol Handler → mdimporter → Word Breaker → Stemmer → 索引

#### Windows Search

- **架构**：SearchIndexer.exe + ESE 数据库 (Jet 引擎) + IFilter 接口
- **插件系统**：IFilter 接口，每种文件类型注册一个 IFilter
- **流程**：Protocol Handler → IFilter → Word Breaker → Stemmer → ESE 索引
- **增量更新**：USN Journal

**共同借鉴意义**：
- **插件化内容解析**：Spotlight 的 mdimporter 和 Windows Search 的 IFilter 都是优秀的插件化范例，与 FileFinder 的 ParserRegistry 设计理念一致
- **分层架构**：Protocol Handler → Content Filter → Word Breaker → Index 的分层设计，职责清晰

---

### 2.8 竞品综合对比

| 维度 | AnyTXT | Everything | DocFetcher | ripgrep | Recoll | FileSeek |
|------|--------|-----------|------------|---------|--------|----------|
| **搜索类型** | 文件名+内容 | 仅文件名 | 文件名+内容 | 仅内容 | 文件名+内容 | 文件名+内容 |
| **索引方式** | 自研倒排索引 | MFT 直接读取 | Lucene | 无索引 | Xapian | 无/可选索引 |
| **内容搜索** | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **PDF 搜索** | ✅ | — | ✅ | 需预处理 | ✅ | ❌ |
| **Word/Excel** | ✅ | — | ✅ | ❌ | ✅ | ❌ |
| **压缩包搜索** | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| **正则搜索** | ✅ | 文件名 | ✅ | ✅ | ✅ | ✅ |
| **搜索速度** | 78ms/百万文档 | 毫秒级 | 毫秒级 | 极快 | 毫秒级 | 中等 |
| **开源** | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ |
| **语言** | C/C++ | C | Java | Rust | C++/Python | C# |

---

## 三、核心技术方案

### 3.1 倒排索引

#### 3.1.1 数据结构

倒排索引的核心是 **Term → Posting List** 映射：

```
倒排索引 = {
    "python" → [doc_1(位置: [3,15]), doc_5(位置: [7]), doc_12(位置: [1,22,45])],
    "搜索"   → [doc_2(位置: [10]), doc_5(位置: [3,20]), doc_8(位置: [5])],
}
```

每个 Posting List 条目包含：
- **doc_id**：文档唯一标识
- **term_frequency**：词频（TF）
- **positions**：词在文档中的位置（用于短语搜索和高亮）

#### 3.1.2 Python 实现方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **SQLite FTS5** | C 实现、性能极高、内置 BM25、与现有 SQLite 无缝集成 | 默认分词器不支持中文 | ⭐⭐⭐⭐⭐ |
| **Whoosh** | 纯 Python、API 类 Lucene、可集成 jieba | 性能不如 C 方案、维护不活跃 | ⭐⭐⭐⭐ |
| **自定义实现** | 完全可控 | 开发量大、性能取决于实现 | ⭐⭐ |

**推荐 SQLite FTS5**，理由：
1. 项目已使用 SQLite，FTS5 无缝集成，无需额外依赖
2. 基于 C 实现，1500 万行数据搜索约 3 秒（微信团队验证）
3. 内置 BM25 排序、snippet() 高亮、增量更新
4. Python 标准库 `sqlite3` 直接支持

#### 3.1.3 中文分词方案

| 方案 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| **jieba 预处理（推荐）** | 索引前用 jieba 分词，空格连接后存入 FTS5 | 实现最简单、效果好 | 存储略增 |
| **N-Gram (Bigram)** | 按每 2 个字符切分 | 无需词典、召回率高 | 索引体积大 |
| **FTS5 trigram** | 内置 3 字符切分分词器 | 无需外部分词 | 索引约 3 倍体积 |
| **自定义 C Tokenizer** | 编写 C 扩展注册到 FTS5 | 性能最佳 | 编译复杂、跨平台差 |

**推荐方案**：P1 阶段用 jieba 预处理 + FTS5 unicode61 分词器，P2 阶段按需升级。

#### 3.1.4 压缩技术

| 技术 | 适用场景 | Python 库 |
|------|---------|----------|
| **VB 编码** | Posting List 中 doc_id 差值编码 | 自行实现（约 20 行代码） |
| **Roaring Bitmap** | 密集 Posting List 的交集/并集运算 | `pyroaring` |

> 对于本地文件搜索（通常 < 100 万文件），Python `set` 交集已足够高效，压缩技术可在索引规模扩大后引入。

---

### 3.2 mmap 流式搜索

#### 3.2.1 原理

`mmap` 将文件直接映射到进程虚拟地址空间，由操作系统按需加载页面：

```
传统方式：文件 → 内核缓冲区 → 用户缓冲区 → 处理（两次拷贝）
mmap 方式：文件 → 虚拟内存 → 直接处理（零拷贝）
```

#### 3.2.2 性能对比

| 维度 | `f.read()` | `f.readline()` | `mmap` |
|------|-----------|---------------|--------|
| 内存占用 | O(文件大小) | O(行大小) | O(实际访问页面) |
| 小文件 (<1MB) | 最快 | 较慢 | 略慢（映射开销） |
| 中等文件 (1-100MB) | 内存压力大 | IO 次数多 | **最优** |
| 大文件 (>100MB) | 可能 OOM | IO 瓶颈 | **最优** |
| 随机访问 | 差 | 差 | **最优** |

#### 3.2.3 ripgrep 的策略选择

ripgrep 的实践证明了**区分场景**的重要性：

| 场景 | 策略 | 原因 |
|------|------|------|
| 单文件搜索 | mmap | 零拷贝，随机访问快 |
| 多文件搜索 | 增量缓冲 (read) | 避免大量 mmap 导致 TLB 冲突和页面错误 |

#### 3.2.4 编码处理

mmap 返回原始字节，编码处理是主要复杂点：

- **UTF-8**：自同步编码，可安全搜索 ASCII 子串
- **GBK**：变长编码（1-2 字节），搜索中文需确保字节对齐
- **推荐策略**：先检测编码 → 将查询编码为字节 → 在 mmap 字节流中匹配 → 匹配字节解码回字符串

#### 3.2.5 Python 实现

```python
import mmap

def mmap_search(file_path: str, pattern: bytes) -> list:
    """mmap 文件搜索"""
    matches = []
    with open(file_path, 'rb') as f:
        with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
            pos = mm.find(pattern)
            while pos != -1:
                # 提取所在行
                line_start = mm.rfind(b'\n', 0, pos) + 1
                line_end = mm.find(b'\n', pos)
                if line_end == -1:
                    line_end = len(mm)
                matches.append(mm[line_start:line_end])
                pos = mm.find(pattern, pos + 1)
    return matches
```

**对 FileFinder 的建议**：小文件（<10MB）继续用 `read()`，大文件（>10MB）切换到 mmap，复用 `utils/encoding.py` 的编码检测。

---

### 3.3 文档格式内容解析

#### 3.3.1 PDF 解析

| 方案 | 速度 | 内存 | 表格 | 项目已用 |
|------|------|------|------|---------|
| **PyMuPDF (fitz)** | 极快 (2.3s/1000页) | 低 (45MB) | 支持 | ✅ 预览 |
| pdfplumber | 中等 | 中 | 最佳 | ❌ |
| pdfminer.six | 慢 | 高 | 不支持 | ❌ |

**推荐 PyMuPDF**（项目已依赖）：

```python
import fitz

class PDFParser(FileParser):
    def can_parse(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() == '.pdf'

    def parse(self, file_path: str) -> Optional[str]:
        try:
            doc = fitz.open(file_path)
            text_parts = [page.get_text("text") for page in doc]
            doc.close()
            full_text = '\n'.join(text_parts)
            return full_text if full_text.strip() else None
        except Exception as e:
            logger.warning(f"PDF 解析失败: {file_path}, {e}")
            return None
```

#### 3.3.2 Word 解析

**推荐 python-docx**（项目已依赖）：

```python
from docx import Document

class DocxParser(FileParser):
    def can_parse(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in ('.docx',)

    def parse(self, file_path: str) -> Optional[str]:
        try:
            doc = Document(file_path)
            text_parts = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    row_text = ' '.join(cell.text for cell in row.cells)
                    if row_text.strip():
                        text_parts.append(row_text)
            return '\n'.join(text_parts) or None
        except Exception as e:
            logger.warning(f"Word 解析失败: {file_path}, {e}")
            return None
```

> ⚠️ python-docx 仅支持 .docx，不支持旧版 .doc 格式。

#### 3.3.3 Excel 解析

**推荐 openpyxl**（项目已依赖）：

```python
import openpyxl

class XlsxParser(FileParser):
    def can_parse(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in ('.xlsx', '.xlsm')

    def parse(self, file_path: str) -> Optional[str]:
        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            text_parts = []
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    row_text = ' '.join(str(c) if c else '' for c in row)
                    if row_text.strip():
                        text_parts.append(row_text)
            wb.close()
            return '\n'.join(text_parts) or None
        except Exception as e:
            logger.warning(f"Excel 解析失败: {file_path}, {e}")
            return None
```

> `read_only=True` 大幅降低内存占用，`data_only=True` 只读值不读公式。

#### 3.3.4 PPT 解析

**推荐 python-pptx**（项目已依赖）：

```python
from pptx import Presentation

class PptxParser(FileParser):
    def can_parse(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in ('.pptx',)

    def parse(self, file_path: str) -> Optional[str]:
        try:
            prs = Presentation(file_path)
            text_parts = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for para in shape.text_frame.paragraphs:
                            if para.text.strip():
                                text_parts.append(para.text)
                    if shape.has_table:
                        for row in shape.table.rows:
                            row_text = ' '.join(cell.text for cell in row.cells)
                            if row_text.strip():
                                text_parts.append(row_text)
            return '\n'.join(text_parts) or None
        except Exception as e:
            logger.warning(f"PPT 解析失败: {file_path}, {e}")
            return None
```

#### 3.3.5 统一架构（Parser Registry）

项目已有 `ParserRegistry` 模式，只需注册新解析器：

```python
class ParserRegistry:
    def __init__(self):
        self._parsers: List[FileParser] = [
            TextParser(),       # 已有
            PDFParser(),        # 新增
            DocxParser(),       # 新增
            XlsxParser(),       # 新增
            PptxParser(),       # 新增
        ]
```

**所有依赖已在 requirements.txt 中，无需额外安装。**

---

### 3.4 正则表达式内容搜索

#### 3.4.1 当前问题

`content_searcher.py` 使用 `re.escape(pattern)` 强制转义，只支持关键词搜索。

#### 3.4.2 改进方案

```python
# 根据搜索模式决定是否转义
if query.content_mode == 'regex':
    regex = re.compile(pattern, flags)
else:
    regex = re.compile(re.escape(pattern), flags)
```

#### 3.4.3 性能优化技巧

| 优化项 | 说明 | 效果 |
|--------|------|------|
| 预编译正则 | `re.compile()` 避免重复编译 | 5-10x 提升 |
| 使用具体字符类 | `[0-9]` 优于 `\d` | 减少回溯 |
| 避免贪婪量词 | `.*?` 优于 `.*` | 减少回溯次数 |
| 使用锚点 | `^` 和 `$` 限制范围 | 大幅减少匹配尝试 |
| 非捕获组 | `(?:...)` 优于 `(...)` | 减少内存分配 |

#### 3.4.4 第三方 `regex` 模块

`pip install regex` 提供比标准库更强大的正则引擎：
- API 完全兼容 `re`，可直接替换 `import re` 为 `import regex as re`
- 支持 Unicode 属性（如 `\p{Han}` 匹配中文）
- 某些场景性能优于 `re`

---

### 3.5 SQLite FTS5 全文搜索

#### 3.5.1 基本用法

```python
import sqlite3

# 创建 FTS5 虚拟表
conn.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS file_content_fts
    USING fts5(
        file_name,
        content,
        content='file_index_cache',
        content_rowid='id',
        tokenize='unicode61'
    )
''')

# 搜索（内置 BM25 排序 + snippet 高亮）
cursor = conn.execute('''
    SELECT rowid, file_name,
           snippet(file_content_fts, 2, '<mark>', '</mark>', '...', 32),
           bm25(file_content_fts) as rank
    FROM file_content_fts
    WHERE file_content_fts MATCH ?
    ORDER BY rank LIMIT ?
''', (query, limit))
```

#### 3.5.2 查询语法

| 语法 | 说明 | 示例 |
|------|------|------|
| `term` | 基本搜索 | `python` |
| `"phrase"` | 短语搜索 | `"def main"` |
| `AND` / `OR` / `NOT` | 布尔运算 | `python AND search` |
| `NEAR/n` | 近邻搜索 | `file NEAR/3 search` |
| `*` | 前缀匹配 | `pyth*` |
| `column:term` | 指定列搜索 | `content:python` |

#### 3.5.3 中文分词集成

**推荐方案：jieba 预处理**

```python
import jieba

def tokenize_for_fts5(text: str) -> str:
    """jieba 分词后以空格连接"""
    words = jieba.cut_for_search(text)
    return ' '.join(w for w in words if w.strip() and len(w) > 1)

# 索引时
content_tokenized = tokenize_for_fts5("我来到北京清华大学")
# → "我 来到 北京 清华 华大 大学 清华大学"

# 搜索时也要同样处理
query_tokenized = tokenize_for_fts5("清华大学")
# → "清华 大学"
```

#### 3.5.4 与自定义倒排索引对比

| 维度 | SQLite FTS5 | 自定义 / Whoosh |
|------|------------|----------------|
| 实现复杂度 | 低（SQL 即可） | 高 |
| 性能 | 极高（C 实现） | 中 |
| 中文支持 | 需预处理 | 可直接集成 jieba |
| 增量更新 | 原生支持 | 需自行实现 |
| 与现有系统集成 | **最佳**（已用 SQLite） | 需额外存储 |
| 依赖 | 无（Python 内置） | Whoosh 需 pip 安装 |

---

## 四、对 FileFinder 的实施建议

### 4.1 P1 阶段（当前优先级最高）

#### ① 文档解析器扩展（最高优先级）

**工作量**：约 2-3 小时 | **依赖**：全部已在 requirements.txt 中

在 `core/file_parser.py` 中注册 PDFParser、DocxParser、XlsxParser、PptxParser。所有解析库项目已依赖，ParserRegistry 架构已就绪，只需实现 `can_parse()` 和 `parse()` 方法。

#### ② 内容正则搜索（高优先级）

**工作量**：约 30 分钟

修改 `core/content_searcher.py`，根据 `SearchQuery.content_mode` 字段决定是否 `re.escape()`。`SearchQuery` 已有 `content_mode` 字段，UI 层需添加模式切换控件。

#### ③ mmap 大文件优化（中优先级）

**工作量**：约 1-2 小时

在 `content_searcher.py` 的 `_search_file()` 中，对 >10MB 文件使用 mmap 替代 `read()`。复用 `utils/encoding.py` 的编码检测能力。

### 4.2 P2 阶段

#### ④ SQLite FTS5 全文索引

**工作量**：约 1-2 天

- 在 `db_manager.py` 中添加 FTS5 虚拟表
- 扫描阶段构建索引（调用文档解析器提取文本 → jieba 分词 → 写入 FTS5）
- 搜索阶段使用 FTS5 MATCH 查询替代实时扫描
- 增量更新：文件变更时 DELETE + INSERT 对应条目

#### ⑤ 中文分词

**工作量**：约 0.5 天（jieba 集成）

- `pip install jieba`（约 50MB 词典）
- 索引时用 `jieba.cut_for_search()` 分词
- 搜索时对查询做同样分词处理
- 可加载自定义词典（文件类型相关术语）

#### ⑥ 压缩包内容搜索

**工作量**：约 1 天

- 使用 Python 标准库 `zipfile` / `tarfile` 解压
- 递归解析压缩包内部文件
- 参考 DocFetcher 和 FileSeek 的实现

### 4.3 技术路线总结

```
P1（当前）                    P2（未来）
┌──────────────────┐        ┌──────────────────────┐
│ 文档解析器扩展    │        │ SQLite FTS5 全文索引   │
│ (PDF/Word/Excel) │───────→│ + jieba 中文分词       │
├──────────────────┤        ├──────────────────────┤
│ 内容正则搜索      │        │ mmap 流式搜索          │
│ (改一行代码)      │        │ (大文件优化)           │
├──────────────────┤        ├──────────────────────┤
│ mmap 大文件优化   │        │ 压缩包内容搜索          │
│ (>10MB 文件)     │        │ (zip/tar/rar)         │
└──────────────────┘        └──────────────────────┘
```

---

## 五、参考资源

### 竞品

| 资源 | 链接 |
|------|------|
| AnyTXT 官网 | https://anytxt.net |
| Everything 官网 | https://www.voidtools.com |
| DocFetcher (GitHub) | https://github.com/docfetcher/DocFetcher |
| ripgrep (GitHub) | https://github.com/BurntSushi/ripgrep |
| Recoll 源码 | https://framagit.org/medoc93/recoll |

### 技术文档

| 资源 | 链接 |
|------|------|
| SQLite FTS5 官方文档 | https://www.sqlite.org/fts5.html |
| PyMuPDF 文档 | https://pymupdf.readthedocs.io/ |
| python-docx 文档 | https://python-docx.readthedocs.io/ |
| openpyxl 文档 | https://openpyxl.readthedocs.io/ |
| python-pptx 文档 | https://python-pptx.readthedocs.io/ |
| jieba 分词 | https://github.com/fxsjy/jieba |
| Whoosh 文档 | https://whoosh.readthedocs.io/ |
| Simple Tokenizer (FTS5 中文) | https://github.com/nicemayi/sqlite3-jieba |

### 技术分析文章

| 资源 | 链接 |
|------|------|
| AnyTXT mmap 技术分析 | https://blog.csdn.net/weixin_35706067/article/details/152722924 |
| AnyTXT 性能评测 | https://blog.51cto.com/u_16517116/14249104 |
