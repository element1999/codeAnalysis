# 项目概览

# 项目概览

# 项目概览

## 1. 项目简介
CodeMind 是一个智能代码分析和文档生成系统，专为复杂代码库设计。它解决了传统代码文档维护困难、代码理解耗时的问题，为开发团队提供了全面的代码理解和文档管理解决方案。

## 2. 技术栈
- **核心语言**: Python
- **代码解析**: Tree-sitter
- **向量存储**: ChromaDB
- **文本嵌入**: FastEmbed
- **大语言模型**: GLM-4.6v, Ollama, DeepSeek, Kimi, OpenAI
- **命令行界面**: Typer
- **数据验证**: Pydantic
- **终端美化**: Rich

## 3. 项目结构说明
- **codemind/cli**: 命令行界面，提供 init、build、chat、status、clean 等命令
- **codemind/chat**: 智能代码问答功能，基于 RAG 技术
- **codemind/config**: 配置管理，包括项目配置和 LLM 配置
- **codemind/core**: 核心工具和常量定义
- **codemind/embedding**: 文本嵌入功能，支持多种嵌入模型
- **codemind/generator**: 文档生成功能，包括 LLM 代理、文档生成器、文档写入器
- **codemind/parser**: 代码解析功能，包括文件扫描、语法解析、符号提取、依赖分析
- **codemind/storage**: 存储管理，包括 ChromaDB 向量存储和文件存储

## 4. 核心功能
1. **代码库静态分析**: 使用 Tree-sitter 解析代码，提取符号和依赖关系
2. **自动文档生成**: 生成结构化 Wiki 文档，包括项目概览、架构设计和模块文档
3. **智能代码问答**: 基于 RAG 技术，回答项目相关问题
4. **依赖关系分析**: 分析代码依赖和调用链，支持循环检测
5. **版本控制**: 为 Wiki 文档提供版本管理，保留历史版本
6. **增量更新**: 只处理变更的文件，提高生成效率

## 5. 快速开始
### 安装
```bash
pip install -e .
```

### 初始化项目
```bash
codemind init
```

### 生成文档
```bash
codemind build --docs-only
```

### 启动聊天
```bash
codemind chat
```

## 6. 架构特点
- **模块化设计**: 清晰的模块划分，便于扩展和维护
- **插件架构**: 支持多种 LLM 提供商和嵌入模型
- **内存数据结构**: 高效的内存数据结构，支持快速查询
- **JSON 持久化**: 将分析结果持久化到 JSON 文件，支持增量更新
- **透明操作**: 详细的日志和终端输出，让用户了解系统运行状态
- **安全可靠**: 支持多种认证方式和错误处理机制

[MOCK RESPONSE END]
