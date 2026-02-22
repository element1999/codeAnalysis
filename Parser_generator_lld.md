# CodeMind 核心模块详细设计文档

&gt; **模块**: Parser（代码解析器）+ Generator（文档生成器）  
&gt; **版本**: v1.0.0  
&gt; **日期**: 2026-02-22

---

## 第一部分：Parser（代码解析器）详细设计

### 1. 架构概览
┌─────────────────────────────────────────────────────────────────┐
│                      Parser 架构图                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ FileScanner  │───→│ TreeSitter   │───→│ SymbolExtractor│     │
│  │ 文件扫描器    │    │ AST 解析器    │    │ 符号提取器     │     │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ↓                   ↓                   ↓               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ MD5Cache     │    │ ASTWalker    │    │ Dependency   │      │
│  │ 增量缓存     │◄───│ AST 遍历器    │───→│ Analyzer     │      │
│  │              │    │              │    │ 依赖分析器     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         └───────────────────┴───────────────────┘               │
│                             │                                   │
│                             ↓                                   │
│                    ┌──────────────┐                            │
│                    │ ChunkBuilder │                            │
│                    │ 分片构建器    │                            │
│                    └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘


### 2. 核心类设计

#### 2.1 数据模型（Pydantic）

```python
# models/symbol.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class SymbolType(str, Enum):
    MODULE = "module"           # 文件/模块级别
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"

class Symbol(BaseModel):
    """代码符号基类"""
    id: str = Field(..., description="全局唯一标识符")
    name: str
    type: SymbolType
    file_path: str              # 相对项目根目录的路径
    absolute_path: str          # 绝对路径
    line_start: int
    line_end: int
    column_start: int = 0
    column_end: int = 0
    
    # 代码内容
    source_code: str            # 原始代码文本
    docstring: Optional[str] = None
    
    # 语义关系
    parent_id: Optional[str] = None           # 父符号（如类包含方法）
    children_ids: List[str] = []              # 子符号列表
    
    # 依赖关系
    dependencies: List[str] = []   # 依赖的其他符号ID
    dependents: List[str] = []     # 被哪些符号依赖
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # 用于分片
    token_count: int = 0
    
    def get_full_name(self) -> str:
        """获取完整限定名（如 module.Class.method）"""
        if self.parent_id:
            parent = symbol_registry.get(self.parent_id)  # 伪代码
            return f"{parent.get_full_name()}.{self.name}"
        return self.name

class FunctionSymbol(Symbol):
    """函数专用模型"""
    type: SymbolType = SymbolType.FUNCTION
    parameters: List[Dict[str, str]] = []      # [{"name": "a", "type": "int", "default": "None"}]
    return_type: Optional[str] = None
    is_async: bool = False
    is_generator: bool = False
    decorators: List[str] = []
    calls: List[str] = []                      # 调用的函数名列表

class ClassSymbol(Symbol):
    """类专用模型"""
    type: SymbolType = SymbolType.CLASS
    bases: List[str] = []                      # 继承的父类
    methods: List[str] = []                    # 方法ID列表
    attributes: List[str] = []                 # 属性ID列表
    is_dataclass: bool = False
    is_abstract: bool = False

class ImportSymbol(Symbol):
    """导入语句模型"""
    type: SymbolType = SymbolType.IMPORT
    module_path: str                           # 导入的模块路径
    imported_names: List[str] = []             # 具体导入的名称
    is_from_import: bool = False
    is_relative: bool = False                  # 相对导入（from . import x）

class CodeChunk(BaseModel):
    """代码分片，用于向量化"""
    id: str
    symbol_id: str                             # 关联的符号ID
    content: str                               # 分片内容（代码或文档）
    chunk_type: str                            # "source", "docstring", "summary"
    start_line: int
    end_line: int
    token_count: int
    embedding: Optional[List[float]] = None    # 由 ChromaDB 管理
    
    # 上下文信息（用于 RAG 时组装提示词）
    context: Dict[str, Any] = Field(default_factory=dict)

2.2 FileScanner（文件扫描器）
``` python
# parser/file_scanner.py
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass

@dataclass
class FileInfo:
    relative_path: str
    absolute_path: str
    size: int
    mtime: float
    md5: str
    language: str

