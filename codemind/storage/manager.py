from typing import Optional
from codemind.storage.base import StorageBackend
from codemind.storage.memory import MemoryStorage
from codemind.storage.file import FileStorage
from codemind.storage.chroma import ChromaStorage


class StorageManager:
    """存储管理器"""
    
    def __init__(self, storage_dir: str = ".codemind"):
        """初始化存储管理器
        
        Args:
            storage_dir: 存储目录路径
        """
        self.storage_dir = storage_dir
        self.memory_storage = MemoryStorage()
        self.file_storage = FileStorage(storage_dir)
        self.chroma_storage = ChromaStorage(persist_dir=f"{storage_dir}/chroma")
    
    @property
    def storage_path(self):
        """存储路径"""
        return self.storage_dir
    
    def get_memory_storage(self) -> MemoryStorage:
        """获取内存存储后端"""
        return self.memory_storage
    
    def get_file_storage(self) -> FileStorage:
        """获取文件存储后端"""
        return self.file_storage
    
    def get_chroma_storage(self) -> ChromaStorage:
        """获取ChromaDB存储后端"""
        return self.chroma_storage
    
    def save_all(self, symbols, chunks):
        """保存所有数据到所有存储后端"""
        # 保存到内存
        self.memory_storage.save_symbols(symbols)
        self.memory_storage.save_chunks(chunks)
        
        # 保存到文件
        self.file_storage.save_symbols(symbols)
        self.file_storage.save_chunks(chunks)
        
        # 保存到ChromaDB
        self.chroma_storage.add_chunks(chunks)
    
    def load_from_file(self):
        """从文件加载数据到内存"""
        symbols = self.file_storage.get_symbols()
        chunks = self.file_storage.get_chunks()
        
        self.memory_storage.save_symbols(symbols)
        self.memory_storage.save_chunks(chunks)
        
        return symbols, chunks
    
    def clear_all(self):
        """清空所有存储"""
        self.memory_storage.clear()
        self.file_storage.clear()
        self.chroma_storage.clear()