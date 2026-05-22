# P1 代码重构计划

## 概述

根据 AGENTS.md 第 204-211 行的 4 项 P1 代码重构任务，对 FileFinder 项目进行代码重构。

---

## 当前状态分析

### main_window.py 现状
- 共 3399 行，包含 15 个类 + 1 个独立函数
- MainWindow 本体仅约 907 行（27%），其余 2492 行被 14 个辅助类占据
- 应提取的类及其行数：

| 类名 | 行范围 | 行数 | 类型 |
|------|--------|------|------|
| ScanWorker | 226-457 | ~232 | 后台线程 |
| SearchWorker | 459-476 | ~18 | 后台线程 |
| WelcomePage | 480-668 | ~189 | 页面组件 |
| ScanProgressDialog | 670-876 | ~207 | 页面组件 |
| SearchScopePanel | 1311-1936 | ~626 | 面板组件 |
| _ScopeSelectionDialog | 1938-2491 | ~554 | 对话框 |
| LoadingSpinner | 178-223 | ~46 | 通用控件 |
| ElidedPathLabel | 878-919 | ~42 | 通用控件 |
| _RoundedPanel | 1031-1118 | ~88 | 通用控件 |
| CollapsibleSection | 1120-1251 | ~132 | 通用控件 |
| HoverInfoIcon | 1253-1286 | ~34 | 通用控件 |
| InfoIconLabel | 1288-1309 | ~22 | 通用控件 |

### _ModernMessageBox 重复情况
- `ui/main_window.py` 第 41-175 行：`ModernMessageBox` + `_styled_msg_box`（最完整版本，支持三按钮）
- `ui/widgets/filter_bar.py` 第 134-248 行：`_ModernMessageBox` + `_styled_msg_box`
- `ui/dialogs/settings_dialog.py` 第 14-128 行：`_ModernMessageBox` + `_styled_msg_box`
- 三处核心逻辑完全相同，main_window.py 版本功能最完整

### AnimatedRadioButton 重复情况
- `ui/main_window.py` 第 921-1028 行
- `ui/widgets/search_bar.py` 第 21-128 行
- `ui/widgets/filter_bar.py` 第 24-131 行
- 三处完全相同，零差异

### 设置对话框持久化现状
- `database/settings_dao.py` 已有完整的 save/load 函数，但**完全未被使用**
- `config.py` 已有 theme/language/max_results/content_max_size_mb 等字段，但 SettingsDialog 不读写
- SettingsDialog 打开时不加载已保存值，关闭时不保存值
- 存在两套并行的持久化系统（config.py JSON + settings_dao.py SQLite），需统一

---

## 重构方案

### 任务 1：提取重复的 _ModernMessageBox

**目标文件**：`ui/modern_dialog.py`（已存在，含 ModernDialogBase）

**操作**：
1. 以 main_window.py 版本为准（功能最完整），将 `ModernMessageBox` 类和 `_styled_msg_box` 函数添加到 `ui/modern_dialog.py` 末尾
2. 删除 `default_button` 参数（死代码，未被使用）
3. 类名统一为 `ModernMessageBox`（公开类，去掉下划线前缀）
4. 辅助函数命名为 `styled_msg_box`（去掉下划线前缀，作为模块级公开函数）
5. 在以下文件中删除本地实现，改为从 `ui/modern_dialog.py` 导入：
   - `ui/main_window.py`：删除第 41-175 行，添加 `from ui.modern_dialog import ModernDialogBase, ModernMessageBox, styled_msg_box`
   - `ui/widgets/filter_bar.py`：删除第 134-248 行，添加 `from ui.modern_dialog import ModernMessageBox, styled_msg_box`
   - `ui/dialogs/settings_dialog.py`：删除第 14-128 行，添加 `from ui.modern_dialog import ModernMessageBox, styled_msg_box`
6. 更新所有调用处：`_styled_msg_box(...)` → `styled_msg_box(...)`

### 任务 2：提取重复的 AnimatedRadioButton

**目标文件**：新建 `ui/widgets/animated_radio_button.py`