class FileScanner:
    """负责发现项目文件并管理增量更新"""
    
    DEFAULT_EXCLUDE = {
        '.git', '__pycache__', '.codemind', 'node_modules',
        '.venv', 'venv', '.env', 'dist', 'build', '.pytest_cache'
    }
    
    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
    }
    
    def __init__(self, project_path: str, config: dict):
        self.project_path = Path(project_path).resolve()
        self.config = config
        self.exclude_dirs = set(config.get('exclude_dirs', [])) | self.DEFAULT_EXCLUDE
        self.include_patterns = config.get('include_patterns', ['*.py'])
        
    def scan(self) -> List[FileInfo]:
        """扫描项目，返回所有相关文件信息"""
        files = []
        
        for pattern in self.include_patterns:
            for file_path in self.project_path.rglob(pattern):
                if self._should_skip(file_path):
                    continue
                    
                stat = file_path.stat()
                content = file_path.read_bytes()
                
                files.append(FileInfo(
                    relative_path=str(file_path.relative_to(self.project_path)),
                    absolute_path=str(file_path),
                    size=stat.st_size,
                    mtime=stat.st_mtime,
                    md5=hashlib.md5(content).hexdigest(),
                    language=self._detect_language(file_path)
                ))
        
        return sorted(files, key=lambda f: f.relative_path)
    
    def _should_skip(self, path: Path) -> bool:
        """判断是否应该跳过该路径"""
        # 检查是否在排除目录中
        for part in path.parts:
            if part in self.exclude_dirs:
                return True
        
        # 检查隐藏文件
        if any(p.startswith('.') for p in path.parts):
            return True
            
        # 检查文件大小限制（默认 1MB）
        max_size = self.config.get('max_file_size', 1024 * 1024)
        if path.stat().st_size > max_size:
            return True
            
        return False
    
    def _detect_language(self, path: Path) -> str:
        """根据扩展名检测语言"""
        return self.LANGUAGE_MAP.get(path.suffix.lower(), 'unknown')
    
    def compute_changes(self, current_files: List[FileInfo], 
                       indexed_files: Dict[str, dict]) -> Tuple[List, List, List]:
        """
        计算文件变更
        返回: (新增文件, 修改文件, 删除文件)
        """
        current_map = {f.relative_path: f for f in current_files}
        indexed_map = {k: v for k, v in indexed_files.items()}
        
        added = []
        modified = []
        deleted = []
        
        # 新增和修改
        for rel_path, file_info in current_map.items():
            if rel_path not in indexed_map:
                added.append(file_info)
            elif indexed_map[rel_path]['md5'] != file_info.md5:
                modified.append(file_info)
        
        # 删除
        for rel_path in indexed_map:
            if rel_path not in current_map:
                deleted.append(rel_path)
        
        return added, modified, deleted

