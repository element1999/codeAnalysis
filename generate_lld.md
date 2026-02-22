第二部分：Generator（文档生成器）详细设计

1. 架构概览
┌─────────────────────────────────────────────────────────────────┐
│                    Generator 架构图                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Context     │───→│  LLM         │───→│  Document    │      │
│  │  Assembler   │    │  Agent       │    │  Writer      │      │
│  │  上下文组装器 │    │  智能体      │    │  文档写入器  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ↓                   ↓                   ↓               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Symbol      │    │  Prompt      │    │  Mermaid     │      │
│  │  Selector    │    │  Templates   │    │  Generator   │      │
│  │  符号选择器  │    │  提示词模板  │    │  图表生成器  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
                    ┌──────────────┐
                    │  Wiki        │
                    │  Structure   │
                    │  (Markdown)  │
                    └──────────────┘


2. 核心类设计
2.1 文档模型

``` python
# models/document.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DocType(str, Enum):
    OVERVIEW = "overview"           # 项目概览
    ARCHITECTURE = "architecture"   # 架构分析
    MODULE = "module"               # 模块文档
    API = "api"                     # API 文档
    GUIDE = "guide"                 # 使用指南

class DocumentSection(BaseModel):
    """文档章节"""
    title: str
    level: int                      # 标题级别（1-6）
    content: str                    # Markdown 内容
    order: int                      # 排序
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Document(BaseModel):
    """文档对象"""
    id: str
    doc_type: DocType
    title: str
    file_path: str                  # 相对 wiki/ 目录的路径
    sections: List[DocumentSection] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    source_symbols: List[str] = []  # 基于哪些符号生成
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_markdown(self) -> str:
        """转换为 Markdown 文本"""
        lines = [f"# {self.title}\n"]
        
        for section in sorted(self.sections, key=lambda s: s.order):
            prefix = "#" * section.level
            lines.append(f"{prefix} {section.title}\n")
            lines.append(section.content)
            lines.append("")  # 空行
        
        return "\n".join(lines)

class WikiStructure(BaseModel):
    """Wiki 结构定义"""
    project_name: str
    documents: List[Document] = []
    nav_order: List[str] = []       # 导航顺序
    
    def get_nav_tree(self) -> Dict:
        """生成导航树"""
        tree = {}
        for doc in self.documents:
            parts = doc.file_path.split('/')
            current = tree
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {"_docs": []}
                current = current[part]
            current.setdefault("_docs", []).append({
                "title": doc.title,
                "path": doc.file_path,
                "type": doc.doc_type.value
            })
        return tree
```

