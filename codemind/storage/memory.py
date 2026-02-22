from typing import Dict, List, Optional
from codemind.storage.base import StorageBackend
from codemind.parser.models.symbol import Symbol
from codemind.parser.models.chunk import CodeChunk


class MemoryStorage(StorageBackend):
    """内存存储后端"""
    
    def __init__(self):
        """初始化内存存储"""
        self.symbols: Dict[str, Symbol] = {}
        self.chunks: Dict[str, CodeChunk] = {}
    
    def save_symbols(self, symbols: List[Symbol]) -> None:
        """保存符号列表"""
        for symbol in symbols:
            self.symbols[symbol.id] = symbol
    
    def get_symbols(self) -> List[Symbol]:
        """获取所有符号"""
        return list(self.symbols.values())
    
    def get_symbol_by_id(self, symbol_id: str) -> Optional[Symbol]:
        """根据ID获取符号"""
        return self.symbols.get(symbol_id)
    
    def save_chunks(self, chunks: List[CodeChunk]) -> None:
        """保存代码块列表"""
        for chunk in chunks:
            self.chunks[chunk.id] = chunk
    
    def get_chunks(self) -> List[CodeChunk]:
        """获取所有代码块"""
        return list(self.chunks.values())
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[CodeChunk]:
        """根据ID获取代码块"""
        return self.chunks.get(chunk_id)
    
    def clear(self) -> None:
        """清空存储"""
        self.symbols.clear()
        self.chunks.clear()