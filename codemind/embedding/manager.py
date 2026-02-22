from typing import Optional, Dict, Any
from codemind.embedding.base import EmbeddingBackend
from codemind.embedding.fastembed import FastEmbedBackend
from codemind.config.schemas import EmbeddingConfig, EmbeddingProvider


class EmbeddingManager:
    """嵌入管理器"""
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """初始化嵌入管理器
        
        Args:
            config: 嵌入配置
        """
        self.config = config or EmbeddingConfig()
        self._backend: Optional[EmbeddingBackend] = None
    
    def get_backend(self) -> EmbeddingBackend:
        """获取嵌入后端
        
        Returns:
            嵌入后端实例
        """
        if not self._backend:
            self._backend = self._create_backend()
        return self._backend
    
    def _create_backend(self) -> EmbeddingBackend:
        """创建嵌入后端
        
        Returns:
            嵌入后端实例
        """
        if self.config.provider == EmbeddingProvider.FASTEMBED:
            return FastEmbedBackend(model_name=self.config.model)
        else:
            # 默认使用FastEmbed
            return FastEmbedBackend(model_name=self.config.model)
    
    def embed_texts(self, texts: list) -> list:
        """为文本列表生成嵌入向量
        
        Args:
            texts: 文本列表
        
        Returns:
            嵌入向量列表
        """
        backend = self.get_backend()
        return backend.embed_texts(texts)
    
    def embed_query(self, query: str) -> list:
        """为查询文本生成嵌入向量
        
        Args:
            query: 查询文本
        
        Returns:
            嵌入向量
        """
        backend = self.get_backend()
        return backend.embed_query(query)
    
    @property
    def dimension(self) -> int:
        """嵌入维度"""
        backend = self.get_backend()
        return backend.dimension
    
    @property
    def model_name(self) -> str:
        """模型名称"""
        backend = self.get_backend()
        return backend.model_name