2.2 ContextAssembler（上下文组装器）
``` python
# generator/context_assembler.py
from typing import List, Dict, Any
from models.symbol import Symbol, SymbolType
import json

class ContextAssembler:
    """
    为 LLM 组装上下文信息
    策略：根据文档类型选择相关符号，构建结构化上下文
    """
    
    def __init__(self, symbols: List[Symbol], dependencies: Dict):
        self.symbols = symbols
        self.dependencies = dependencies
        self.symbol_map = {s.id: s for s in symbols}
    
    def assemble_for_overview(self) -> Dict[str, Any]:
        """组装项目概览所需的上下文"""
        # 收集顶层模块
        modules = [s for s in self.symbols if s.type == SymbolType.MODULE]
        
        # 收集入口点（包含 main 函数或 app 创建的文件）
        entry_points = []
        for sym in self.symbols:
            if sym.type == SymbolType.FUNCTION and sym.name in ['main', 'create_app', 'run']:
                entry_points.append(sym)
            if 'config' in sym.name.lower() and sym.type == SymbolType.MODULE:
                entry_points.append(sym)
        
        # 收集配置信息（requirements.txt, package.json 等）
        config_files = self._find_config_files()
        
        # 统计信息
        stats = self._calculate_stats()
        
        return {
            "project_structure": self._build_tree_structure(),
            "modules": [self._summarize_symbol(m) for m in modules[:20]],  # 限制数量
            "entry_points": [self._summarize_symbol(ep) for ep in entry_points],
            "config_files": config_files,
            "statistics": stats,
            "dependencies": self._extract_key_dependencies()
        }
    
    def assemble_for_module(self, module_symbol: Symbol) -> Dict[str, Any]:
        """组装特定模块的上下文"""
        # 获取模块内的所有符号
        module_symbols = [
            s for s in self.symbols 
            if s.file_path == module_symbol.file_path and s.id != module_symbol.id
        ]
        
        # 分类
        classes = [s for s in module_symbols if s.type == SymbolType.CLASS]
        functions = [s for s in module_symbols if s.type == SymbolType.FUNCTION]
        imports = [s for s in module_symbols if s.type == SymbolType.IMPORT]
        
        # 获取模块的依赖关系
        module_deps = self._get_module_dependencies(module_symbol.file_path)
        
        return {
            "module_info": self._summarize_symbol(module_symbol, detailed=True),
            "classes": [self._summarize_symbol(c, detailed=True) for c in classes],
            "functions": [self._summarize_symbol(f) for f in functions],
            "imports": [self._summarize_symbol(i) for i in imports],
            "dependencies": module_deps,
            "source_code": module_symbol.source_code[:2000]  # 限制长度
        }
    
    def assemble_for_architecture(self) -> Dict[str, Any]:
        """组装架构分析所需的上下文"""
        # 构建依赖图摘要
        graph_summary = self._summarize_dependency_graph()
        
        # 识别关键组件（高度连接的节点）
        key_components = self._identify_key_components()
        
        # 识别分层结构（如 MVC、分层架构）
        layers = self._identify_layers()
        
        return {
            "dependency_graph": graph_summary,
            "key_components": key_components,
            "layers": layers,
            "design_patterns": self._detect_design_patterns()
        }
    
    def _summarize_symbol(self, sym: Symbol, detailed: bool = False) -> Dict:
        """将符号转换为摘要信息"""
        summary = {
            "name": sym.name,
            "type": sym.type.value,
            "file": sym.file_path,
            "line": sym.line_start,
            "docstring": sym.docstring[:200] if sym.docstring else None
        }
        
        if detailed:
            summary.update({
                "source_preview": sym.source_code[:500],
                "dependencies_count": len(sym.dependencies),
                "dependents_count": len(sym.dependents)
            })
            
            if hasattr(sym, 'parameters'):
                summary['signature'] = self._build_signature(sym)
        
        return summary
    
    def _build_signature(self, sym) -> str:
        """构建函数签名"""
        if hasattr(sym, 'parameters'):
            params = ", ".join([
                f"{p.get('name', 'arg')}: {p.get('type', 'Any')}" 
                for p in sym.parameters
            ])
            ret = f" -> {sym.return_type}" if sym.return_type else ""
            return f"def {sym.name}({params}){ret}"
        return sym.name
    
    def _build_tree_structure(self) -> str:
        """构建项目树形结构文本"""
        tree = {}
        for sym in self.symbols:
            if sym.type == SymbolType.MODULE:
                parts = sym.file_path.split('/')
                current = tree
                for part in parts:
                    current = current.setdefault(part, {})
        
        def render(node, prefix=""):
            lines = []
            items = sorted(node.items())
            for i, (name, subtree) in enumerate(items):
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{name}")
                if subtree:
                    extension = "    " if is_last else "│   "
                    lines.extend(render(subtree, prefix + extension))
            return lines
        
        return "\n".join(render(tree))
    
    def _calculate_stats(self) -> Dict:
        """计算项目统计信息"""
        return {
            "total_files": len(set(s.file_path for s in self.symbols if s.type == SymbolType.MODULE)),
            "total_classes": len([s for s in self.symbols if s.type == SymbolType.CLASS]),
            "total_functions": len([s for s in self.symbols if s.type == SymbolType.FUNCTION]),
            "total_lines": sum(s.line_end - s.line_start for s in self.symbols)
        }
    
    def _find_config_files(self) -> List[Dict]:
        """查找配置文件"""
        configs = []
        for sym in self.symbols:
            if sym.type == SymbolType.MODULE:
                fname = sym.file_path.lower()
                if any(x in fname for x in ['requirements', 'package', 'pyproject', 'setup', 'dockerfile', 'makefile']):
                    configs.append({
                        "name": sym.file_path,
                        "preview": sym.source_code[:500]
                    })
        return configs
    
    def _extract_key_dependencies(self) -> List[str]:
        """提取关键外部依赖"""
        imports = set()
        for sym in self.symbols:
            if sym.type == SymbolType.IMPORT and hasattr(sym, 'module_path'):
                module = sym.module_path.split('.')[0]
                if module not in ['sys', 'os', 'typing', 'collections', 'json']:
                    imports.add(module)
        return sorted(list(imports))[:20]
    
    def _get_module_dependencies(self, file_path: str) -> Dict:
        """获取模块级别的依赖关系"""
        module_syms = [s for s in self.symbols if s.file_path == file_path]
        
        incoming = []
        outgoing = []
        
        for sym in module_syms:
            # 出向依赖
            for dep_id in sym.dependencies:
                dep_sym = self.symbol_map.get(dep_id)
                if dep_sym and dep_sym.file_path != file_path:
                    outgoing.append({
                        "symbol": sym.name,
                        "depends_on": dep_sym.name,
                        "in_file": dep_sym.file_path
                    })
            
            # 入向依赖
            for dep_sym in self.symbols:
                if sym.id in dep_sym.dependencies and dep_sym.file_path != file_path:
                    incoming.append({
                        "symbol": dep_sym.name,
                        "in_file": dep_sym.file_path,
                        "depends_on": sym.name
                    })
        
        return {"incoming": incoming[:10], "outgoing": outgoing[:10]}
    
    def _summarize_dependency_graph(self) -> Dict:
        """摘要依赖图"""
        nodes = self.dependencies.get('nodes', [])
        edges = self.dependencies.get('edges', [])
        
        # 统计
        file_deps = {}
        for edge in edges:
            from_node = next((n for n in nodes if n['id'] == edge['from']), None)
            to_node = next((n for n in nodes if n['id'] == edge['to']), None)
            if from_node and to_node:
                from_file = from_node['file']
                to_file = to_node['file']
                if from_file != to_file:
                    file_deps.setdefault(from_file, []).append(to_file)
        
        return {
            "total_symbols": len(nodes),
            "total_relations": len(edges),
            "file_dependencies": {k: list(set(v))[:5] for k, v in list(file_deps.items())[:10]}
        }
    
    def _identify_key_components(self) -> List[Dict]:
        """识别关键组件（高连接度节点）"""
        node_connections = {}
        for edge in self.dependencies.get('edges', []):
            node_connections[edge['from']] = node_connections.get(edge['from'], 0) + 1
            node_connections[edge['to']] = node_connections.get(edge['to'], 0) + 1
        
        sorted_nodes = sorted(
            node_connections.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        result = []
        for node_id, count in sorted_nodes:
            sym = self.symbol_map.get(node_id)
            if sym:
                result.append({
                    "name": sym.name,
                    "type": sym.type.value,
                    "file": sym.file_path,
                    "connections": count
                })
        
        return result
    
    def _identify_layers(self) -> List[Dict]:
        """识别架构分层（启发式）"""
        layers = {
            "api": [],      # 包含 route, view, controller
            "service": [],  # 包含 service, business
            "data": [],     # 包含 model, repository, db
            "util": []      # 其他
        }
        
        for sym in self.symbols:
            path = sym.file_path.lower()
            name = sym.name.lower()
            
            if any(x in path for x in ['route', 'view', 'controller', 'api', 'endpoint']):
                layers['api'].append(sym.file_path)
            elif any(x in path for x in ['service', 'business', 'logic']):
                layers['service'].append(sym.file_path)
            elif any(x in path for x in ['model', 'repository', 'db', 'data', 'entity']):
                layers['data'].append(sym.file_path)
            else:
                layers['util'].append(sym.file_path)
        
        # 去重并限制
        return [
            {"name": k, "files": list(set(v))[:5]} 
            for k, v in layers.items() if v
        ]
    
    def _detect_design_patterns(self) -> List[str]:
        """检测可能的设计模式（启发式）"""
        patterns = []
        
        # 检查单例模式
        singleton_candidates = [
            s for s in self.symbols 
            if s.type == SymbolType.CLASS and 'instance' in s.source_code.lower()
        ]
        if singleton_candidates:
            patterns.append("Singleton (疑似)")
        
        # 检查工厂模式
        factory_candidates = [
            s for s in self.symbols
            if 'factory' in s.name.lower() or 'create' in s.name.lower()
        ]
        if factory_candidates:
            patterns.append("Factory (疑似)")
        
        # 检查依赖注入
        di_candidates = [
            s for s in self.symbols
            if hasattr(s, 'parameters') and any('inject' in str(p).lower() for p in s.parameters)
        ]
        if di_candidates:
            patterns.append("Dependency Injection (疑似)")
        
        return patterns
```
2.3 LLMAgent（LLM 智能体）
``` python
# generator/llm_agent.py
import openai
from typing import List, Dict, Optional, Generator
import json
import logging

logger = logging.getLogger(__name__)

class LLMProvider(str, Enum):
    """LLM 提供商枚举"""
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"
    GLM = "glm"
    KIMI = "kimi"
    OPENAI = "openai"

class LLMAgent:
    """LLM 交互封装，支持多种 LLM 提供商"""
    
    PROVIDER_CONFIGS = {
        LLMProvider.OLLAMA: {
            "default_base_url": "http://localhost:11434/v1",
            "default_model": "llama3.2",
            "requires_api_key": False
        },
        LLMProvider.DEEPSEEK: {
            "default_base_url": "https://api.deepseek.com/v1",
            "default_model": "deepseek-chat",
            "requires_api_key": True
        },
        LLMProvider.GLM: {
            "default_base_url": "https://open.bigmodel.cn/api/paas/v4",
            "default_model": "glm-4",
            "requires_api_key": True
        },
        LLMProvider.KIMI: {
            "default_base_url": "https://api.moonshot.cn/v1",
            "default_model": "moonshot-v1-8k",
            "requires_api_key": True
        },
        LLMProvider.OPENAI: {
            "default_base_url": None,
            "default_model": "gpt-4",
            "requires_api_key": True
        }
    }
    
    def __init__(self, config: Dict):
        self.config = config
        self.provider = LLMProvider(config.get('provider', 'ollama'))
        self.model = config.get('model', self.PROVIDER_CONFIGS[self.provider]['default_model'])
        self.max_tokens = config.get('max_tokens', 4000)
        self.temperature = config.get('temperature', 0.3)
        
        # 初始化客户端
        self.client = self._init_client()
    
    def _init_client(self) -> openai.OpenAI:
        """根据提供商初始化 OpenAI 客户端"""
        provider_config = self.PROVIDER_CONFIGS[self.provider]
        
        # 获取 API Key
        api_key = self.config.get('api_key')
        if provider_config['requires_api_key'] and not api_key:
            raise ValueError(f"{self.provider.value} requires api_key")
        
        # 获取 base_url
        base_url = self.config.get('base_url', provider_config['default_base_url'])
        
        return openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    def generate_document(self, prompt: str, context: Dict) -> str:
        """
        生成文档内容
        
        Args:
            prompt: 提示词模板
            context: 上下文数据（会被格式化为 JSON 插入提示词）
        
        Returns:
            生成的 Markdown 内容
        """
        full_prompt = self._assemble_prompt(prompt, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a technical documentation expert. Generate clear, structured Markdown documentation based on the provided code context."
                    },
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            content = self._clean_markdown(content)
            
            return content
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise
    
    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        """流式生成（用于 chat 命令）"""
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                max_tokens=self.max_tokens
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Stream generation failed: {e}")
            raise
    
    def chat(self, messages: List[Dict], stream: bool = False) -> Union[str, Generator[str, None, None]]:
        """
        通用聊天接口，支持多轮对话
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}, ...]
            stream: 是否流式输出
        
        Returns:
            生成的回复或流式生成器
        """
        try:
            if stream:
                stream_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                
                def generator():
                    for chunk in stream_response:
                        if chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                
                return generator()
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise
    
    def _assemble_prompt(self, template: str, context: Dict) -> str:
        """组装提示词"""
        context_str = json.dumps(context, indent=2, default=str, ensure_ascii=False)
        prompt = template.replace("{{context}}", context_str)
        return prompt
    
    def _clean_markdown(self, content: str) -> str:
        """清理 LLM 输出的 markdown 格式"""
        lines = content.split('\n')
        if lines[0].strip().startswith('```'):
            lines = lines[1:]
        if lines[-1].strip() == '```':
            lines = lines[:-1]
        return '\n'.join(lines).strip()


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


