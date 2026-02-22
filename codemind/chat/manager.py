from typing import List, Optional, Dict, Any
from codemind.chat.rag import ChromaRAGBackend
from codemind.storage.chroma import ChromaStorage
from codemind.embedding.manager import EmbeddingManager
from codemind.config.schemas import LLMConfig, EmbeddingConfig
from codemind.core.logger import logger


class ChatManager:
    """聊天管理器"""
    
    def __init__(self, llm_config: LLMConfig,
                 embedding_config: EmbeddingConfig):
        """初始化聊天管理器
        
        Args:
            llm_config: LLM配置
            embedding_config: 嵌入配置
        """
        self.llm_config = llm_config
        self.embedding_config = embedding_config
        self.chroma_storage = ChromaStorage()
        self.embedding_manager = EmbeddingManager(embedding_config)
        self.rag_backend = ChromaRAGBackend(
            self.chroma_storage,
            self.llm_config,
            self.embedding_manager
        )
        self.conversation_history: List[Dict[str, str]] = []
    
    def chat(self, query: str, k: int = 5) -> Dict[str, Any]:
        """执行聊天
        
        Args:
            query: 用户查询
            k: 检索结果数量
        
        Returns:
            包含回答和来源的字典
        """
        try:
            # 执行RAG流程
            result = self.rag_backend.rag(query, k=k)
            
            # 添加到对话历史
            self.conversation_history.append({
                "role": "user",
                "content": query
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": result["answer"]
            })
            
            return result
        except Exception as e:
            logger.error(f"Failed to chat: {e}")
            return {
                "answer": f"Error: {e}",
                "sources": []
            }
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史
        
        Returns:
            对话历史
        """
        return self.conversation_history
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history.clear()
    
    def generate_with_history(self, query: str, k: int = 5) -> Dict[str, Any]:
        """使用历史对话生成回答
        
        Args:
            query: 用户查询
            k: 检索结果数量
        
        Returns:
            包含回答和来源的字典
        """
        # 构建对话历史上下文
        history_context = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self.conversation_history[-5:]  # 只使用最近5条消息
        ])
        
        # 构建增强查询
        enhanced_query = f"""根据以下对话历史和最新问题，生成一个综合查询：

{history_context}

最新问题：{query}

请生成一个能够体现对话上下文的综合查询。
"""
        
        # 执行RAG流程
        return self.chat(enhanced_query, k=k)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息
        """
        chroma_stats = self.chroma_storage.get_stats()
        return {
            "conversation_history_length": len(self.conversation_history),
            "chroma_db_count": chroma_stats.get("count", 0),
            "model_name": self.llm_config.model
        }