```

2.3 TreeSitterParser（AST 解析器）
``` python
# parser/tree_sitter_parser.py
import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Tree, Node
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class TreeSitterParser:
    """基于 Tree-sitter 的代码解析器"""
    
    def __init__(self):
        self.language = Language(tspython.language())
        self.parser = Parser(self.language)
        
        # 定义查询模式（Tree-sitter Query）
        self._init_queries()
    
    def _init_queries(self):
        """初始化 Tree-sitter 查询模式"""
        # 函数定义查询
        self.function_query = self.language.query("""
            (function_definition
                name: (identifier) @func_name
                parameters: (parameters) @params
                body: (block) @body
            ) @func_def
            
            (decorated_definition
                (decorator)* @decorators
                definition: (function_definition
                    name: (identifier) @func_name
                    parameters: (parameters) @params
                    return_type: (type)? @return_type
                    body: (block) @body
                ) @func_def
            )
        """)
        
        # 类定义查询
        self.class_query = self.language.query("""
            (class_definition
                name: (identifier) @class_name
                superclasses: (argument_list)? @bases
                body: (block) @body
            ) @class_def
        """)
        
        # 导入查询
        self.import_query = self.language.query("""
            (import_statement
                name: (dotted_name) @module_name
            ) @import
            
            (import_from_statement
                module_name: (dotted_name)? @module
                relative_import: (relative_import)? @relative
                name: (dotted_name) @name
            ) @from_import
        """)
        
        # 函数调用查询（用于依赖分析）
        self.call_query = self.language.query("""
            (call
                function: [
                    (identifier) @func_name
                    (attribute
                        object: (identifier) @obj
                        attribute: (identifier) @method
                    )
                ]
            ) @call
        """)
    
    def parse(self, source_code: bytes, file_path: str) -> Optional[Tree]:
        """解析源代码返回 AST"""
        try:
            tree = self.parser.parse(source_code)
            return tree
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return None
    
    def extract_symbols(self, tree: Tree, source_code: bytes, 
                       file_path: str) -> List[Symbol]:
        """从 AST 提取所有符号"""
        symbols = []
        root_node = tree.root_node
        
        # 提取模块级符号（文件本身）
        module_symbol = self._create_module_symbol(file_path, source_code)
        symbols.append(module_symbol)
        
        # 提取类定义
        class_captures = self.class_query.captures(root_node)
        for match in self._group_captures(class_captures):
            class_sym = self._parse_class(match, source_code, file_path, module_symbol.id)
            symbols.append(class_sym)
        
        # 提取函数定义（包括类外函数）
        func_captures = self.function_query.captures(root_node)
        for match in self._group_captures(func_captures):
            func_sym = self._parse_function(match, source_code, file_path, module_symbol.id)
            symbols.append(func_sym)
        
        # 提取导入语句
        import_captures = self.import_query.captures(root_node)
        for match in self._group_captures(import_captures):
            import_sym = self._parse_import(match, source_code, file_path)
            symbols.append(import_sym)
        
        # 建立父子关系
        self._build_relationships(symbols)
        
        return symbols
    
    def _create_module_symbol(self, file_path: str, source_code: bytes) -> Symbol:
        """创建模块级符号"""
        lines = source_code.decode('utf-8', errors='ignore').split('\n')
        return Symbol(
            id=f"mod_{hash(file_path)}",
            name=Path(file_path).stem,
            type=SymbolType.MODULE,
            file_path=file_path,
            absolute_path=str(Path(file_path).resolve()),
            line_start=1,
            line_end=len(lines),
            source_code=source_code.decode('utf-8', errors='ignore'),
            docstring=self._extract_module_docstring(lines)
        )
    
    def _parse_class(self, match: Dict, source_code: bytes, 
                    file_path: str, parent_id: str) -> ClassSymbol:
        """解析类定义"""
        node = match.get('class_def', [None])[0]
        name_node = match.get('class_name', [None])[0]
        
        if not node or not name_node:
            raise ValueError("Invalid class match")
        
        name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')
        
        # 提取父类
        bases = []
        if 'bases' in match:
            bases_node = match['bases'][0]
            bases = self._extract_bases(bases_node, source_code)
        
        # 提取类体
        body_node = match['body'][0]
        methods, attributes = self._extract_class_members(body_node, source_code)
        
        # 提取 docstring
        docstring = self._extract_docstring(body_node, source_code)
        
        return ClassSymbol(
            id=f"cls_{file_path}_{name}_{node.start_point[0]}",
            name=name,
            type=SymbolType.CLASS,
            file_path=file_path,
            absolute_path=str(Path(file_path).resolve()),
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            column_start=node.start_point[1],
            column_end=node.end_point[1],
            source_code=source_code[node.start_byte:node.end_byte].decode('utf-8'),
            docstring=docstring,
            parent_id=parent_id,
            bases=bases,
            methods=methods,
            attributes=attributes
        )
    
    def _parse_function(self, match: Dict, source_code: bytes,
                       file_path: str, parent_id: str) -> FunctionSymbol:
        """解析函数定义"""
        node = match.get('func_def', [None])[0]
        name_node = match.get('func_name', [None])[0]
        
        name = source_code[name_node.start_byte:name_node.end_byte].decode('utf-8')
        
        # 提取参数
        params = []
        if 'params' in match:
            params = self._extract_parameters(match['params'][0], source_code)
        
        # 提取返回类型
        return_type = None
        if 'return_type' in match:
            ret_node = match['return_type'][0]
            return_type = source_code[ret_node.start_byte:ret_node.end_byte].decode('utf-8')
        
        # 提取装饰器
        decorators = []
        if 'decorators' in match:
            for dec_node in match['decorators']:
                dec_text = source_code[dec_node.start_byte:dec_node.end_byte].decode('utf-8')
                decorators.append(dec_text)
        
        # 提取函数体中的调用
        body_node = match['body'][0]
        calls = self._extract_calls(body_node, source_code)
        
        # 检查是否是异步函数
        is_async = b'async' in source_code[node.start_byte:node.start_byte+10]
        
        return FunctionSymbol(
            id=f"func_{file_path}_{name}_{node.start_point[0]}",
            name=name,
            type=SymbolType.FUNCTION,
            file_path=file_path,
            absolute_path=str(Path(file_path).resolve()),
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            column_start=node.start_point[1],
            column_end=node.end_point[1],
            source_code=source_code[node.start_byte:node.end_byte].decode('utf-8'),
            docstring=self._extract_docstring(body_node, source_code),
            parent_id=parent_id,
            parameters=params,
            return_type=return_type,
            is_async=is_async,
            decorators=decorators,
            calls=calls
        )
    
    def _extract_calls(self, node: Node, source_code: bytes) -> List[str]:
        """提取函数调用（用于依赖分析）"""
        calls = []
        call_captures = self.call_query.captures(node)
        
        for match in self._group_captures(call_captures):
            if 'func_name' in match:
                name = source_code[match['func_name'][0].start_byte:match['func_name'][0].end_byte]
                calls.append(name.decode('utf-8'))
            elif 'method' in match:
                obj = source_code[match['obj'][0].start_byte:match['obj'][0].end_byte].decode('utf-8')
                method = source_code[match['method'][0].start_byte:match['method'][0].end_byte].decode('utf-8')
                calls.append(f"{obj}.{method}")
        
        return calls
    
    def _group_captures(self, captures) -> List[Dict[str, List[Node]]]:
        """将 Tree-sitter captures 按匹配分组"""
        # Tree-sitter 返回的是 (node, capture_name) 列表，需要按匹配分组
        # 简化实现：这里假设每个 capture 是独立的
        groups = []
        current_group = {}
        
        for node, capture_name in captures:
            if capture_name in current_group:
                # 新的匹配开始
                groups.append(current_group)
                current_group = {}
            current_group.setdefault(capture_name, []).append(node)
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _extract_docstring(self, node: Node, source_code: bytes) -> Optional[str]:
        """提取文档字符串"""
        # 查找函数/类体的第一个表达式语句
        for child in node.children:
            if child.type == 'expression_statement':
                expr = child.children[0]
                if expr.type == 'string':
                    return source_code[expr.start_byte:expr.end_byte].decode('utf-8').strip('"\'')
        return None
