from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class EmbeddingBackend(ABC):
    """嵌入后端抽象基类"""
    
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """为文本列表生成嵌入向量
        
        Args:
            texts: 文本列表
        
        Returns:
            嵌入向量列表
        """
        pass
    
    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """为查询文本生成嵌入向量
        
        Args:
            query: 查询文本
        
        Returns:
            嵌入向量
        """
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """嵌入维度"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """模型名称"""
        pass