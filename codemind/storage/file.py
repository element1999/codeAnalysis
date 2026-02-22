import json
import os
from typing import Dict, List, Optional
from codemind.storage.base import StorageBackend
from codemind.parser.models.symbol import Symbol
from codemind.parser.models.chunk import CodeChunk


class FileStorage(StorageBackend):
    """文件存储后端"""
    
    def __init__(self, storage_dir: str = ".codemind"):
        """初始化文件存储
        
        Args:
            storage_dir: 存储目录路径
        """
        self.storage_dir = storage_dir
        self.symbols_file = os.path.join(storage_dir, "symbols.json")
        self.chunks_file = os.path.join(storage_dir, "chunks.json")
        
        # 创建存储目录
        os.makedirs(storage_dir, exist_ok=True)
    
    def save_symbols(self, symbols: List[Symbol]) -> None:
        """保存符号列表到文件"""
        symbols_data = [symbol.model_dump() for symbol in symbols]
        with open(self.symbols_file, 'w', encoding='utf-8') as f:
            json.dump(symbols_data, f, ensure_ascii=False, indent=2)
    
    def get_symbols(self) -> List[Symbol]:
        """从文件读取符号列表"""
        if not os.path.exists(self.symbols_file):
            return []
        
        with open(self.symbols_file, 'r', encoding='utf-8') as f:
            symbols_data = json.load(f)
        
        return [Symbol(**data) for data in symbols_data]
    
    def get_symbol_by_id(self, symbol_id: str) -> Optional[Symbol]:
        """根据ID获取符号"""
        symbols = self.get_symbols()
        for symbol in symbols:
            if symbol.id == symbol_id:
                return symbol
        return None
    
    def save_chunks(self, chunks: List[CodeChunk]) -> None:
        """保存代码块列表到文件"""
        chunks_data = [chunk.model_dump() for chunk in chunks]
        with open(self.chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)
    
    def get_chunks(self) -> List[CodeChunk]:
        """从文件读取代码块列表"""
        if not os.path.exists(self.chunks_file):
            return []
        
        with open(self.chunks_file, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
        
        return [CodeChunk(**data) for data in chunks_data]
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[CodeChunk]:
        """根据ID获取代码块"""
        chunks = self.get_chunks()
        for chunk in chunks:
            if chunk.id == chunk_id:
                return chunk
        return None
    
    def clear(self) -> None:
        """清空存储"""
        if os.path.exists(self.symbols_file):
            os.remove(self.symbols_file)
        if os.path.exists(self.chunks_file):
            os.remove(self.chunks_file)