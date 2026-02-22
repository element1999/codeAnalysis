"""LLM agent for document generation"""

import openai
from typing import List, Dict, Optional, Generator, Union
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM provider enum"""
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"
    GLM = "glm"
    KIMI = "kimi"
    OPENAI = "openai"


class LLMAgent:
    """LLM interaction wrapper, supporting multiple LLM providers"""
    
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
        self.mock = config.get('mock', False)
        
        # Initialize client only if not in mock mode
        if not self.mock:
            self.client = self._init_client()
        else:
            self.client = None
            logger.info("LLMAgent initialized in MOCK mode - no actual LLM calls will be made")
    
    def _init_client(self) -> openai.OpenAI:
        """Initialize OpenAI client based on provider"""
        provider_config = self.PROVIDER_CONFIGS[self.provider]
        
        # Get API Key
        api_key = self.config.get('api_key')
        if provider_config['requires_api_key'] and not api_key:
            raise ValueError(f"{self.provider.value} requires api_key")
        
        # For providers that don't require API key (like Ollama), set a dummy value
        if not api_key:
            api_key = "dummy_key"  # OpenAI client requires this parameter
        
        # Get base_url
        base_url = self.config.get('base_url', provider_config['default_base_url'])
        
        return openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    def generate_document(self, prompt: str, context: Dict) -> str:
        """
        Generate document content
        
        Args:
            prompt: Prompt template
            context: Context data (will be formatted as JSON and inserted into prompt)
        
        Returns:
            Generated Markdown content
        """
        from rich.console import Console
        console = Console()
        
        full_prompt = self._assemble_prompt(prompt, context)
        
        # Display LLM request details directly to user
        console.print("[bold blue]=== LLM Request Details ===[/bold blue]")
        console.print(f"[green]Model:[/green] {self.model}")
        console.print(f"[green]Provider:[/green] {self.provider.value}")
        console.print(f"[green]Base URL:[/green] {self.client.base_url if self.client else 'N/A (Mock mode)'}")
        console.print(f"[green]Temperature:[/green] {self.temperature}")
        console.print(f"[green]Max Tokens:[/green] {self.max_tokens}")
        console.print(f"[green]Prompt length:[/green] {len(full_prompt)} characters")
        console.print(f"[green]Mode:[/green] {'MOCK' if self.mock else 'REAL'}")
        console.print()
        
        console.print("[bold cyan]System Prompt:[/bold cyan]")
        console.print("You are a technical documentation expert. Generate clear, structured Markdown documentation based on the provided code context.")
        console.print()
        
        console.print("[bold cyan]User Prompt (Preview):[/bold cyan]")
        console.print(f"{full_prompt[:1000]}...")
        console.print()
        
        # Log full request details
        logger.debug("LLM Request Details:")
        logger.debug(f"Model: {self.model}")
        logger.debug(f"Provider: {self.provider.value}")
        logger.debug(f"Base URL: {self.client.base_url if self.client else 'N/A (Mock mode)'}")
        logger.debug(f"Temperature: {self.temperature}")
        logger.debug(f"Max Tokens: {self.max_tokens}")
        logger.debug(f"Mode: {'MOCK' if self.mock else 'REAL'}")
        logger.debug(f"Full Prompt: {full_prompt}")
        
        if self.mock:
            # Mock mode - return simulated response
            console.print("[bold blue]=== MOCK Mode Activated ===[/bold blue]")
            console.print("[yellow]No actual LLM call will be made. Returning mock response.[/yellow]")
            console.print()
            
            # Generate different mock responses based on prompt type
            if "生成详细的项目概览文档" in full_prompt:
                # Project overview document request
                mock_content = f"# 项目概览\n\n## 1. 项目简介\nCodeMind 是一个智能代码分析和文档生成系统，专为复杂代码库设计。它解决了传统代码文档维护困难、代码理解耗时的问题，为开发团队提供了全面的代码理解和文档管理解决方案。\n\n## 2. 技术栈\n- **核心语言**: Python\n- **代码解析**: Tree-sitter\n- **向量存储**: ChromaDB\n- **文本嵌入**: FastEmbed\n- **大语言模型**: GLM-4.6v, Ollama, DeepSeek, Kimi, OpenAI\n- **命令行界面**: Typer\n- **数据验证**: Pydantic\n- **终端美化**: Rich\n\n## 3. 项目结构说明\n- **codemind/cli**: 命令行界面，提供 init、build、chat、status、clean 等命令\n- **codemind/chat**: 智能代码问答功能，基于 RAG 技术\n- **codemind/config**: 配置管理，包括项目配置和 LLM 配置\n- **codemind/core**: 核心工具和常量定义\n- **codemind/embedding**: 文本嵌入功能，支持多种嵌入模型\n- **codemind/generator**: 文档生成功能，包括 LLM 代理、文档生成器、文档写入器\n- **codemind/parser**: 代码解析功能，包括文件扫描、语法解析、符号提取、依赖分析\n- **codemind/storage**: 存储管理，包括 ChromaDB 向量存储和文件存储\n\n## 4. 核心功能\n1. **代码库静态分析**: 使用 Tree-sitter 解析代码，提取符号和依赖关系\n2. **自动文档生成**: 生成结构化 Wiki 文档，包括项目概览、架构设计和模块文档\n3. **智能代码问答**: 基于 RAG 技术，回答项目相关问题\n4. **依赖关系分析**: 分析代码依赖和调用链，支持循环检测\n5. **版本控制**: 为 Wiki 文档提供版本管理，保留历史版本\n6. **增量更新**: 只处理变更的文件，提高生成效率\n\n## 5. 快速开始\n### 安装\n```bash\npip install -e .\n```\n\n### 初始化项目\n```bash\ncodemind init\n```\n\n### 生成文档\n```bash\ncodemind build --docs-only\n```\n\n### 启动聊天\n```bash\ncodemind chat\n```\n\n## 6. 架构特点\n- **模块化设计**: 清晰的模块划分，便于扩展和维护\n- **插件架构**: 支持多种 LLM 提供商和嵌入模型\n- **内存数据结构**: 高效的内存数据结构，支持快速查询\n- **JSON 持久化**: 将分析结果持久化到 JSON 文件，支持增量更新\n- **透明操作**: 详细的日志和终端输出，让用户了解系统运行状态\n- **安全可靠**: 支持多种认证方式和错误处理机制\n\n[MOCK RESPONSE END]"
            elif "生成架构设计文档" in full_prompt or "architecture" in full_prompt.lower():
                # Architecture document request
                mock_content = f"# 架构设计\n\n## 1. 架构概览\nCodeMind 采用分层架构设计，从底层的代码解析到上层的文档生成和用户交互，形成了完整的代码分析和文档生成 pipeline。\n\n## 2. 系统分层\n### 核心层\n- **代码解析**: Tree-sitter 解析器、符号提取器、依赖分析器\n- **存储层**: ChromaDB 向量存储、文件存储、内存数据结构\n- **嵌入层**: FastEmbed 文本嵌入、向量索引管理\n\n### 功能层\n- **文档生成**: LLM 代理、文档生成器、文档写入器、Mermaid 图表生成\n- **智能问答**: RAG 检索、聊天管理器、会话管理\n- **命令行界面**: 命令解析、参数验证、进度展示\n\n### 接口层\n- **CLI 命令**: init、build、chat、status、clean\n- **配置管理**: 项目配置、LLM 配置、生成器配置\n\n## 3. 核心组件\n- **FileScanner**: 扫描项目文件，构建文件树\n- **TreeSitterParser**: 使用 Tree-sitter 解析代码，生成语法树\n- **SymbolExtractor**: 从语法树中提取符号（函数、类、变量等）\n- **DependencyAnalyzer**: 分析符号之间的依赖关系，构建依赖图\n- **ChunkBuilder**: 将代码分割成小块，用于嵌入和检索\n- **StorageManager**: 管理存储，包括向量存储和文件存储\n- **LLMAgent**: 与大语言模型交互，生成文档和回答问题\n- **DocumentGenerator**: 生成结构化文档，包括项目概览、架构设计和模块文档\n- **DocumentWriter**: 写入文档到磁盘，管理版本控制\n- **ChatManager**: 管理聊天会话，处理用户查询\n\n## 4. 数据流\n1. **代码分析流程**: 文件扫描 → 语法解析 → 符号提取 → 依赖分析 → 代码分块 → 向量嵌入 → 存储\n2. **文档生成流程**: 代码映射生成 → 项目背景提取 → 模块划分 → 架构文档生成 → 模块文档生成 → 项目概览生成 → 文档写入\n3. **聊天流程**: 用户查询 → RAG 检索 → 上下文构建 → LLM 生成 → 响应返回\n\n## 5. 设计决策\n- **使用 Tree-sitter**: 选择 Tree-sitter 作为代码解析器，支持多种编程语言，解析速度快，准确率高\n- **使用 ChromaDB**: 选择 ChromaDB 作为向量存储，轻量级，易于集成，支持增量更新\n- **使用 FastEmbed**: 选择 FastEmbed 作为文本嵌入库，速度快，内存占用小，适合生产环境\n- **模块化设计**: 采用模块化设计，便于扩展和维护，支持插件架构\n- **内存数据结构**: 使用内存数据结构存储分析结果，提高查询速度，支持 JSON 持久化\n- **版本控制**: 为 Wiki 文档提供版本管理，保留历史版本，支持回滚\n\n## 6. 扩展点\n- **LLM 提供商**: 支持多种 LLM 提供商，可根据需要添加新的提供商\n- **嵌入模型**: 支持多种嵌入模型，可根据需要切换不同的模型\n- **代码解析**: 支持多种编程语言，可根据需要添加新的语言支持\n- **文档格式**: 支持 Markdown 格式，可根据需要添加其他格式支持\n- **存储后端**: 支持 ChromaDB 和文件存储，可根据需要添加其他存储后端\n\n[MOCK RESPONSE END]"
            elif "生成模块文档" in full_prompt or "模块信息" in full_prompt:
                # Module document request
                # Extract module name from prompt
                import re
                module_name_match = re.search(r'名称: (.*?)\n', full_prompt)
                module_name = module_name_match.group(1) if module_name_match else "Unknown Module"
                
                mock_content = f"# {module_name}\n\n## 1. 模块概述\n{module_name} 模块是 CodeMind 系统的核心组件之一，负责处理特定功能域的任务。该模块采用模块化设计，与其他模块保持松耦合，便于单独开发和测试。\n\n## 2. 包含文件\n- **file1.py**: 模块的主要入口文件，定义核心功能\n- **file2.py**: 辅助功能实现，提供工具函数\n- **file3.py**: 数据模型定义，用于模块内部数据结构\n\n## 3. 核心功能\n- **功能一**: 详细描述功能一的作用和实现\n- **功能二**: 详细描述功能二的作用和实现\n- **功能三**: 详细描述功能三的作用和实现\n\n## 4. 关键组件\n- **Class1**: 核心类，实现模块的主要功能\n- **Class2**: 辅助类，提供支持功能\n- **function1**: 关键函数，实现核心逻辑\n- **function2**: 工具函数，提供通用功能\n\n## 5. 使用方法\n```python\n# 导入模块\nfrom codemind.module import Class1, function1\n\n# 创建实例\ninstance = Class1()\n\n# 调用方法\nresult = instance.method1()\n\n# 使用函数\nresult = function1()\n```\n\n## 6. 依赖关系\n- **依赖模块 1**: 提供基础功能支持\n- **依赖模块 2**: 提供数据存储服务\n- **被依赖模块**: 被其他模块调用，提供核心功能\n\n[MOCK RESPONSE END]"
            else:
                # Default mock response
                mock_content = f"# Mock Response\n\nThis is a mock response generated in MOCK mode.\n\n## Request Summary\n- Model: {self.model}\n- Provider: {self.provider.value}\n- Prompt length: {len(full_prompt)} characters\n- Temperature: {self.temperature}\n- Max Tokens: {self.max_tokens}\n\n## Mock Content\nThis is a simulated response that would be generated by the LLM based on the provided prompt.\nIn real mode, the LLM would analyze the code context and generate comprehensive documentation.\n\n### Key sections that would be generated:\n- Detailed analysis of the codebase\n- Structured documentation with clear sections\n- Technical explanations and insights\n- Usage examples and best practices\n\n[MOCK RESPONSE END]"
            
            # Display mock response details
            console.print("[bold blue]=== Mock Response Details ===[/bold blue]")
            console.print(f"[green]Response status:[/green] Success (Mock)")
            console.print(f"[green]Usage:[/green] Prompt tokens: {len(full_prompt) // 4}, Completion tokens: {len(mock_content) // 4}, Total tokens: {(len(full_prompt) + len(mock_content)) // 4}")
            console.print(f"[green]Response ID:[/green] mock_{hash(full_prompt) % 1000000}")
            console.print()
            
            # Log mock response details
            logger.debug("LLM Mock Response Details:")
            logger.debug(f"Response ID: mock_{hash(full_prompt) % 1000000}")
            logger.debug(f"Mock Content: {mock_content}")
            
            console.print("[bold cyan]Generated Content (Preview):[/bold cyan]")
            console.print(f"{mock_content[:1000]}...")
            console.print()
            console.print(f"[green]✓ Mock content generated successfully! Total length: {len(mock_content)} characters[/green]")
            console.print()
            
            return mock_content
        else:
            # Real mode - make actual LLM call
            try:
                console.print("[bold blue]Sending request to LLM...[/bold blue]")
                console.print("[yellow]This may take a few moments...[/yellow]")
                console.print()
                
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
                
                # Display LLM response details directly to user
                console.print("[bold blue]=== LLM Response Details ===[/bold blue]")
                console.print(f"[green]Response status:[/green] Success")
                console.print(f"[green]Usage:[/green] Prompt tokens: {response.usage.prompt_tokens}, Completion tokens: {response.usage.completion_tokens}, Total tokens: {response.usage.total_tokens}")
                console.print(f"[green]Response ID:[/green] {response.id}")
                console.print()
                
                # Log full response details
                logger.debug("LLM Response Details:")
                logger.debug(f"Response ID: {response.id}")
                logger.debug(f"Usage: Prompt tokens: {response.usage.prompt_tokens}, Completion tokens: {response.usage.completion_tokens}, Total tokens: {response.usage.total_tokens}")
                logger.debug(f"Full Response: {response}")
                
                content = response.choices[0].message.content
                content = self._clean_markdown(content)
                
                console.print("[bold cyan]Generated Content (Preview):[/bold cyan]")
                console.print(f"{content[:1000]}...")
                console.print()
                console.print(f"[green]✓ Content generated successfully! Total length: {len(content)} characters[/green]")
                console.print()
                
                # Log generated content
                logger.debug(f"Generated Content (Full): {content}")
                
                return content
                
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                logger.debug(f"Failed request prompt: {full_prompt[:500]}...")
                console.print(f"[red]✗ LLM generation failed: {e}[/red]")
                import traceback
                traceback.print_exc()
                raise
    
    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        """Stream generation (for chat command)"""
        if self.mock:
            # Mock mode - return simulated streaming response
            logger.debug(f"Stream generation in MOCK mode: {prompt[:100]}...")
            
            mock_response = f"This is a mock streaming response generated in MOCK mode.\n\nThe LLM would normally analyze your request and generate a detailed response, but in mock mode, we're returning this simulated output.\n\nRequest: {prompt[:200]}...\n\n[MOCK STREAMING RESPONSE END]"
            
            # Simulate streaming by yielding chunks
            chunks = mock_response.split(' ')
            for i, chunk in enumerate(chunks):
                yield chunk + (' ' if i < len(chunks) - 1 else '')
            
            return
        
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
        General chat interface, supporting multi-turn conversations
        
        Args:
            messages: Message list [{"role": "user", "content": "..."}, ...]
            stream: Whether to use streaming output
        
        Returns:
            Generated response or streaming generator
        """
        # Log chat request
        logger.debug(f"Chat request: messages={messages}, stream={stream}, mode={'MOCK' if self.mock else 'REAL'}")
        
        if self.mock:
            # Mock mode - return simulated response
            logger.debug("Chat in MOCK mode")
            
            # Extract user message content
            user_message = ""
            for msg in messages:
                if msg.get('role') == 'user':
                    user_message = msg.get('content', '')
                    break
            
            # Generate different mock responses based on request type
            if "summarize the following project information into a concise project background" in user_message.lower():
                # Project background summary request
                mock_response = "CodeMind 是一个智能代码分析和文档生成系统，专为复杂代码库设计。它解决了传统代码文档维护困难、代码理解耗时的问题。主要功能包括：代码库静态分析、自动生成结构化 Wiki 文档、智能代码问答、依赖关系分析和调用链检测。技术栈包括 Python、Tree-sitter、ChromaDB、FastEmbed 和多种大语言模型集成（如 GLM、Ollama、DeepSeek 等）。系统采用模块化设计，支持增量更新和版本控制，为开发团队提供了全面的代码理解和文档管理解决方案。"
                logger.debug("Mocking project background summary response")
            elif "analyze code map and suggest module divisions" in user_message.lower():
                # Module division request - return invalid JSON to trigger fallback
                mock_response = "I need to analyze this codebase more carefully. Let me think about the module divisions..."
                logger.debug("Mocking module division response (will trigger fallback)")
            else:
                # Default mock response
                mock_response = f"This is a mock chat response generated in MOCK mode.\n\nThe LLM would normally analyze your message and generate a detailed response, but in mock mode, we're returning this simulated output.\n\nUser message: {user_message[:200]}...\n\nModel: {self.model}\nProvider: {self.provider.value}\nTemperature: {self.temperature}\n\n[MOCK CHAT RESPONSE END]"
            
            if stream:
                # Simulate streaming response
                def mock_generator():
                    chunks = mock_response.split(' ')
                    for i, chunk in enumerate(chunks):
                        yield chunk + (' ' if i < len(chunks) - 1 else '')
                
                return mock_generator()
            else:
                # Return full mock response
                logger.debug(f"Mock chat response: {mock_response}")
                return mock_response
        
        try:
            if stream:
                logger.debug("Sending streaming chat request")
                stream_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                
                def generator():
                    full_response = ""
                    for chunk in stream_response:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            yield chunk.choices[0].delta.content
                    logger.debug(f"Streaming chat response completed: {full_response[:500]}...")
                
                return generator()
            else:
                logger.debug("Sending non-streaming chat request")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                
                content = response.choices[0].message.content
                logger.debug(f"Chat response: {content}")
                logger.debug(f"Chat usage: Prompt tokens: {response.usage.prompt_tokens}, Completion tokens: {response.usage.completion_tokens}, Total tokens: {response.usage.total_tokens}")
                
                return content
                
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            logger.debug(f"Failed chat messages: {messages}")
            raise
    
    def _assemble_prompt(self, template: str, context: Dict) -> str:
        """Assemble prompt"""
        # Replace {{context}} with entire context JSON
        context_str = json.dumps(context, indent=2, default=str, ensure_ascii=False)
        prompt = template.replace("{{context}}", context_str)
        
        # Replace {{context.xxx}} placeholders with specific context values
        import re
        placeholders = re.findall(r'\{\{context\.(\w+)\}\}', prompt)
        for key in placeholders:
            placeholder = f"{{{{context.{key}}}}}"
            value = context.get(key, "")
            # Convert dict values to string
            if isinstance(value, dict):
                value = json.dumps(value, indent=2, default=str, ensure_ascii=False)
            # Convert list values to string
            elif isinstance(value, list):
                value = "\n".join(str(item) for item in value)
            prompt = prompt.replace(placeholder, str(value))
        
        return prompt
    
    def _clean_markdown(self, content: str) -> str:
        """Clean LLM output markdown format"""
        lines = content.split('\n')
        if lines and lines[0].strip().startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        return '\n'.join(lines).strip()


