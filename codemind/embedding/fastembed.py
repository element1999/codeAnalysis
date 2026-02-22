from typing import List, Optional
from fastembed import TextEmbedding
from codemind.embedding.base import EmbeddingBackend
from codemind.core.logger import logger


class FastEmbedBackend(EmbeddingBackend):
    """FastEmbed嵌入后端"""
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """初始化FastEmbed后端
        
        Args:
            model_name: 模型名称
        """
        self._model_name = model_name
        self._model = None
        self._dimension = None
        self._initialize_model()
    
    def _initialize_model(self):
        """初始化模型"""
        try:
            logger.info(f"Initializing FastEmbed model: {self._model_name}")
            self._model = TextEmbedding(model_name=self._model_name)
            
            # 获取嵌入维度
            test_embedding = self.embed_query("test")
            self._dimension = len(test_embedding)
            logger.info(f"FastEmbed model initialized with dimension: {self._dimension}")
        except Exception as e:
            logger.error(f"Failed to initialize FastEmbed model: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """为文本列表生成嵌入向量"""
        if not self._model:
            self._initialize_model()
        
        try:
            embeddings = list(self._model.embed(texts))
            return embeddings
        except Exception as e:
            logger.error(f"Failed to embed texts: {e}")
            raise
    
    def embed_query(self, query: str) -> List[float]:
        """为查询文本生成嵌入向量"""
        if not self._model:
            self._initialize_model()
        
        try:
            embedding = list(self._model.embed([query]))[0]
            return embedding
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise
    
    @property
    def dimension(self) -> int:
        """嵌入维度"""
        if self._dimension is None:
            self._initialize_model()
        return self._dimension
    
    @property
    def model_name(self) -> str:
        """模型名称"""
        return self._model_name