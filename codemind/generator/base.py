from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from codemind.parser.models.symbol import Symbol
from codemind.parser.models.chunk import CodeChunk


class Generator(ABC):
    """生成器抽象基类"""
    
    @abstractmethod
    def generate(self, *args, **kwargs) -> Any:
        """生成内容"""
        pass


class DocumentationGenerator(Generator):
    """文档生成器抽象基类"""
    
    @abstractmethod
    def generate_symbol_docs(self, symbol: Symbol) -> str:
        """为符号生成文档
        
        Args:
            symbol: 符号对象
        
        Returns:
            生成的文档内容
        """
        pass
    
    @abstractmethod
    def generate_chunk_docs(self, chunk: CodeChunk) -> str:
        """为代码块生成文档
        
        Args:
            chunk: 代码块对象
        
        Returns:
            生成的文档内容
        """
        pass
    
    @abstractmethod
    def generate_summary(self, symbols: List[Symbol], chunks: List[CodeChunk]) -> str:
        """生成项目摘要
        
        Args:
            symbols: 符号列表
            chunks: 代码块列表
        
        Returns:
            生成的摘要内容
        """
        pass