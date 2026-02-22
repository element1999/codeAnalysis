from typing import List, Optional, Dict, Any
import os
from openai import OpenAI
from codemind.generator.base import DocumentationGenerator
from codemind.parser.models.symbol import Symbol, FunctionSymbol, ClassSymbol
from codemind.parser.models.chunk import CodeChunk
from codemind.config.schemas import LLMConfig, LLMProvider
from codemind.core.logger import logger


class LLMGenerator(DocumentationGenerator):
    """基于LLM的文档生成器"""
    
    def __init__(self, config: LLMConfig):
        """初始化LLM生成器
        
        Args:
            config: LLM配置
        """
        self.config = config
        self.client = self._create_client()
    
    def _create_client(self) -> OpenAI:
        """创建OpenAI客户端
        
        Returns:
            OpenAI客户端实例
        """
        if self.config.provider == LLMProvider.OLLAMA:
            return OpenAI(
                base_url=self.config.base_url,
                api_key="ollama"  # Ollama不需要真实API密钥
            )
        elif self.config.provider == LLMProvider.DEEPSEEK:
            return OpenAI(
                base_url=self.config.base_url,
                api_key=self.config.api_key
            )
        elif self.config.provider == LLMProvider.GLM:
            return OpenAI(
                base_url=self.config.base_url,
                api_key=self.config.api_key
            )
        elif self.config.provider == LLMProvider.KIMI:
            return OpenAI(
                base_url=self.config.base_url,
                api_key=self.config.api_key
            )
        elif self.config.provider == LLMProvider.OPENAI:
            return OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )
        else:
            # 默认使用Ollama
            return OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama"
            )
    
    def generate(self, prompt: str, **kwargs) -> str:
        """生成内容
        
        Args:
            prompt: 提示词
            **kwargs: 额外参数
        
        Returns:
            生成的内容
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的代码文档生成助手，擅长分析代码并生成清晰、准确的文档。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to generate content: {e}")
            return f"Error generating content: {e}"
    
    def generate_symbol_docs(self, symbol: Symbol) -> str:
        """为符号生成文档"""
        if isinstance(symbol, FunctionSymbol):
            return self._generate_function_docs(symbol)
        elif isinstance(symbol, ClassSymbol):
            return self._generate_class_docs(symbol)
        else:
            return self._generate_generic_docs(symbol)
    
    def _generate_function_docs(self, symbol: FunctionSymbol) -> str:
        """为函数生成文档"""
        prompt = f"""请为以下函数生成详细的文档：

函数名：{symbol.name}
文件路径：{symbol.file_path}
行号：{symbol.line_start}-{symbol.line_end}

函数代码：
```python
{symbol.source_code}
```

请生成包含以下内容的Markdown文档：
1. 函数说明
2. 参数说明
3. 返回值说明
4. 函数功能
5. 代码示例（如果适用）
6. 注意事项（如果有）

文档语言：中文
"""
        return self.generate(prompt)
    
    def _generate_class_docs(self, symbol: ClassSymbol) -> str:
        """为类生成文档"""
        prompt = f"""请为以下类生成详细的文档：

类名：{symbol.name}
文件路径：{symbol.file_path}
行号：{symbol.line_start}-{symbol.line_end}
父类：{', '.join(symbol.bases) if symbol.bases else '无'}

类代码：
```python
{symbol.source_code}
```

请生成包含以下内容的Markdown文档：
1. 类说明
2. 继承关系
3. 主要方法
4. 主要属性
5. 类的作用
6. 使用示例
7. 注意事项（如果有）

文档语言：中文
"""
        return self.generate(prompt)
    
    def _generate_generic_docs(self, symbol: Symbol) -> str:
        """为通用符号生成文档"""
        prompt = f"""请为以下代码元素生成详细的文档：

名称：{symbol.name}
类型：{symbol.type.value}
文件路径：{symbol.file_path}
行号：{symbol.line_start}-{symbol.line_end}

代码：
```python
{symbol.source_code}
```

请生成包含以下内容的Markdown文档：
1. 元素说明
2. 功能描述
3. 使用方法（如果适用）
4. 注意事项（如果有）

文档语言：中文
"""
        return self.generate(prompt)
    
    def generate_chunk_docs(self, chunk: CodeChunk) -> str:
        """为代码块生成文档"""
        prompt = f"""请为以下代码块生成详细的文档：

代码块类型：{chunk.chunk_type}

代码：
```python
{chunk.content}
```

请生成包含以下内容的Markdown文档：
1. 代码块说明
2. 功能描述
3. 关键逻辑分析
4. 使用方法（如果适用）
5. 注意事项（如果有）

文档语言：中文
"""
        return self.generate(prompt)
    
    def generate_summary(self, symbols: List[Symbol], chunks: List[CodeChunk]) -> str:
        """生成项目摘要"""
        # 统计信息
        function_count = sum(1 for s in symbols if isinstance(s, FunctionSymbol))
        class_count = sum(1 for s in symbols if isinstance(s, ClassSymbol))
        total_symbols = len(symbols)
        total_chunks = len(chunks)
        
        # 获取主要符号
        main_symbols = []
        for symbol in symbols:
            if isinstance(symbol, (FunctionSymbol, ClassSymbol)):
                main_symbols.append({
                    "name": symbol.name,
                    "type": symbol.type.value,
                    "file_path": symbol.file_path
                })
        
        prompt = f"""请为以下项目生成详细的项目摘要：

项目统计信息：
- 总符号数：{total_symbols}
- 函数数量：{function_count}
- 类数量：{class_count}
- 代码块数量：{total_chunks}

主要符号：
{main_symbols[:10]}

请生成包含以下内容的Markdown文档：
1. 项目概述
2. 目录结构
3. 核心功能模块
4. 主要API/类/函数
5. 技术栈
6. 使用指南
7. 项目亮点

文档语言：中文
"""
        return self.generate(prompt)