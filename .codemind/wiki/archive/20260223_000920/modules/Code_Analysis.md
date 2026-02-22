# 模块: Code Analysis

# Code Analysis

# Code Analysis 模块文档

## 1. 模块概述
### 职责
负责代码的解析、分析及语义理解，提取代码中的符号、依赖关系和结构化信息。

### 定位
作为代码分析的核心模块，提供从源代码到结构化数据的转换能力，是后续代码理解、重构、优化等功能的基石。

### 设计意图
构建一个可扩展的代码分析框架，通过模块化设计支持多种编程语言的解析（基于Tree-sitter）、代码块构建、依赖分析及符号提取，为上层应用（如代码补全、代码导航、代码质量分析）提供结构化数据支持。


## 2. 包含文件
| 文件路径 | 作用 |
|----------|------|
| `codemind/parser/__init__.py` | 模块初始化文件，导出核心功能类/函数 |
| `codemind/parser/chunk_builder.py` | 代码块构建器，将代码拆分为逻辑块（如函数、类） |
| `codemind/parser/dependency_analyzer.py` | 依赖分析器，分析代码中的导入/引用关系 |
| `codemind/parser/file_scanner.py` | 文件扫描器，递归扫描指定目录下的源代码文件 |
| `codemind/parser/md5_cache.py` | MD5缓存管理器，缓存文件解析结果以提升性能 |
| `codemind/parser/models/__init__.py` | 数据模型模块初始化，导出核心模型类 |
| `codemind/parser/models/chunk.py` | 代码块模型（`Chunk`），定义代码块的结构和属性 |
| `codemind/parser/models/document.py` | 文档模型（`Document`），封装整个代码文件的解析结果 |
| `codemind/parser/models/symbol.py` | 符号模型（`Symbol`），定义代码符号（如变量、函数、类）的结构 |
| `codemind/parser/symbol_extractor.py` | 符号提取器，从解析后的代码树中提取符号信息 |
| `codemind/parser/tree_sitter_parser.py` | Tree-sitter解析器，使用Tree-sitter库解析源代码为语法树 |


## 3. 核心功能
- **代码解析**：通过Tree-sitter库将源代码转换为语法树（AST），支持多种编程语言（如Python、Java、C++等）。
- **代码块构建**：将代码拆分为逻辑块（如函数、类、方法），便于后续分析。
- **依赖分析**：识别代码中的导入语句、引用关系，生成依赖图。
- **符号提取**：从语法树中提取符号信息（如变量名、函数名、类名），并关联其定义和引用位置。
- **文件扫描**：递归扫描指定目录，收集所有源代码文件路径。
- **缓存管理**：通过MD5校验缓存文件解析结果，避免重复解析相同文件。
- **数据模型定义**：提供结构化的数据模型（如`Chunk`、`Symbol`、`Document`），统一代码分析结果的存储格式。


## 4. 关键组件
| 组件名称 | 类型 | 作用 |
|----------|------|------|
| `Chunk` | 类（`models.chunk.Chunk`） | 代码块模型，封装代码块的起始/结束位置、类型（函数/类/方法）及内容 |
| `Document` | 类（`models.document.Document`） | 文档模型，封装整个代码文件的解析结果（包括语法树、符号列表、依赖信息） |
| `Symbol` | 类（`models.symbol.Symbol`） | 符号模型，封装符号的名称、类型（变量/函数/类）、定义位置、引用位置及作用域 |
| `ChunkBuilder` | 类（`chunk_builder.ChunkBuilder`） | 代码块构建器，将语法树拆分为逻辑块 |
| `DependencyAnalyzer` | 类（`dependency_analyzer.DependencyAnalyzer`） | 依赖分析器，分析代码中的导入/引用关系，生成依赖图 |
| `FileScanner` | 类（`file_scanner.FileScanner`） | 文件扫描器，递归扫描目录下的源代码文件 |
| `SymbolExtractor` | 类（`symbol_extractor.SymbolExtractor`） | 符号提取器，从语法树中提取符号信息 |
| `TreeSitterParser` | 类（`tree_sitter_parser.TreeSitterParser`） | Tree-sitter解析器，使用Tree-sitter库解析源代码 |
| `MD5Cache` | 类（`md5_cache.MD5Cache`） | MD5缓存管理器，缓存文件解析结果 |


## 5. 使用方法
### 基本流程
1. **扫描文件**：使用`FileScanner`递归扫描指定目录，获取所有源代码文件路径。
2. **解析代码**：使用`TreeSitterParser`解析文件内容为语法树。
3. **提取符号**：使用`SymbolExtractor`从语法树中提取符号信息。
4. **分析依赖**：使用`DependencyAnalyzer`分析符号间的依赖关系。
5. **构建代码块**：使用`ChunkBuilder`将代码拆分为逻辑块（可选）。

### 示例代码
```python
from codemind.parser.file_scanner import FileScanner
from codemind.parser.tree_sitter_parser import TreeSitterParser
from codemind.parser.symbol_extractor import SymbolExtractor
from codemind.parser.dependency_analyzer import DependencyAnalyzer

# 1. 扫描指定目录下的源代码文件
scanner = FileScanner()
files = scanner.scan_directory("/path/to/your/code")

# 2. 初始化Tree-sitter解析器（需提前加载对应语言的解析器）
parser = TreeSitterParser(language="python")  # 支持python、java、c++等

# 3. 解析文件并提取符号
symbols = []
for file_path in files:
    # 解析文件内容为语法树
    code_tree = parser.parse_file(file_path)
    # 提取符号信息
    extractor = SymbolExtractor(code_tree)
    symbols.extend(extractor.extract())

# 4. 分析依赖关系
analyzer = DependencyAnalyzer()
dependencies = analyzer.analyze(symbols)

# 5. （可选）构建代码块
chunk_builder = ChunkBuilder()
chunks = chunk_builder.build(code_tree)

# 输出结果
print(f"提取的符号数量: {len(symbols)}")
print(f"依赖关系数量: {len(dependencies)}")
```


## 6. 依赖关系
### 内部依赖
- `codemind.parser.models`：数据模型模块，提供`Chunk`、`Symbol`、`Document`等核心模型类。

### 外部依赖
- **Tree-sitter**：代码解析库，用于将源代码转换为语法树（需提前安装对应语言的解析器，如`tree-sitter-python`）。
- **os**：Python标准库，用于文件路径操作（`file_scanner.py`）。
- **hashlib**：Python标准库，用于MD5计算（`md5_cache.py`）。
- **typing**：Python标准库，用于类型注解（如`List`、`Dict`）。


## 总结
`Code Analysis`模块通过模块化设计，将代码解析、分析、符号提取等功能拆分为独立组件，支持可扩展的代码理解流程。用户可通过简单的接口（如`FileScanner`、`TreeSitterParser`）快速获取结构化代码数据，适用于代码补全、代码导航、代码质量分析等场景。