class PromptTemplates:
    """提示词模板库"""
    
    OVERVIEW_TEMPLATE = """
基于以下代码库信息，生成项目概览文档（Markdown 格式）。

## 项目结构
```text
{{context.project_structure}}
```

{context.statistics}}
入口点
{{context.entry_points}}
配置文件
{{context.config_files}}
关键依赖
{{context.dependencies}}
请生成包含以下章节的项目概览文档：
项目简介（1-2段话描述项目目标和定位）
技术栈（列出主要技术、框架、版本）
项目结构说明（解释主要目录和模块的职责）
核心功能（列出主要功能模块）
快速开始（安装、配置、运行步骤）
架构特点（简要说明架构设计亮点）
要求：
使用中文撰写
技术术语保留英文
使用 Markdown 格式
适当使用列表和表格增强可读性
"""
MODULE_TEMPLATE = """
基于以下模块信息，生成模块文档（Markdown 格式）。
模块信息
{{context.module_info}}
类定义
{{context.classes}}
函数定义
{{context.functions}}
依赖关系
{{context.dependencies}}
请生成包含以下章节的模块文档：
模块概述（职责、定位、设计意图）
主要类说明（每个类的职责、关键方法）
函数清单（重要函数的用途和参数）
使用示例（伪代码或简短示例）
依赖说明（依赖哪些模块，被谁依赖）
要求：
使用中文撰写
代码保留原样
重点解释设计意图，而非重复代码
"""
ARCHITECTURE_TEMPLATE = """
基于以下架构分析数据，生成架构设计文档。
依赖图摘要
{{context.dependency_graph}}
关键组件
{{context.key_components}}
架构分层
{{context.layers}}
设计模式
{{context.design_patterns}}
请生成包含以下章节的架构文档：
架构概览（整体架构图描述，使用 Mermaid 语法）
系统分层（各层的职责和交互）
核心组件（关键类的职责和协作关系）
数据流（主要业务流程的数据流转）
设计决策（重要的架构选择和理由）
要求：
包含 Mermaid 图表（flowchart 或 classDiagram）
解释为什么选择当前架构
指出潜在的扩展点
"""