**操作**：
1. 从 main_window.py 第 921-1028 行提取 `AnimatedRadioButton` 类到新文件
2. 在以下文件中删除本地实现，改为导入：
   - `ui/main_window.py`：删除第 921-1028 行，添加 `from ui.widgets.animated_radio_button import AnimatedRadioButton`
   - `ui/widgets/search_bar.py`：删除第 21-128 行，添加 `from ui.widgets.animated_radio_button import AnimatedRadioButton`
   - `ui/widgets/filter_bar.py`：删除第 24-131 行，添加 `from ui.widgets.animated_radio_button import AnimatedRadioButton`

### 任务 3：拆分 main_window.py

**提取顺序**（按依赖关系，先提取无依赖的底层组件）：

#### 3.1 提取通用小控件 → `ui/widgets/common_widgets.py`

将以下小型通用控件合并到一个文件：
- `LoadingSpinner`（~46 行）
- `ElidedPathLabel`（~42 行）
- `_RoundedPanel`（~88 行）→ 改名为 `RoundedPanel`
- `CollapsibleSection`（~132 行）
- `HoverInfoIcon`（~34 行）
- `InfoIconLabel`（~22 行）

#### 3.2 提取 ScanWorker → `core/scan_worker.py`

- ScanWorker 是纯后台线程，不依赖 UI，属于 core 层
- 需要导入的：`QThread`, `Signal` from PySide6.QtCore；`DatabaseManager` from database.db_manager；`config` 相关函数
- 注意：ScanWorker 内部使用 `os.walk` 遍历目录，与 UI 完全解耦

#### 3.3 提取 SearchWorker → `core/search_worker.py`

- SearchWorker 也是纯后台线程，仅封装 SearchEngine 调用
- 需要导入的：`QThread`, `Signal` from PySide6.QtCore；`SearchEngine` from core.search_engine

#### 3.4 提取 WelcomePage → `ui/pages/welcome_page.py`

- 需要新建 `ui/pages/` 目录和 `__init__.py`
- WelcomePage 依赖：`DirListWidget`（from ui.widgets.filter_bar）、`FlowLayout`、样式常量
- WelcomePage 发出信号：`scan_requested(list[str])`

#### 3.5 提取 ScanProgressDialog → `ui/pages/scan_progress.py`

- 依赖：样式常量
- 发出信号：`cancel_requested()`

#### 3.6 提取 SearchScopePanel + _ScopeSelectionDialog

- `SearchScopePanel` → `ui/widgets/search_scope_panel.py`
- `_ScopeSelectionDialog` → `ui/dialogs/scope_selection_dialog.py`（改名为 `ScopeSelectionDialog`）
- SearchScopePanel 依赖：`AnimatedRadioButton`、`CollapsibleSection`、`ElidedPathLabel`、`HoverInfoIcon`、`FlowLayout`、`ScopeSelectionDialog`、`styled_msg_box`
- ScopeSelectionDialog 依赖：`ModernDialogBase`、`styled_msg_box`

#### 3.7 更新 main_window.py

- 删除所有已提取的类定义
- 添加所有新模块的导入
- MainWindow 类本体代码不变，仅调整导入和引用

**预期效果**：main_window.py 从 ~3399 行缩减到 ~1000 行（MainWindow 本体 + 导入语句）

### 任务 4：设置对话框持久化

**决策**：使用 `config.py`（JSON 文件）作为持久化存储，而非 `settings_dao.py`（SQLite）。

理由：
- config.py 已有对应字段且被业务代码引用
- JSON 文件更易调试和手动编辑
- 避免两套系统并存造成混乱

**操作**：

#### 4.1 在 config.py 中添加便捷 setter 函数

```python
def set_theme(theme: str) -> None:
    """设置界面主题"""
    cfg = load_config()
    cfg["general"]["theme"] = theme
    save_config(cfg)

def set_language(lang: str) -> None:
    """设置语言"""
    cfg = load_config()
    cfg["general"]["language"] = lang
    save_config(cfg)

def set_global_shortcut(shortcut: str) -> None:
    """设置全局快捷键"""
    cfg = load_config()
    cfg["general"]["global_shortcut"] = shortcut
    save_config(cfg)

def set_max_results(max_results: int) -> None:
    """设置最大搜索结果数"""
    cfg = load_config()
    cfg["search"]["max_results"] = max_results
    save_config(cfg)

def set_content_max_size_mb(size_mb: int) -> None:
    """设置内容搜索最大文件大小"""
    cfg = load_config()
    cfg["search"]["content_max_size_mb"] = size_mb
    save_config(cfg)

def get_theme() -> str: ...
def get_language() -> str: ...
def get_global_shortcut() -> str: ...
```