```

2.4 DependencyAnalyzer（依赖分析器）
``` python
# parser/dependency_analyzer.py
from typing import List, Dict, Set, Tuple
from collections import defaultdict

class DependencyAnalyzer:
    """分析符号间的依赖关系"""
    
    def __init__(self, symbols: List[Symbol]):
        self.symbols = {s.id: s for s in symbols}
        self.symbol_index = self._build_index()
    
    def _build_index(self) -> Dict[str, List[str]]:
        """构建名称到符号ID的索引"""
        index = defaultdict(list)
        for sym_id, sym in self.symbols.items():
            index[sym.name].append(sym_id)
            # 也索引完整限定名
            if hasattr(sym, 'get_full_name'):
                index[sym.get_full_name()].append(sym_id)
        return index
    
    def analyze(self) -> Dict[str, List[str]]:
        """
        分析所有依赖关系
        返回: {symbol_id: [dependency_symbol_ids]}
        """
        dependencies = defaultdict(list)
        
        for sym_id, sym in self.symbols.items():
            # 分析导入依赖
            if sym.type == SymbolType.IMPORT:
                resolved = self._resolve_import(sym)
                dependencies[sym_id] = resolved
            
            # 分析函数调用依赖
            elif isinstance(sym, FunctionSymbol):
                for call in sym.calls:
                    resolved = self._resolve_call(call, sym.file_path)
                    dependencies[sym_id].extend(resolved)
            
            # 分析类继承依赖
            elif isinstance(sym, ClassSymbol):
                for base in sym.bases:
                    resolved = self._resolve_class(base, sym.file_path)
                    dependencies[sym_id].extend(resolved)
        
        return dict(dependencies)
    
    def _resolve_import(self, import_sym: ImportSymbol) -> List[str]:
        """解析导入语句指向的符号"""
        # 简化实现：匹配模块名
        results = []
        target_module = import_sym.module_path
        
        for sym_id, sym in self.symbols.items():
            if sym.type == SymbolType.MODULE:
                # 检查文件路径是否匹配模块路径
                module_path = sym.file_path.replace('/', '.').replace('.py', '')
                if module_path.endswith(target_module) or target_module.endswith(module_path):
                    results.append(sym_id)
        
        return results
    
    def _resolve_call(self, call_name: str, current_file: str) -> List[str]:
        """解析函数调用指向的符号"""
        # 处理简单名称和属性访问（如 obj.method）
        if '.' in call_name:
            # 可能是方法调用，尝试匹配类方法
            class_name, method_name = call_name.rsplit('.', 1)
            # 在当前文件查找类定义
            for sym_id, sym in self.symbols.items():
                if sym.file_path == current_file and sym.name == class_name:
                    if isinstance(sym, ClassSymbol) and method_name in sym.methods:
                        return [f"{sym_id}.{method_name}"]
        
        # 简单名称匹配
        return self.symbol_index.get(call_name, [])
    
    def build_dependency_graph(self) -> Dict:
        """构建完整的依赖图"""
        deps = self.analyze()
        
        nodes = []
        edges = []
        
        for sym_id, sym in self.symbols.items():
            nodes.append({
                "id": sym_id,
                "name": sym.name,
                "type": sym.type.value,
                "file": sym.file_path
            })
            
            for dep_id in deps.get(sym_id, []):
                edges.append({
                    "from": sym_id,
                    "to": dep_id,
                    "type": self._determine_edge_type(sym, self.symbols.get(dep_id))
                })
        
        return {"nodes": nodes, "edges": edges}
    
    def _determine_edge_type(self, from_sym: Symbol, to_sym: Optional[Symbol]) -> str:
        """确定边的类型"""
        if from_sym.type == SymbolType.IMPORT:
            return "imports"
        elif isinstance(from_sym, ClassSymbol) and to_sym and to_sym.type == SymbolType.CLASS:
            return "inherits"
        elif isinstance(from_sym, FunctionSymbol):
            return "calls"
        return "references"