``` python

#### 2.4 MermaidGenerator（图表生成器）

```python
# generator/mermaid_generator.py
from typing import List, Dict
from models.symbol import Symbol, SymbolType

class MermaidGenerator:
    """生成 Mermaid 图表"""
    
    def generate_class_diagram(self, symbols: List[Symbol]) -> str:
        """生成类图"""
        lines = ["classDiagram"]
        
        classes = [s for s in symbols if s.type == SymbolType.CLASS]
        
        for cls in classes:
            lines.append(f"    class {cls.name}{{")
            if hasattr(cls, 'methods'):
                for method_id in cls.methods[:5]:  # 限制方法数
                    method_sym = next((s for s in symbols if s.id == method_id), None)
                    if method_sym:
                        lines.append(f"        +{method_sym.name}()")
            lines.append("    }")
            
            # 继承关系
            if hasattr(cls, 'bases') and cls.bases:
                for base in cls.bases:
                    lines.append(f"    {base} <|-- {cls.name}")
        
        return "\n".join(lines)
    
    def generate_flowchart(self, entry_symbol: Symbol, symbols: List[Symbol], depth: int = 3) -> str:
        """生成流程图（从入口函数开始的调用链）"""
        lines = ["flowchart TD"]
        
        visited = set()
        queue = [(entry_symbol, 0)]
        
        while queue:
            current, level = queue.pop(0)
            if current.id in visited or level > depth:
                continue
            visited.add(current.id)
            
            node_id = current.id.replace('-', '_')
            lines.append(f'    {node_id}["{current.name}"]')
            
            # 查找调用的函数
            if hasattr(current, 'calls'):
                for call_name in current.calls[:5]:  # 限制分支
                    target = self._find_symbol_by_name(call_name, symbols)
                    if target:
                        target_id = target.id.replace('-', '_')
                        lines.append(f"    {node_id} --> {target_id}")
                        queue.append((target, level + 1))
        
        return "\n".join(lines)
    
    def generate_dependency_graph(self, dependencies: Dict) -> str:
        """生成依赖关系图（文件级别）"""
        lines = ["graph LR"]
        
        nodes = dependencies.get('nodes', [])
        edges = dependencies.get('edges', [])
        
        # 按文件分组
        file_deps = {}
        for edge in edges:
            from_node = next((n for n in nodes if n['id'] == edge['from']), None)
            to_node = next((n for n in nodes if n['id'] == edge['to']), None)
            if from_node and to_node:
                from_file = from_node['file']
                to_file = to_node['file']
                if from_file != to_file:
                    file_deps.setdefault(from_file, set()).add(to_file)
        
        # 生成边（限制数量避免过于复杂）
        rendered_files = set()
        for from_file, to_files in list(file_deps.items())[:10]:
            from_name = self._file_to_id(from_file)
            lines.append(f'    {from_name}["{from_file}"]')
            rendered_files.add(from_file)
            
            for to_file in list(to_files)[:3]:
                to_name = self._file_to_id(to_file)
                if to_file not in rendered_files:
                    lines.append(f'    {to_name}["{to_file}"]')
                    rendered_files.add(to_file)
                lines.append(f"    {from_name} --> {to_name}")
        
        return "\n".join(lines)
    
    def _find_symbol_by_name(self, name: str, symbols: List[Symbol]) -> Optional[Symbol]:
        """根据名称查找符号"""
        for sym in symbols:
            if sym.name == name:
                return sym
        return None
    
    def _file_to_id(self, file_path: str) -> str:
        """将文件路径转换为 Mermaid ID"""
        return "f_" + file_path.replace('/', '_').replace('.', '_').replace('-', '_')