#### 4.2 修改 SettingsDialog

- `_init_ui()` 中：从 config.py 读取当前值设置到控件，而非硬编码默认索引
- 添加 `_save_settings()` 方法：将 5 个控件的当前值写入 config.py
- 重写 `accept()` 方法：调用 `_save_settings()` 后再 `super().accept()`
- 修正 `_on_reset()`：重置为 config.py 中的默认值而非硬编码索引，并保存
- 修正 config.py 中 `global_shortcut` 默认值为 `"Ctrl+Shift+F"` 以与 SettingsDialog 一致

#### 4.3 统一默认值映射

| 控件 | config.py key | 默认值 | combo 选项到值的映射 |
|------|--------------|--------|---------------------|
| theme_combo | general.theme | "system" | 0→"system", 1→"light", 2→"dark" |
| lang_combo | general.language | "zh_CN" | 0→"zh_CN" |
| shortcut_combo | general.global_shortcut | "Ctrl+Shift+F" | 0→"Ctrl+Shift+F", 1→"Alt+F", 2→"custom" |
| max_results_combo | search.max_results | 1000 | 0→100, 1→500, 2→1000, 3→2000, 4→5000 |
| max_file_size_combo | search.content_max_size_mb | 10 | 0→1, 1→5, 2→10, 3→20, 4→50 |

---

## 执行顺序

1. **任务 1**：提取 _ModernMessageBox（3 处重复消除）
2. **任务 2**：提取 AnimatedRadioButton（3 处重复消除）
3. **任务 3**：拆分 main_window.py（按 3.1→3.2→3.3→3.4→3.5→3.6→3.7 顺序）
4. **任务 4**：设置对话框持久化

任务 1 和 2 互相独立，可以并行执行。任务 3 依赖任务 1 和 2（因为 main_window.py 中的 ModernMessageBox 和 AnimatedRadioButton 需要先提取出去，再拆分其他类）。任务 4 与前三项独立。

---

## 假设与决策

1. **ModernMessageBox 放在 modern_dialog.py**：因为该文件已有 ModernDialogBase 基类，消息框是其自然扩展，避免创建过多小文件
2. **通用小控件合并到 common_widgets.py**：6 个小型控件（每个 20-130 行）各自独立文件过于碎片化，合并更易管理
3. **ScanWorker/SearchWorker 放在 core/** 而非 ui/workers/：它们是纯后台逻辑，不依赖 UI，按项目架构规范属于 core 层
4. **WelcomePage/ScanProgressDialog 放在 ui/pages/**：它们是独立的页面组件，不是 widget 也不是 dialog，新建 pages 子目录更清晰
5. **持久化使用 config.py**：而非 settings_dao.py，因为 config.py 已有对应字段且被业务代码引用
6. **_ScopeSelectionDialog 改名为 ScopeSelectionDialog**：提取为独立模块后应为公开类
7. **_RoundedPanel 改名为 RoundedPanel**：同上理由

---

## 验证步骤

1. 每完成一个提取任务后，运行程序确认无导入错误
2. 测试消息框功能：在主窗口、筛选栏、设置对话框中触发消息框，确认样式和功能正常
3. 测试 AnimatedRadioButton：在搜索栏匹配模式切换、筛选栏分类选择、搜索范围面板中确认动画正常
4. 测试主窗口页面切换：欢迎页 → 扫描进度 → 搜索页，确认所有页面正常显示
5. 测试磁盘扫描：触发扫描，确认 ScanWorker 正常工作和进度更新
6. 测试搜索功能：执行文件名搜索和内容搜索，确认 SearchWorker 正常
7. 测试搜索范围面板：打开搜索范围面板，确认目录选择对话框正常
8. 测试设置持久化：修改设置 → 关闭对话框 → 重新打开，确认值已保存
9. 测试设置重置：点击重置按钮，确认值恢复默认