```

2.5 ChunkBuilder（分片构建器）

``` python
# parser/chunk_builder.py
import tiktoken
from typing import List
from models.symbol import Symbol, CodeChunk, SymbolType

class ChunkBuilder:
    """将符号转换为可向量化的代码分片"""
    
    def __init__(self, max_tokens: int = 512, overlap_tokens: int = 50):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.encoder = tiktoken.get_encoding("cl100k_base")
    
    def build_chunks(self, symbols: List[Symbol]) -> List[CodeChunk]:
        """为所有符号构建分片"""
        chunks = []
        
        for sym in symbols:
            sym_chunks = self._chunk_symbol(sym)
            chunks.extend(sym_chunks)
        
        return chunks
    
    def _chunk_symbol(self, sym: Symbol) -> List[CodeChunk]:
        """为单个符号构建分片"""
        chunks = []
        
        # 策略 1: 为每个符号创建元数据分片（用于检索）
        meta_chunk = self._create_meta_chunk(sym)
        chunks.append(meta_chunk)
        
        # 策略 2: 如果符号有文档字符串，单独分片
        if sym.docstring:
            doc_chunk = CodeChunk(
                id=f"{sym.id}_doc",
                symbol_id=sym.id,
                content=f"{sym.name}: {sym.docstring}",
                chunk_type="docstring",
                start_line=sym.line_start,
                end_line=sym.line_start + 1,
                token_count=self._count_tokens(sym.docstring),
                context={
                    "symbol_name": sym.name,
                    "symbol_type": sym.type.value,
                    "file_path": sym.file_path
                }
            )
            chunks.append(doc_chunk)
        
        # 策略 3: 源代码分片（如果代码较长则拆分）
        source_chunks = self._chunk_source_code(sym)
        chunks.extend(source_chunks)
        
        return chunks
    
    def _create_meta_chunk(self, sym: Symbol) -> CodeChunk:
        """创建符号元数据分片（用于快速检索）"""
        # 构建结构化的元数据描述
        content_parts = [
            f"Symbol: {sym.name}",
            f"Type: {sym.type.value}",
            f"File: {sym.file_path}",
            f"Lines: {sym.line_start}-{sym.line_end}",
        ]
        
        if sym.docstring:
            content_parts.append(f"Documentation: {sym.docstring[:200]}...")
        
        # 添加特定类型的元数据
        if isinstance(sym, FunctionSymbol):
            params_str = ", ".join([p.get('name', 'unknown') for p in sym.parameters])
            content_parts.append(f"Parameters: ({params_str})")
            if sym.return_type:
                content_parts.append(f"Returns: {sym.return_type}")
        
        elif isinstance(sym, ClassSymbol):
            if sym.bases:
                content_parts.append(f"Inherits: {', '.join(sym.bases)}")
            content_parts.append(f"Methods: {len(sym.methods)}")
        
        content = "\n".join(content_parts)
        
        return CodeChunk(
            id=f"{sym.id}_meta",
            symbol_id=sym.id,
            content=content,
            chunk_type="summary",
            start_line=sym.line_start,
            end_line=sym.line_end,
            token_count=self._count_tokens(content),
            context={
                "symbol_id": sym.id,
                "full_name": sym.get_full_name() if hasattr(sym, 'get_full_name') else sym.name
            }
        )
    
    def _chunk_source_code(self, sym: Symbol) -> List[CodeChunk]:
        """对源代码进行智能分片"""
        source = sym.source_code
        tokens = self.encoder.encode(source)
        
        if len(tokens) <= self.max_tokens:
            # 代码较短，不需要拆分
            return [CodeChunk(
                id=f"{sym.id}_source",
                symbol_id=sym.id,
                content=source,
                chunk_type="source",
                start_line=sym.line_start,
                end_line=sym.line_end,
                token_count=len(tokens),
                context={"is_complete": True}
            )]
        
        # 代码较长，需要拆分
        chunks = []
        lines = source.split('\n')
        current_lines = []
        current_tokens = 0
        chunk_start_line = sym.line_start
        
        for i, line in enumerate(lines):
            line_tokens = len(self.encoder.encode(line))
            
            if current_tokens + line_tokens > self.max_tokens and current_lines:
                # 保存当前分片
                chunk_content = '\n'.join(current_lines)
                chunks.append(CodeChunk(
                    id=f"{sym.id}_source_{len(chunks)}",
                    symbol_id=sym.id,
                    content=chunk_content,
                    chunk_type="source",
                    start_line=chunk_start_line,
                    end_line=chunk_start_line + len(current_lines) - 1,
                    token_count=current_tokens,
                    context={"is_complete": False, "chunk_index": len(chunks)}
                ))
                
                # 重叠处理：保留最后几行用于上下文连贯
                overlap_lines = current_lines[-3:] if len(current_lines) > 3 else current_lines
                current_lines = overlap_lines + [line]
                current_tokens = sum(len(self.encoder.encode(l)) for l in current_lines)
                chunk_start_line = sym.line_start + i - len(overlap_lines) + 1
            else:
                current_lines.append(line)
                current_tokens += line_tokens
        
        # 处理剩余行
        if current_lines:
            chunk_content = '\n'.join(current_lines)
            chunks.append(CodeChunk(
                id=f"{sym.id}_source_{len(chunks)}",
                symbol_id=sym.id,
                content=chunk_content,
                chunk_type="source",
                start_line=chunk_start_line,
                end_line=sym.line_end,
                token_count=current_tokens,
                context={"is_complete": True, "chunk_index": len(chunks)}
            ))
        
        return chunks
    
    def _count_tokens(self, text: str) -> int:
        """计算文本的 token 数量"""
        return len(self.encoder.encode(text))
