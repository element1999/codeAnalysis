# 模块: Code Analysis & Parsing

# Code Analysis & Parsing

# Code Analysis & Parsing 模块文档

## 1. 模块概述
**职责**：负责源代码的解析、分析及文档处理，将原始代码转换为结构化的中间表示（如代码块、文档、符号）。  
**定位**：作为代码理解的核心模块，为上层模块（如代码生成、文档生成）提供结构化的代码数据。  
**设计意图**：通过统一的解析流程和模型定义，实现代码的标准化处理，降低上层模块的复杂度，提升代码分析的效率和准确性。


## 2. 包含文件
| 文件路径 | 作用 |
|----------|------|
| `codemind/parser/chunk_builder.py` | 负责将代码分割为逻辑块（Chunk），并构建块之间的关系 |
| `codemind/parser/dependency_analyzer.py` | 分析代码间的依赖关系（如导入、调用） |
| `codemind/parser/file_scanner.py` | 扫描指定目录下的源代码文件，收集文件路径 |
| `codemind/parser/md5_cache.py` | 使用MD5哈希缓存解析结果，避免重复解析相同文件 |
| `codemind/parser/symbol_extractor.py` | 从代码中提取符号（函数、类、变量等） |
| `codemind/parser/tree_sitter_parser.py` | 使用Tree-sitter库解析源代码为抽象语法树（AST） |
| `codemind/parser/models/chunk.py` | 定义代码块（Chunk）的数据模型 |
| `codemind/parser/models/document.py` | 定义文档（Document）的数据模型 |
| `codemind/parser/models/symbol.py` | 定义符号（Symbol）的数据模型 |
| `codemind/parser/__init__.py` | 模块初始化文件，导出核心类和函数 |


## 3. 核心功能
- **代码解析**：使用Tree-sitter将源代码解析为AST，支持多种编程语言（如Python、Java）。  
- **依赖分析**：识别代码中的导入语句、函数调用等依赖关系，构建依赖图。  
- **符号提取**：从AST中提取函数、类、变量等符号，并记录其位置和属性。  
- **代码块构建**：将代码按逻辑单元（如函数、类）分割为代码块，便于后续处理。  
- **文档处理**：提取代码中的注释、文档字符串，关联到对应的符号或代码块。  
- **缓存管理**：通过MD5哈希缓存解析结果，提升重复解析的效率。


## 4. 关键组件
### 4.1 核心类
| 类名 | 所属文件 | 作用 |
|------|----------|------|
| `ChunkBuilder` | `chunk_builder.py` | 构建代码块（Chunk），处理块间的嵌套和依赖关系 |
| `DependencyAnalyzer` | `dependency_analyzer.py` | 分析代码依赖，生成依赖图 |
| `FileScanner` | `file_scanner.py` | 递归扫描目录，收集源代码文件路径 |
| `MD5Cache` | `md5_cache.py` | 管理解析结果的缓存，避免重复解析 |
| `SymbolExtractor` | `symbol_extractor.py` | 从AST中提取符号（函数、类、变量） |
| `TreeSitterParser` | `tree_sitter_parser.py` | 使用Tree-sitter解析源代码为AST |
| `Chunk` | `models/chunk.py` | 代码块的数据模型，包含代码内容、位置、父块等信息 |
| `Document` | `models/document.py` | 文档的数据模型，关联代码与文档（注释、文档字符串） |
| `Symbol` | `models/symbol.py` | 符号的数据模型，包含符号名称、类型、位置、所属文档等信息 |

### 4.2 核心函数
- `parse_code(file_path: str) -> AST`（`tree_sitter_parser.py`）：解析指定文件的代码为AST。  
- `extract_symbols(ast: AST) -> List[Symbol]`（`symbol_extractor.py`）：从AST中提取符号列表。  
- `build_chunks(ast: AST) -> List[Chunk]`（`chunk_builder.py`）：将AST分割为代码块列表。  
- `analyze_dependencies(chunks: List[Chunk]) -> Dict[str, List[str]]`（`dependency_analyzer.py`）：分析代码块间的依赖关系。  


## 5. 使用方法
以下是模块的典型使用流程（以解析Python文件为例）：

```python
from codemind.parser.tree_sitter_parser import TreeSitterParser
from codemind.parser.file_scanner import FileScanner
from codemind.parser.symbol_extractor import SymbolExtractor
from codemind.parser.chunk_builder import ChunkBuilder
from codemind.parser.dependency_analyzer import DependencyAnalyzer
from codemind.parser.md5_cache import MD5Cache

# 1. 初始化缓存（可选，提升重复解析效率）
cache = MD5Cache()

# 2. 扫描源代码文件
scanner = FileScanner()
file_paths = scanner.scan_directory("/path/to/source/code")

# 3. 解析文件并提取AST
parser = TreeSitterParser(language="python")
ast_list = []
for file_path in file_paths:
    ast = parser.parse_code(file_path, cache=cache)
    ast_list.append(ast)

# 4. 提取符号
extractor = SymbolExtractor()
symbols = []
for ast in ast_list:
    symbols.extend(extractor.extract_symbols(ast))

# 5. 构建代码块
builder = ChunkBuilder()
chunks = []
for ast in ast_list:
    chunks.extend(builder.build_chunks(ast))

# 6. 分析依赖关系
analyzer = DependencyAnalyzer()
dependencies = analyzer.analyze_dependencies(chunks)

# 7. 使用结果（如生成文档、代码分析报告）
print(f"提取的符号数量: {len(symbols)}")
print(f"构建的代码块数量: {len(chunks)}")
print(f"依赖关系: {dependencies}")
```


## 6. 依赖关系
- **依赖的外部库**：  
  - `tree-sitter`：用于解析源代码为AST（通过`tree_sitter_parser.py`）。  
  - `hashlib`：用于生成MD5哈希（通过`md5_cache.py`）。  

- **依赖的内部模块**：  
  - `codemind.parser.models`：使用`Chunk`、`Document`、`Symbol`等数据模型（通过`chunk_builder.py`、`symbol_extractor.py`等）。  

- **被依赖的模块**：  
  - 上层模块（如`codemind.generator`、`codemind.doc_generator`）：使用本模块提供的结构化代码数据（如`Chunk`、`Symbol`）进行代码生成或文档生成。
