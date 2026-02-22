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
        
        # Initialize client
        self.client = self._init_client()
    
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
        console.print(f"[green]Base URL:[/green] {self.client.base_url}")
        console.print(f"[green]Temperature:[/green] {self.temperature}")
        console.print(f"[green]Max Tokens:[/green] {self.max_tokens}")
        console.print(f"[green]Prompt length:[/green] {len(full_prompt)} characters")
        console.print()
        
        console.print("[bold cyan]System Prompt:[/bold cyan]")
        console.print("You are a technical documentation expert. Generate clear, structured Markdown documentation based on the provided code context.")
        console.print()
        
        console.print("[bold cyan]User Prompt (Preview):[/bold cyan]")
        console.print(f"{full_prompt[:1000]}...")
        console.print()
        
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
            
            content = response.choices[0].message.content
            content = self._clean_markdown(content)
            
            console.print("[bold cyan]Generated Content (Preview):[/bold cyan]")
            console.print(f"{content[:1000]}...")
            console.print()
            console.print(f"[green]✓ Content generated successfully! Total length: {len(content)} characters[/green]")
            console.print()
            
            return content
            
        except Exception as e:
            console.print(f"[red]✗ LLM generation failed: {e}[/red]")
            import traceback
            traceback.print_exc()
            raise
    
    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        """Stream generation (for chat command)"""
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
        """Assemble prompt"""
        context_str = json.dumps(context, indent=2, default=str, ensure_ascii=False)
        prompt = template.replace("{{context}}", context_str)
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