```

2.6 Parser 主控类
``` python
# parser/__init__.py
from typing import List, Dict, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

class CodeParser:
    """代码解析主控类，协调各组件完成解析任务"""
    
    def __init__(self, project_path: str, storage_path: str):
        self.project_path = Path(project_path)
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        self.config = self._load_config()
        self.file_scanner = FileScanner(project_path, self.config.get('parser', {}))
        self.tree_parser = TreeSitterParser()
        self.chunk_builder = ChunkBuilder()
        
        # 状态
        self.indexed_files = self._load_indexed_files()
        self.symbols: List[Symbol] = []
        self.chunks: List[CodeChunk] = []
    
    def parse(self, incremental: bool = True) -> Dict:
        """
        执行解析流程
        
        Args:
            incremental: 是否启用增量更新
        
        Returns:
            解析统计信息
        """
        logger.info(f"Starting parsing: {self.project_path}")
        
        # 1. 扫描文件
        current_files = self.file_scanner.scan()
        logger.info(f"Found {len(current_files)} files")
        
        # 2. 计算变更
        if incremental:
            added, modified, deleted = self.file_scanner.compute_changes(
                current_files, self.indexed_files
            )
            logger.info(f"Changes: {len(added)} added, {len(modified)} modified, {len(deleted)} deleted")
        else:
            added = current_files
            modified = []
            deleted = list(self.indexed_files.keys())
            logger.info("Full rebuild mode")
        
        # 3. 处理删除的文件
        for rel_path in deleted:
            self._remove_file_symbols(rel_path)
        
        # 4. 处理新增和修改的文件
        files_to_process = added + modified
        
        for file_info in files_to_process:
            try:
                self._process_file(file_info)
            except Exception as e:
                logger.error(f"Failed to process {file_info.relative_path}: {e}")
                continue
        
        # 5. 依赖分析
        logger.info("Analyzing dependencies...")
        analyzer = DependencyAnalyzer(self.symbols)
        self.dependency_graph = analyzer.build_dependency_graph()
        
        # 6. 构建分片
        logger.info("Building chunks...")
        self.chunks = self.chunk_builder.build_chunks(self.symbols)
        
        # 7. 持久化
        self._save_results()
        
        return {
            "files_processed": len(files_to_process),
            "symbols_found": len(self.symbols),
            "chunks_created": len(self.chunks),
            "dependencies_mapped": len(self.dependency_graph.get('edges', []))
        }
    
    def _process_file(self, file_info: FileInfo):
        """处理单个文件"""
        # 读取文件
        source_bytes = Path(file_info.absolute_path).read_bytes()
        
        # 解析 AST
        tree = self.tree_parser.parse(source_bytes, file_info.relative_path)
        if not tree:
            return
        
        # 提取符号
        file_symbols = self.tree_parser.extract_symbols(
            tree, source_bytes, file_info.relative_path
        )
        
        # 移除该文件旧的符号（如果是修改）
        self._remove_file_symbols(file_info.relative_path)
        
        # 添加新符号
        self.symbols.extend(file_symbols)
        
        # 更新索引记录
        self.indexed_files[file_info.relative_path] = {
            "md5": file_info.md5,
            "mtime": file_info.mtime,
            "size": file_info.size
        }
        
        logger.debug(f"Processed {file_info.relative_path}: {len(file_symbols)} symbols")
    
    def _remove_file_symbols(self, relative_path: str):
        """移除指定文件的所有符号"""
        self.symbols = [s for s in self.symbols if s.file_path != relative_path]
        if relative_path in self.indexed_files:
            del self.indexed_files[relative_path]
    
    def _save_results(self):
        """保存解析结果到存储"""
        # 保存符号表
        symbols_data = [s.model_dump() for s in self.symbols]
        (self.storage_path / "symbols.json").write_text(
            json.dumps(symbols_data, indent=2, default=str)
        )
        
        # 保存依赖图
        (self.storage_path / "dependencies.json").write_text(
            json.dumps(self.dependency_graph, indent=2)
        )
        
        # 保存文件索引
        (self.storage_path / "files.json").write_text(
            json.dumps(self.indexed_files, indent=2)
        )
        
        # 保存分片（单独目录）
        chunks_dir = self.storage_path / "chunks"
        chunks_dir.mkdir(exist_ok=True)
        
        # 清理旧分片
        for f in chunks_dir.glob("*.json"):
            f.unlink()
        
        # 写入新分片
        for chunk in self.chunks:
            chunk_file = chunks_dir / f"{chunk.id}.json"
            chunk_file.write_text(json.dumps(chunk.model_dump(), indent=2, default=str))
        
        logger.info(f"Saved results to {self.storage_path}")
    
    def _load_indexed_files(self) -> Dict:
        """加载已索引的文件记录"""
        files_json = self.storage_path / "files.json"
        if files_json.exists():
            return json.loads(files_json.read_text())
        return {}
    
    def _load_config(self) -> dict:
        """加载解析配置"""
        config_json = self.project_path / ".codemind" / "config.json"
        if config_json.exists():
            return json.loads(config_json.read_text())
        return {}
    
    def get_symbol_by_id(self, symbol_id: str) -> Optional[Symbol]:
        """根据 ID 获取符号"""
        for sym in self.symbols:
            if sym.id == symbol_id:
                return sym
        return None
    
    def get_symbols_by_file(self, file_path: str) -> List[Symbol]:
        """获取指定文件的所有符号"""
        return [s for s in self.symbols if s.file_path == file_path]