```

2.5 DocumentWriter（文档写入器）
``` python
# generator/document_writer.py
from pathlib import Path
from typing import List
from models.document import Document, DocumentSection, DocType
import re

class DocumentWriter:
    """管理文档的写入和更新"""
    
    def __init__(self, wiki_path: str):
        self.wiki_path = Path(wiki_path)
        self.wiki_path.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (self.wiki_path / "modules").mkdir(exist_ok=True)
        (self.wiki_path / "api").mkdir(exist_ok=True)
        (self.wiki_path / "assets").mkdir(exist_ok=True)
    
    def write_document(self, doc: Document):
        """写入单个文档"""
        file_path = self.wiki_path / doc.file_path
        
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入内容
        content = doc.to_markdown()
        file_path.write_text(content, encoding='utf-8')
        
        # 更新索引
        self._update_index(doc)
    
    def write_documents(self, docs: List[Document]):
        """批量写入文档"""
        for doc in docs:
            self.write_document(doc)
        
        # 生成导航文件
        self._generate_nav_file(docs)
    
    def _update_index(self, doc: Document):
        """更新文档索引（用于快速查找）"""
        index_file = self.wiki_path / ".index.json"
        
        index = {}
        if index_file.exists():
            import json
            index = json.loads(index_file.read_text())
        
        index[doc.file_path] = {
            "title": doc.title,
            "type": doc.doc_type.value,
            "updated_at": doc.updated_at.isoformat(),
            "symbols": doc.source_symbols
        }
        
        index_file.write_text(json.dumps(index, indent=2))
    
    def _generate_nav_file(self, docs: List[Document]):
        """生成导航文件（_sidebar.md 或 README）"""
        # 按类型分组
        groups = {}
        for doc in docs:
            groups.setdefault(doc.doc_type.value, []).append(doc)
        
        lines = ["# 文档导航\n"]
        
        # 概览和架构优先
        for doc_type in ['overview', 'architecture', 'module', 'api']:
            if doc_type in groups:
                type_name = {
                    'overview': '项目概览',
                    'architecture': '架构设计',
                    'module': '模块文档',
                    'api': 'API 文档'
                }.get(doc_type, doc_type)
                
                lines.append(f"## {type_name}")
                for doc in sorted(groups[doc_type], key=lambda d: d.file_path):
                    lines.append(f"- [{doc.title}]({doc.file_path})")
                lines.append("")
        
        nav_content = "\n".join(lines)
        (self.wiki_path / "_sidebar.md").write_text(nav_content, encoding='utf-8')
        
        # 同时更新主页 README
        readme_content = self._generate_readme(docs)
        (self.wiki_path / "README.md").write_text(readme_content, encoding='utf-8')
    
    def _generate_readme(self, docs: List[Document]) -> str:
        """生成 Wiki 主页"""
        overview_doc = next((d for d in docs if d.doc_type == DocType.OVERVIEW), None)
        
        lines = [
            "# CodeMind 生成的项目文档",
            "",
            "> 本文档由 CodeMind 自动生成，基于代码静态分析。",
            "> 最后更新：" + docs[0].updated_at.strftime("%Y-%m-%d %H:%M") if docs else "",
            "",
            "## 快速导航",
            "",
            "- [项目概览](00-overview.md)",
            "- [架构设计](01-architecture.md)",
            "- [模块文档](./modules/)",
            "",
            "## 使用说明",
            "",
            "本文档包含以下类型的内容：",
            "- **项目概览**：项目目标、技术栈、快速开始",
            "- **架构设计**：系统架构、核心流程、设计决策",
            "- **模块文档**：各模块的详细说明",
            "",
            "---",
            "",
            "*Generated by CodeMind*"
        ]
        
        return "\n".join(lines)
    
    def clean(self):
        """清理所有生成的文档"""
        import shutil
        if self.wiki_path.exists():
            shutil.rmtree(self.wiki_path)
            self.wiki_path.mkdir(parents=True, exist_ok=True)
