# CodeMind PRD（产品需求文档）

&gt; **版本**: v1.0.0  
&gt; **日期**: 2026-02-22  
&gt; **状态**: 初稿  
&gt; **目标**: 复刻 DeepWiki 核心能力，服务单个项目，支持 Wiki 生成与智能问答

---

## 1. 产品概述

### 1.1 产品名称
**CodeMind** - 代码智能文档与问答系统

### 1.2 产品定位
面向开发者的 AI 驱动代码理解工具，自动分析项目结构、生成技术文档、回答代码相关问题。

### 1.3 核心能力
1. **自动文档生成**: 分析代码库，生成层级化 Wiki 文档（项目→模块→函数）
2. **智能问答**: 基于代码上下文回答技术问题（RAG 架构）
3. **代码图谱**: 构建函数/类/模块间的依赖关系图
4. **增量更新**: 支持代码变更后的局部更新，无需全量重建

### 1.4 非目标（本期不做）
- 多项目管理（本期仅服务单个项目）
- Web 前端界面（CLI 交互为主）
- 多语言支持（首期支持 Python，后续扩展）
- 分布式部署
- 用户权限管理

---

## 2. 技术架构

### 2.1 技术栈选型

| 组件 | 技术选型 | 理由 |
|------|----------|------|
| **编程语言** | Python 3.10+ | 生态丰富，AI/ML 库支持好 |
| **语法分析** | Tree-sitter | 多语言支持，增量解析，性能优异 |
| **向量存储** | ChromaDB | 本地嵌入，无需外部服务，支持持久化 |
| **LLM 接口** | OpenAI 兼容 API | 支持 GPT-4/DeepSeek/GLM/Kimi/本地 Ollama |
| **嵌入模型** | FastEmbed | 轻量级，本地运行，支持多种模型 |
| **文档存储** | 文件系统 (JSON/Markdown) | 无需数据库，简单可维护 |
| **任务队列** | 本地异步 (asyncio) | 足够支撑单项目处理 |
| **缓存** | 本地文件缓存 | MD5 校验，避免重复计算 |

### 2.2 系统架构图

┌─────────────────────────────────────────────────────────────────┐
│                        CLI 交互层                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  codemind init  │  │ codemind build  │  │ codemind chat   │ │
│  │  初始化项目      │  │ 构建文档索引     │  │ 启动问答会话     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
│
┌─────────────────────────────────────────────────────────────────┐
│                      核心引擎层 (Core Engine)                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ 代码解析器    │  │ 文档生成器    │  │ 问答引擎 (RAG)       │  │
│  │ (Parser)     │  │ (Generator)  │  │ (QA Engine)          │  │
│  ├──────────────┤  ├──────────────┤  ├──────────────────────┤  │
│  │ • Tree-sitter│  │ • 项目分析    │  │ • 向量检索           │  │
│  │ • AST 遍历   │  │ • 模块分析    │  │ • 上下文组装         │  │
│  │ • 依赖提取   │  │ • 函数分析    │  │ • LLM 对话           │  │
│  │ • 符号索引   │  │ • Markdown   │  │ • 引用溯源           │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
│
┌─────────────────────────────────────────────────────────────────┐
│                      存储层 (Storage)                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  项目存储目录 (.codemind/)                               │  │
│  │  ├── config.json          # 项目配置                     │  │
│  │  ├── index/               # 索引数据                     │  │
│  │  │   ├── symbols.json     # 符号表（函数、类、模块）      │  │
│  │  │   ├── dependencies.json # 依赖关系图                  │  │
│  │  │   └── chunks/          # 代码分片（JSON）             │  │
│  │  ├── vectors/             # ChromaDB 向量存储            │  │
│  │  ├── wiki/                # 生成的 Wiki 文档             │  │
│  │  │   ├── 00-overview.md   # 项目概览                     │  │
│  │  │   ├── 01-architecture.md # 架构分析                   │  │
│  │  │   ├── modules/         # 模块文档目录                 │  │
│  │  │   └── api/             # API 文档目录                 │  │
│  │  └── cache/               # 文件缓存（MD5 校验）          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

## 3. 功能模块详细设计

### 3.1 模块一：代码解析器 (Parser)

