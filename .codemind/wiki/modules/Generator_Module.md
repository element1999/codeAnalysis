# 模块: Generator Module

# Generator Module

```markdown
# Generator Module 文档

## 1. 模块概述

**职责**：负责文档生成和输出格式化，是 CodeMind 项目中核心的文档生成模块。

**定位**：作为项目文档生成的核心引擎，负责整合代码分析结果，通过 LLM 生成结构化的文档内容，并支持多种输出格式（如 Markdown、Mermaid 图表等）。

**设计意图**：通过模块化的设计，将文档生成的不同职责分离，包括：
- 上下文组装：收集和整理代码分析结果
- LLM 集成：与大型语言模型交互生成文档内容
- 文档写入：管理文档的输出和版本控制
- 图表生成：支持架构可视化

## 2. 包含文件

| 文件路径 | 作用描述 |
|---------|---------|
| `codemind/generator/__init__.py` | 模块初始化文件，定义公共接口 |
| `codemind/generator/base.py` | 定义生成器抽象基类和文档生成器基类 |
| `codemind/generator/context_assembler.py` | 上下文组装器，负责收集和整理代码分析结果 |
| `codemind/generator/document_generator.py` | 主文档生成器，协调整个文档生成流程 |
| `codemind/generator/document_writer.py` | 文档写入器，管理文档输出和版本控制 |
| `codemind/generator/llm_agent.py` | LLM 代理，处理与大型语言模型的交互 |
| `codemind/generator/llm_generator.py` | 基于 LLM 的文档生成器实现 |
| `codemind/generator/manager.py` | 生成器管理器，提供高层接口 |
| `codemind/generator/mermaid_generator.py` | Mermaid 图表生成器，支持架构可视化 |

## 3. 核心功能

### 3.1 文档生成流程
- **代码映射生成**：分析项目文件结构，生成代码映射
- **模块划分建议**：通过 LLM 分析项目结构，建议逻辑模块划分
- **文档生成**：为每个模块生成详细的文档内容
- **架构文档生成**：生成项目架构分析文档
- **概览文档生成**：生成项目概览文档

### 3.2 输出格式支持
- **Markdown 文档**：生成标准的 Markdown 格式文档
- **Mermaid 图表**：支持生成类图、流程图、依赖关系图等可视化图表
- **版本控制**：支持文档的版本管理和增量更新

### 3.3 LLM 集成功能
- **多提供商支持**：支持 Ollama、DeepSeek 等多种 LLM 提供商
- **流式输出**：支持流式生成，适用于交互式场景
- **提示模板管理**：提供可配置的提示模板库

## 4. 关键组件

### 4.1 核心类

#### ContextAssembler
- **职责**：组装 LLM 文档生成所需的上下文信息
- **主要方法**：
  - `assemble_for_overview()`：组装项目概览上下文
  - `assemble_for_module()`：组装特定模块上下文
  - `assemble_for_architecture()`：组装架构分析上下文
  - `_summarize_symbol()`：符号信息摘要
  - `_build_signature()`：构建函数签名
  - `_calculate_stats()`：计算项目统计信息

#### DocumentGenerator
- **职责**：主文档生成器，协调整个文档生成流程
- **主要方法**：
  - `generate_all()`：生成完整的 Wiki 文档
  - `_generate_overview()`：生成项目概览文档
  - `_generate_architecture()`：生成架构文档
  - `_generate_module_docs()`：生成模块文档
  - `incremental_update()`：增量更新文档

#### DocumentWriter
- **职责**：管理文档写入和版本控制
- **主要方法**：
  - `write_document()`：写入单个文档
  - `write_documents()`：批量写入文档（带版本控制）
  - `_generate_nav_file()`：生成导航文件
  - `_generate_readme()`：生成 Wiki 首页
  - `clean()`：清理所有生成的文档

#### LLMAgent
- **职责**：LLM 交互包装器，支持多种 LLM 提供商
- **主要方法**：
  - `generate_document()`：生成文档内容
  - `generate_stream()`：流式生成
  - `chat()`：通用聊天接口
  - `_assemble_prompt()`：组装提示词
  - `_clean_markdown()`：清理 Markdown 输出格式

#### LLMGenerator
- **职责**：基于 LLM 的文档生成器实现
- **主要方法**：
  - `generate()`：生成内容
  - `generate_symbol_docs()`：为符号生成文档
  - `generate_chunk_docs()`：为代码块生成文档
  - `generate_summary()`：生成项目摘要

#### MermaidGenerator
- **职责**：生成 Mermaid 图表用于架构可视化
- **主要方法**：
  - `generate_class_diagram()`：生成类图
  - `generate_flowchart()`：生成流程图
  - `generate_dependency_graph()`：生成依赖关系图

#### GeneratorManager
- **职责**：生成器管理器，提供高层接口
- **主要方法**：
  - `generate_docs()`：生成项目文档
  - `update_docs()`：更新文档

## 5. 使用方法

### 5.1 基本使用流程

```python
# 1. 初始化生成器管理器
manager = GeneratorManager(llm_config, generator_config)

# 2. 生成项目文档
stats = manager.generate_docs(project_path, storage_path)

# 3. 增量更新（当文件变更时）
changed_files = ["src/module1.py", "src/module2.py"]
update_stats = manager.update_docs(project_path, storage_path, changed_files)
```

### 5.2 配置示例

```python
# LLM 配置示例
llm_config = {
    "provider": "ollama",
    "model": "codellama",
    "max_tokens": 4000,
    "temperature": 0.3,
    "mock": False
}

# 生成器配置示例
generator_config = {
    "output_format": "markdown",
    "include_diagrams": True,
    "version_control": True
}
```

### 5.3 自定义提示模板

```python
# 使用 PromptTemplates 自定义提示
from codemind.generator.llm_agent import PromptTemplates

templates = PromptTemplates()
templates.add_template("module_docs", """
请为以下模块生成详细的文档：

模块名：{{context.module_info.name}}
文件列表：{{context.module_info.files}}

请包含以下内容：
1. 模块概述
2. 主要功能
3. 关键类和方法
4. 使用示例
5. 注意事项
""")
```

## 6. 依赖关系

### 6.1 模块间依赖

- **DocumentGenerator** 依赖：
  - `ContextAssembler`：用于组装文档上下文
  - `LLMAgent`：用于与 LLM 交互
  - `DocumentWriter`：用于写入文档

- **LLMAgent** 依赖：
  - `LLMGenerator`：具体的 LLM 生成实现
  - `PromptTemplates`：提示模板管理

- **MermaidGenerator** 依赖：
  - 基础的符号数据结构

### 6.2 外部依赖

| 依赖项 | 用途 |
|--------|------|
| `codemind` | 核心框架依赖 |
| `abc` | 抽象基类支持 |
| `typing` | 类型提示支持 |
| `json` | JSON 数据处理 |
| `logging` | 日志记录 |
| `pathlib` | 路径操作 |
| `os` | 操作系统接口 |
| `openai` | OpenAI API 客户端 |
| `enum` | 枚举类型支持 |

### 6.3 与其他模块的关系

- **Parser 模块**：依赖解析结果（符号、依赖图）
- **Storage 模块**：读取存储的解析结果
- **UI 模块**：提供文档生成的用户界面