```

2.6 Generator 主控类
``` python
# generator/__init__.py
from typing import List, Dict, Optional
from pathlib import Path
import json
import logging

from models.symbol import Symbol, SymbolType
from models.document import Document, DocumentSection, DocType
from generator.context_assembler import ContextAssembler
from generator.llm_agent import LLMAgent, PromptTemplates
from generator.mermaid_generator import MermaidGenerator
from generator.document_writer import DocumentWriter

logger = logging.getLogger(__name__)

class DocumentGenerator:
    """文档生成主控类"""
    
    def __init__(self, project_path: str, storage_path: str, llm_config: Dict):
        self.project_path = Path(project_path)
        self.storage_path = Path(storage_path)
        self.wiki_path = self.storage_path / "wiki"
        
        # 加载解析结果
        self.symbols = self._load_symbols()
        self.dependencies = self._load_dependencies()
        
        # 初始化组件
        self.context_assembler = ContextAssembler(self.symbols, self.dependencies)
        self.llm_agent = LLMAgent(llm_config)
        self.mermaid = MermaidGenerator()
        self.writer = DocumentWriter(str(self.wiki_path))
        
        self.templates = PromptTemplates()
    
    def generate_all(self) -> Dict:
        """
        生成完整 Wiki 文档
        
        Returns:
            生成统计信息
        """
        documents = []
        
        # 1. 生成项目概览
        logger.info("Generating overview document...")
        overview_doc = self._generate_overview()
        documents.append(overview_doc)
        
        # 2. 生成架构文档
        logger.info("Generating architecture document...")
        arch_doc = self._generate_architecture()
        documents.append(arch_doc)
        
        # 3. 生成模块文档（为每个重要模块）
        logger.info("Generating module documents...")
        module_docs = self._generate_module_docs()
        documents.extend(module_docs)
        
        # 4. 写入所有文档
        logger.info("Writing documents to disk...")
        self.writer.write_documents(documents)
        
        return {
            "total_documents": len(documents),
            "overview": overview_doc.file_path,
            "architecture": arch_doc.file_path,
            "modules": len(module_docs),
            "wiki_path": str(self.wiki_path)
        }
    
    def _generate_overview(self) -> Document:
        """生成项目概览文档"""
        context = self.context_assembler.assemble_for_overview()
        
        content = self.llm_agent.generate_document(
            self.templates.OVERVIEW_TEMPLATE,
            context
        )
        
        return Document(
            id="doc_overview",
            doc_type=DocType.OVERVIEW,
            title="项目概览",
            file_path="00-overview.md",
            sections=[
                DocumentSection(
                    title="项目概览",
                    level=1,
                    content=content,
                    order=0
                )
            ],
            source_symbols=[]  # 基于所有符号
        )
    
    def _generate_architecture(self) -> Document:
        """生成架构文档"""
        context = self.context_assembler.assemble_for_architecture()
        
        # 生成架构图
        class_diagram = self.mermaid.generate_class_diagram(self.symbols)
        dep_graph = self.mermaid.generate_dependency_graph(self.dependencies)
        
        # 将图表加入上下文
        context['class_diagram'] = class_diagram
        context['dependency_graph_mermaid'] = dep_graph
        
        content = self.llm_agent.generate_document(
            self.templates.ARCHITECTURE_TEMPLATE,
            context
        )
        
        # 在内容中插入图表
        full_content = f"""
## 类图

```mermaid
{class_diagram}
```

依赖关系
    return Document(
        id="doc_architecture",
        doc_type=DocType.ARCHITECTURE,
        title="架构设计",
        file_path="01-architecture.md",
        sections=[
            DocumentSection(
                title="架构设计",
                level=1,
                content=full_content,
                order=0
            )
        ],
        source_symbols=[]
    )

def _generate_module_docs(self) -> List[Document]:
    """为重要模块生成文档"""
    # 选择重要模块（包含较多符号的文件）
    file_symbol_counts = {}
    for sym in self.symbols:
        if sym.type != SymbolType.MODULE:
            file_symbol_counts[sym.file_path] = file_symbol_counts.get(sym.file_path, 0) + 1
    
    # 排序，选择前 10 个最复杂的文件
    important_files = sorted(
        file_symbol_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    documents = []
    for file_path, count in important_files:
        # 找到模块符号
        module_sym = next(
            (s for s in self.symbols if s.file_path == file_path and s.type == SymbolType.MODULE),
            None
        )
        if not module_sym:
            continue
        
        try:
            doc = self._generate_single_module(module_sym)
            documents.append(doc)
        except Exception as e:
            logger.error(f"Failed to generate doc for {file_path}: {e}")
    
    return documents

def _generate_single_module(self, module_sym: Symbol) -> Document:
    """为单个模块生成文档"""
    context = self.context_assembler.assemble_for_module(module_sym)
    
    content = self.llm_agent.generate_document(
        self.templates.MODULE_TEMPLATE,
        context
    )
    
    # 生成文件名
    safe_name = module_sym.file_path.replace('/', '_').replace('.py', '')
    file_name = f"modules/{safe_name}.md"
    
    return Document(
        id=f"doc_mod_{module_sym.id}",
        doc_type=DocType.MODULE,
        title=f"模块: {module_sym.name}",
        file_path=file_name,
        sections=[
            DocumentSection(
                title=module_sym.name,
                level=1,
                content=content,
                order=0
            )
        ],
        source_symbols=[module_sym.id] + [s.id for s in self.symbols if s.file_path == module_sym.file_path]
    )

def _load_symbols(self) -> List[Symbol]:
    """加载解析的符号"""
    symbols_file = self.storage_path / "index" / "symbols.json"
    if not symbols_file.exists():
        raise FileNotFoundError("Symbols not found. Run parser first.")
    
    data = json.loads(symbols_file.read_text())
    return [Symbol.model_validate(s) for s in data]

def _load_dependencies(self) -> Dict:
    """加载依赖图"""
    deps_file = self.storage_path / "index" / "dependencies.json"
    if not deps_file.exists():
        return {"nodes": [], "edges": []}
    
    return json.loads(deps_file.read_text())

def incremental_update(self, changed_files: List[str]):
    """
    增量更新文档（针对变更的文件）
    
    Args:
        changed_files: 变更的文件路径列表
    """
    # 找到受影响的文档
    affected_docs = []
    for doc in self._list_existing_docs():
        if any(f in doc.source_symbols for f in changed_files):
            affected_docs.append(doc)
    
    # 重新生成受影响的模块文档
    for file_path in changed_files:
        module_sym = next(
            (s for s in self.symbols if s.file_path == file_path and s.type == SymbolType.MODULE),
            None
        )
        if module_sym:
            new_doc = self._generate_single_module(module_sym)
            self.writer.write_document(new_doc)
            logger.info(f"Updated module doc: {file_path}")
    
    # 如果入口文件变更，重新生成概览和架构
    entry_files = {'main.py', 'app.py', '__init__.py'}
    if any(f in entry_files for f in changed_files):
        overview = self._generate_overview()
        self.writer.write_document(overview)
        
        arch = self._generate_architecture()
        self.writer.write_document(arch)
        logger.info("Updated overview and architecture")

def _list_existing_docs(self) -> List[Document]:
    """列出已存在的文档（用于增量更新）"""
    # 简化实现：从索引读取
    index_file = self.wiki_path / ".index.json"
    if not index_file.exists():
        return []
    
    data = json.loads(index_file.read_text())
    docs = []
    for file_path, info in data.items():
        docs.append(Document(
            id=f"existing_{file_path}",
            doc_type=DocType(info['type']),
            title=info['title'],
            file_path=file_path,
            source_symbols=info.get('symbols', [])
        ))
    return docs


---

## 第三部分：Parser 与 Generator 协作流程

### 完整处理流程
┌─────────────────────────────────────────────────────────────────┐
│                     完整构建流程                                │
└─────────────────────────────────────────────────────────────────┘
Phase 1: 解析阶段 (Parser)
───────────────────────────
FileScanner.scan()
└─► 发现所有 Python 文件
└─► 计算 MD5，识别变更文件
TreeSitterParser.parse()
└─► 对每个变更文件生成 AST
└─► 提取函数、类、导入等符号
DependencyAnalyzer.analyze()
└─► 分析符号间调用关系
└─► 构建依赖图
ChunkBuilder.build_chunks()
└─► 将符号转换为文本分片
└─► 计算 token 数量
└─► 长代码智能拆分
持久化到 .codemind/index/
├─► symbols.json
├─► dependencies.json
├─► files.json
└─► chunks/*.json
Phase 2: 生成阶段 (Generator)
─────────────────────────────
ContextAssembler 组装上下文
├─► assemble_for_overview()
├─► assemble_for_architecture()
└─► assemble_for_module()
LLMAgent.generate_document()
└─► 调用 OpenAI API
└─► 生成 Markdown 内容
MermaidGenerator 生成图表
├─► 类图
├─► 依赖图
└─► 流程图
DocumentWriter 写入文件
├─► wiki/00-overview.md
├─► wiki/01-architecture.md
└─► wiki/modules/*.md
Phase 3: 向量化阶段 (Indexer)
─────────────────────────────
加载所有 chunks
使用 OpenAI Embedding API 生成向量
存入 ChromaDB
└─► .codemind/vectors/



### 关键接口定义

```python
# 主控类接口（供 CLI 调用）

class CodeMind:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.storage_path = self.project_path / ".codemind"
        self.config = self._load_config()
    
    def init(self):
        """初始化项目，创建配置和目录"""
        pass
    
    def build(self, full: bool = False):
        """执行完整构建流程"""
        # 1. Parse
        parser = CodeParser(str(self.project_path), str(self.storage_path / "index"))
        stats = parser.parse(incremental=not full)
        
        # 2. Generate
        generator = DocumentGenerator(
            str(self.project_path),
            str(self.storage_path),
            self.config['llm']
        )
        doc_stats = generator.generate_all()
        
        # 3. Index (向量化)
        indexer = VectorIndexer(str(self.storage_path))
        indexer.index_all()
        
        return {**stats, **doc_stats}
    
    def chat(self):
        """启动交互式问答"""
        qa = QAEngine(str(self.storage_path), self.config['llm'])
        qa.interactive_loop()

这份详细设计文档涵盖了 Parser 和 Generator 的完整实现方案，包括：
Parser 模块：
文件扫描与增量检测
Tree-sitter AST 解析
符号提取与依赖分析
智能代码分片
Generator 模块：
上下文智能组装
LLM 提示词工程
Mermaid 图表生成
文档分层写入
你可以基于此直接开始编码实现。建议先实现 Parser 的核心流程（文件扫描 → AST 解析 → 符号保存），验证数据流正确后再实现 Generator。