### 3. Embedding 集成设计

#### 3.1 EmbeddingManager 类

```python
# parser/embedding_manager.py
from typing import List, Dict, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class EmbeddingProvider(str, Enum):
    """Embedding 提供商枚举"""
    FASTEMBED = "fastembed"
    OPENAI = "openai"

class EmbeddingManager:
    """Embedding 管理器，支持 FastEmbed 和 OpenAI"""
    
    FASTEMBED_MODELS = {
        "BAAI/bge-small-en-v1.5": 384,
        "BAAI/bge-base-en-v1.5": 768,
        "BAAI/bge-small-zh-v1.5": 512,
        "BAAI/bge-base-zh-v1.5": 768,
        "sentence-transformers/all-MiniLM-L6-v2": 384
    }
    
    def __init__(self, config: Dict):
        self.config = config
        self.provider = EmbeddingProvider(config.get('provider', 'fastembed'))
        self.model_name = config.get('model', 'BAAI/bge-small-en-v1.5')
        self.dimension = config.get('dimension', 384)
        
        # 初始化 embedding 模型
        self.model = self._init_model()
    
    def _init_model(self):
        """初始化 embedding 模型"""
        if self.provider == EmbeddingProvider.FASTEMBED:
            try:
                from fastembed import TextEmbedding
                self.embedding_model = TextEmbedding(self.model_name)
                logger.info(f"Initialized FastEmbed model: {self.model_name}")
                return self.embedding_model
            except ImportError:
                raise ImportError("FastEmbed not installed. Install with: pip install fastembed")
        
        elif self.provider == EmbeddingProvider.OPENAI:
            import openai
            self.client = openai.OpenAI(
                api_key=self.config.get('api_key'),
                base_url=self.config.get('base_url')
            )
            logger.info(f"Initialized OpenAI embedding model: {self.model_name}")
            return self.client
        
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")
    
    def embed(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        生成文本的向量表示
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小
        
        Returns:
            向量列表
        """
        if self.provider == EmbeddingProvider.FASTEMBED:
            embeddings = []
            for embedding in self.model.embed(texts, batch_size=batch_size):
                embeddings.append(embedding.tolist())
            return embeddings
        
        elif self.provider == EmbeddingProvider.OPENAI:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            return [item.embedding for item in response.data]
    
    def embed_single(self, text: str) -> List[float]:
        """
        生成单个文本的向量表示
        
        Args:
            text: 文本
        
        Returns:
            向量
        """
        embeddings = self.embed([text])
        return embeddings[0]
    
    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.dimension
```

