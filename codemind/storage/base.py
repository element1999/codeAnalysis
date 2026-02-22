from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from codemind.parser.models.symbol import Symbol
from codemind.parser.models.chunk import CodeChunk


class StorageBackend(ABC):
    """存储后端抽象基类"""
    
    @abstractmethod
    def save_symbols(self, symbols: List[Symbol]) -> None:
        """保存符号列表"""
        pass
    
    @abstractmethod
    def get_symbols(self) -> List[Symbol]:
        """获取所有符号"""
        pass
    
    @abstractmethod
    def get_symbol_by_id(self, symbol_id: str) -> Optional[Symbol]:
        """根据ID获取符号"""
        pass
    
    @abstractmethod
    def save_chunks(self, chunks: List[CodeChunk]) -> None:
        """保存代码块列表"""
        pass
    
    @abstractmethod
    def get_chunks(self) -> List[CodeChunk]:
        """获取所有代码块"""
        pass
    
    @abstractmethod
    def get_chunk_by_id(self, chunk_id: str) -> Optional[CodeChunk]:
        """根据ID获取代码块"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空存储"""
        pass