#### 3.1.1 职责
- 扫描项目文件结构
- 使用 Tree-sitter 解析代码生成 AST
- 提取符号（函数、类、变量）和依赖关系
- 生成代码分片（Chunks）用于向量化

#### 3.1.2 处理流程

```python
# 伪代码流程
def parse_project(project_path):
    # 1. 文件发现
    files = discover_files(project_path, exclude=[".git", "node_modules", ".codemind"])
    
    # 2. 增量处理（基于 MD5 缓存）
    for file in files:
        if is_cached(file) and not is_modified(file):
            continue
        process_file(file)
    
    # 3. AST 解析与符号提取
    for file in new_or_modified_files:
        ast = tree_sitter_parse(file)
        symbols = extract_symbols(ast)  # 函数、类、方法
        dependencies = extract_dependencies(ast)  # import, from, call
        
    # 4. 构建依赖图
    dependency_graph = build_graph(symbols, dependencies)
    
    # 5. 生成代码分片
    chunks = create_chunks(symbols, max_tokens=512)
    
    # 6. 持久化
    save_symbols(symbols)
    save_graph(dependency_graph)
    save_chunks(chunks)

#### 3.1.3 数据结构
符号表 (symbols.json)
{
  "symbols": [
    {
      "id": "sym_001",
      "name": "UserService",
      "type": "class",
      "file": "src/services/user.py",
      "line_start": 15,
      "line_end": 45,
      "docstring": "用户服务类，处理用户相关逻辑...",
      "methods": ["get_user", "create_user"],
      "dependencies": ["sym_002", "sym_003"]
    }
  ]
}

依赖图 (dependencies.json)
{
  "nodes": [{"id": "sym_001", "label": "UserService"}],
  "edges": [
    {"from": "sym_001", "to": "sym_002", "type": "imports"},
    {"from": "sym_001", "to": "sym_003", "type": "calls"}
  ]
}

代码分片 (chunks/sym_001.json)
{
  "symbol_id": "sym_001",
  "content": "class UserService:\n    def __init__(self, db: Database):\n        self.db = db\n    ...",
  "tokens": 180,
  "embedding": null  // 由向量存储管理
}

3.2 模块二：文档生成器 (Generator)
3.2.1 职责
分析项目整体架构
生成层级化 Markdown 文档
自动创建架构图（Mermaid）
支持增量更新
3.2.2 文档层级结构
wiki/
├── 00-overview.md          # 项目概览（目标、技术栈、快速开始）
├── 01-architecture.md      # 架构分析（系统架构图、核心流程）
├── 02-data-model.md        # 数据模型（如有）
├── modules/                # 模块文档
│   ├── index.md           # 模块总览
│   ├── user-service.md    # 具体模块文档
│   └── order-service.md
├── api/                    # API 文档（如适用）
│   └── index.md
└── assets/                 # 图片资源
    └── architecture.png

2.3 生成策略
采用三阶段生成（类似 DeepWiki）：
项目级分析: 分析整体结构、技术栈、入口点
模块级分析: 分析每个模块的职责、接口、依赖
函数级分析: 详细解释关键函数的逻辑

提示词模板示例：

# 项目概览生成提示词
你是一位资深架构师，请分析以下代码库信息，生成项目概览文档。

## 输入信息
- 项目结构：{project_tree}
- 主要依赖：{dependencies}
- 入口文件：{entry_points}
- 配置文件：{config_files}

## 输出要求
1. 项目目标与定位（1-2段话）
2. 技术栈清单（带版本）
3. 核心功能模块列表
4. 快速开始指南（安装、运行）
5. 架构特点总结

请使用 Markdown 格式，技术术语使用英文。

3.3 模块三：问答引擎 (QA Engine)
3.3.1 职责
接收用户自然语言问题
检索相关代码上下文（RAG）
组装提示词并调用 LLM
返回答案并标注引用来源

3.3.2 RAG 流程

def answer_question(question: str) -> Answer:
    # 1. 问题向量化
    query_embedding = embed(question)
    
    # 2. 向量检索（ChromaDB）
    relevant_chunks = chroma.query(
        query_embeddings=[query_embedding],
        n_results=5,
        where={"type": "code"}  # 可过滤代码/文档
    )
    
    # 3. 重排序（可选）
    ranked_chunks = rerank(relevant_chunks, question)
    
    # 4. 上下文组装
    context = assemble_context(ranked_chunks, max_tokens=3000)
    
    # 5. LLM 生成
    prompt = build_qa_prompt(question, context)
    answer = llm.generate(prompt)
    
    # 6. 溯源处理
    citations = extract_citations(answer, ranked_chunks)
    
    return Answer(content=answer, citations=citations)

3.3.3 引用溯源
答案中需包含代码引用标记，例如：
用户服务通过 Database 类进行数据操作 [1]。
[1] src/services/user.py:15 - class UserService

4. CLI 接口设计
4.1 命令列表

# 初始化项目（创建 .codemind/ 目录）
codemind init [project_path]
# 交互式配置：选择 LLM 模型、嵌入模型等

# 构建/更新索引和文档
codemind build
# 选项：
#   --full: 全量重建（忽略缓存）
#   --docs-only: 仅重新生成文档（不重新解析代码）
#   --workers: 并行工作数（默认 4）

# 启动交互式问答
codemind chat
# 支持命令：
#   /help: 显示帮助
#   /refresh: 刷新上下文
#   /save <file>: 保存对话历史
#   /exit: 退出

# 查看项目状态
codemind status
# 显示：文件数、符号数、索引状态、最后更新时间

# 清理缓存和索引
codemind clean
# 选项：
#   --cache: 仅清理文件缓存
#   --vectors: 仅清理向量存储
#   --all: 清理所有（保留配置）

4.2 配置管理
配置文件 (.codemind/config.json):
{
  "project": {
    "name": "my-project",
    "path": "/path/to/project",
    "language": "python",
    "entry_points": ["src/main.py", "src/app.py"]
  },
  "llm": {
    "provider": "ollama",
    "model": "llama3.2",
    "api_key": null,
    "base_url": "http://localhost:11434/v1",
    "temperature": 0.3,
    "max_tokens": 4000
  },
  "embedding": {
    "provider": "fastembed",
    "model": "BAAI/bge-small-en-v1.5",
    "dimension": 384
  },
  "parser": {
    "exclude_dirs": [".git", "node_modules", "__pycache__", ".codemind"],
    "include_patterns": ["*.py"],
    "max_file_size": "1MB"
  },
  "generator": {
    "doc_language": "zh",
    "max_workers": 4
  }
}

支持的 LLM 提供商：

1. **Ollama（本地模型）**
```json
{
  "llm": {
    "provider": "ollama",
    "model": "llama3.2",
    "api_key": null,
    "base_url": "http://localhost:11434/v1"
  }
}
```

2. **DeepSeek**
```json
{
  "llm": {
    "provider": "deepseek",
    "model": "deepseek-chat",
    "api_key": "${DEEPSEEK_API_KEY}",
    "base_url": "https://api.deepseek.com/v1"
  }
}
```

3. **GLM（智谱AI）**
```json
{
  "llm": {
    "provider": "glm",
    "model": "glm-4",
    "api_key": "${GLM_API_KEY}",
    "base_url": "https://open.bigmodel.cn/api/paas/v4"
  }
}
```

4. **Kimi（月之暗面）**
```json
{
  "llm": {
    "provider": "kimi",
    "model": "moonshot-v1-8k",
    "api_key": "${KIMI_API_KEY}",
    "base_url": "https://api.moonshot.cn/v1"
  }
}
```

5. **OpenAI**
```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4",
    "api_key": "${OPENAI_API_KEY}",
    "base_url": null
  }
}
```

支持的 Embedding 提供商：

1. **FastEmbed（推荐）**
```json
{
  "embedding": {
    "provider": "fastembed",
    "model": "BAAI/bge-small-en-v1.5",
    "dimension": 384
  }
}
```

支持的 FastEmbed 模型：
- `BAAI/bge-small-en-v1.5` (384维，英文)
- `BAAI/bge-base-en-v1.5` (768维，英文)
- `BAAI/bge-small-zh-v1.5` (512维，中文)
- `BAAI/bge-base-zh-v1.5` (768维，中文)
- `sentence-transformers/all-MiniLM-L6-v2` (384维，多语言)

5. 数据存储规范
5.1 目录结构
.codemind/
├── config.json              # 项目配置（用户可编辑）
├── state.json               # 运行状态（自动维护）
├── index/
│   ├── files.json           # 文件清单与 MD5 校验
│   ├── symbols.json         # 符号表
│   ├── dependencies.json    # 依赖关系图
│   └── chunks/              # 代码分片（按符号 ID 分文件）
│       ├── sym_001.json
│       └── ...
├── vectors/                 # ChromaDB 数据目录
│   ├── chroma.sqlite3
│   └── ...
├── wiki/                    # 生成的文档
│   ├── 00-overview.md
│   ├── 01-architecture.md
│   └── modules/
└── cache/                   # 文件内容缓存
    └── {md5_hash}.json

5.2 存储说明
不使用 SQLite: 所有元数据使用 JSON 文件存储
ChromaDB: 仅用于向量存储，使用其本地持久化模式
文件缓存: 基于 MD5 哈希，避免重复读取大文件
增量更新: 通过对比文件修改时间和 MD5 实现

6. 关键算法与逻辑
6.1 代码分片策略

def create_chunks(symbol, max_tokens=512):
    """
    将代码符号分块，保持语义完整性
    策略：
    1. 优先按逻辑块分割（函数、类、方法）
    2. 大块进一步按段落分割
    3. 每个分片保留上下文信息（所属文件、类、行号）
    """
    chunks = []
    
    # 类：拆分为类定义 + 各个方法
    if symbol.type == "class":
        # 类头部分（docstring + 属性定义）
        header = extract_class_header(symbol)
        chunks.append(create_chunk(header, type="class_header"))
        
        # 每个方法单独成块
        for method in symbol.methods:
            if count_tokens(method) > max_tokens:
                chunks.extend(split_method(method))
            else:
                chunks.append(create_chunk(method, type="method"))
    
    # 函数：直接分块或进一步拆分
    elif symbol.type == "function":
        if count_tokens(symbol) > max_tokens:
            chunks.extend(split_by_paragraphs(symbol, max_tokens))
        else:
            chunks.append(create_chunk(symbol, type="function"))
    
    return chunks

6.2 增量更新逻辑
``` python
def incremental_update():
    """
    增量更新流程：
    1. 扫描当前文件列表
    2. 对比已索引文件（路径 + MD5）
    3. 处理变更：
       - 新增文件：完整解析
       - 修改文件：重新解析，更新相关符号
       - 删除文件：移除相关符号和分片
    4. 更新依赖图（级联更新受影响的符号）
    5. 重新生成受影响的文档
    """
    current_files = scan_files()
    indexed_files = load_indexed_files()
    
    changes = diff_files(current_files, indexed_files)
    
    for file in changes.added:
        parse_and_index(file)
    
    for file in changes.modified:
        old_symbols = get_symbols_by_file(file)
        new_symbols = parse_and_index(file)
        affected = find_affected_symbols(old_symbols, new_symbols)
        mark_for_rebuild(affected)
    
    for file in changes.deleted:
        remove_symbols_by_file(file)
    
    rebuild_dependency_graph()
    rebuild_affected_documents()
```
7. 非功能性需求
7.2 扩展性设计
语言扩展: Tree-sitter 支持 30+ 语言，通过配置添加新语言解析器
模型切换: 通过配置切换不同 LLM 提供商（OpenAI、Anthropic、本地模型）
嵌入模型: 支持更换不同维度的嵌入模型（需重建向量索引）
7.3 错误处理
解析错误: 跳过无法解析的文件，记录警告，继续处理其他文件
LLM 超时: 重试 3 次，失败后返回友好提示
存储损坏: 提供 codemind repair 命令尝试修复，或提示重新构建

9. 附录
9.1 依赖库清单
# 核心依赖
tree-sitter>=0.20.0
tree-sitter-python>=0.20.0
chromadb>=0.4.0
fastembed>=0.2.0
openai>=1.0.0
pydantic>=2.0.0
typer>=0.9.0  # CLI 框架
rich>=13.0.0  # 终端美化
aiofiles>=23.0.0  # 异步文件操作

# 可选依赖
tree-sitter-javascript>=0.20.0
tree-sitter-java>=0.20.0

10. 待决策事项
是否支持多轮对话上下文？
建议：支持多轮对话
是否自动生成架构图（Mermaid）？
建议：使用 LLM 生成 Mermaid 代码

---