#### 3.2 ChunkEmbedder 类

```python
# parser/chunk_embedder.py
from typing import List, Dict
import chromadb
from chromadb.config import Settings
import logging

logger = logging.getLogger(__name__)

class ChunkEmbedder:
    """代码分片向量化器"""
    
    def __init__(self, embedding_manager: EmbeddingManager, project_path: str):
        self.embedding_manager = embedding_manager
        self.project_path = project_path
        
        # 初始化 ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(project_path / ".codemind" / "vectors"),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 获取或创建集合
        self.collection = self.chroma_client.get_or_create_collection(
            name="code_chunks",
            metadata={"hnsw:space": "cosine"}
        )
    
    def embed_chunks(self, chunks: List[CodeChunk]) -> int:
        """
        批量向量化代码分片
        
        Args:
            chunks: 代码分片列表
        
        Returns:
            成功嵌入的分片数量
        """
        if not chunks:
            return 0
        
        # 准备文本内容
        texts = [chunk.content for chunk in chunks]
        
        # 生成向量
        embeddings = self.embedding_manager.embed(texts)
        
        # 准备元数据
        ids = [chunk.id for chunk in chunks]
        metadatas = [
            {
                "symbol_id": chunk.symbol_id,
                "chunk_type": chunk.chunk_type,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "file_path": chunk.context.get("file_path", "")
            }
            for chunk in chunks
        ]
        
        # 存储到 ChromaDB
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            logger.info(f"Embedded {len(chunks)} chunks")
            return len(chunks)
        except Exception as e:
            logger.error(f"Failed to embed chunks: {e}")
            return 0
    
    def search(self, query: str, n_results: int = 5, 
              filters: Optional[Dict] = None) -> List[Dict]:
        """
        语义搜索代码分片
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            filters: 元数据过滤条件
        
        Returns:
            搜索结果列表
        """
        # 生成查询向量
        query_embedding = self.embedding_manager.embed_single(query)
        
        # 执行搜索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filters
        )
        
        # 格式化结果
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i]
            })
        
        return formatted_results
    
    def delete_chunks(self, chunk_ids: List[str]):
        """
        删除指定的代码分片
        
        Args:
            chunk_ids: 分片ID列表
        """
        try:
            self.collection.delete(ids=chunk_ids)
            logger.info(f"Deleted {len(chunk_ids)} chunks")
        except Exception as e:
            logger.error(f"Failed to delete chunks: {e}")
    
    def clear_collection(self):
        """清空集合"""
        try:
            self.chroma_client.delete_collection("code_chunks")
            self.collection = self.chroma_client.create_collection(
                name="code_chunks",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Cleared code_chunks collection")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
```
```