from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class ChatBackend(ABC):
    """聊天后端抽象基类"""
    
    @abstractmethod
    def generate_response(self, query: str, context: Optional[Dict] = None) -> str:
        """生成响应
        
        Args:
            query: 用户查询
            context: 上下文信息
        
        Returns:
            生成的响应
        """
        pass
    
    @abstractmethod
    def get_sources(self) -> List[Dict[str, Any]]:
        """获取引用的来源
        
        Returns:
            来源列表
        """
        pass


class RAGBackend(ABC):
    """RAG后端抽象基类"""
    
    @abstractmethod
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """检索相关文档
        
        Args:
            query: 查询文本
            k: 返回结果数量
        
        Returns:
            相关文档列表
        """
        pass
    
    @abstractmethod
    def generate(self, query: str, context: List[Dict[str, Any]]) -> str:
        """生成回答
        
        Args:
            query: 查询文本
            context: 检索到的上下文
        
        Returns:
            生成的回答
        """
        pass
    
    @abstractmethod
    def rag(self, query: str, k: int = 5) -> Dict[str, Any]:
        """执行RAG流程
        
        Args:
            query: 查询文本
            k: 返回结果数量
        
        Returns:
            包含回答和来源的字典
        """
        pass