class PromptTemplates:
    """Prompt templates library"""
    
    OVERVIEW_TEMPLATE = """
基于以下代码库信息，生成项目概览文档（Markdown 格式）。

## 项目结构
```text
{{context.project_structure}}
```

## 统计信息
{{context.statistics}}

## 入口点
{{context.entry_points}}

## 配置文件
{{context.config_files}}

## 关键依赖
{{context.dependencies}}

请生成包含以下章节的项目概览文档：
1. 项目简介（1-2段话描述项目目标和定位）
2. 技术栈（列出主要技术、框架、版本）
3. 项目结构说明（解释主要目录和模块的职责）
4. 核心功能（列出主要功能模块）
5. 快速开始（安装、配置、运行步骤）
6. 架构特点（简要说明架构设计亮点）

要求：
- 使用中文撰写
- 技术术语保留英文
- 使用 Markdown 格式
- 适当使用列表和表格增强可读性
"""
    
    MODULE_TEMPLATE = """
基于以下模块信息，生成模块文档（Markdown 格式）。

## 模块信息
{{context.module_info}}

## 类定义
{{context.classes}}

## 函数定义
{{context.functions}}

## 依赖关系
{{context.dependencies}}

请生成包含以下章节的模块文档：
1. 模块概述（职责、定位、设计意图）
2. 主要类说明（每个类的职责、关键方法）
3. 函数清单（重要函数的用途和参数）
4. 使用示例（伪代码或简短示例）
5. 依赖说明（依赖哪些模块，被谁依赖）

要求：
- 使用中文撰写
- 代码保留原样
- 重点解释设计意图，而非重复代码
"""
    
    ARCHITECTURE_TEMPLATE = """
基于以下架构分析数据，生成架构设计文档。

## 依赖图摘要
{{context.dependency_graph}}

## 关键组件
{{context.key_components}}

## 架构分层
{{context.layers}}

## 设计模式
{{context.design_patterns}}

请生成包含以下章节的架构文档：
1. 架构概览（整体架构图描述，使用 Mermaid 语法）
2. 系统分层（各层的职责和交互）
3. 核心组件（关键类的职责和协作关系）
4. 数据流（主要业务流程的数据流转）
5. 设计决策（重要的架构选择和理由）

要求：
- 包含 Mermaid 图表（flowchart 或 classDiagram）
- 解释为什么选择当前架构
- 指出潜在的扩展点
"""
