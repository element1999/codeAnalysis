from typing import List, Optional, Dict, Any
from openai import OpenAI
from codemind.chat.base import RAGBackend
from codemind.storage.chroma import ChromaStorage
from codemind.embedding.manager import EmbeddingManager
from codemind.config.schemas import LLMConfig
from codemind.core.logger import logger


class ChromaRAGBackend(RAGBackend):
    """基于ChromaDB的RAG后端"""
    
    def __init__(self, chroma_storage: ChromaStorage,
                 llm_config: LLMConfig,
                 embedding_manager: EmbeddingManager):
        """初始化RAG后端
        
        Args:
            chroma_storage: ChromaDB存储
            llm_config: LLM配置
            embedding_manager: 嵌入管理器
        """
        self.chroma_storage = chroma_storage
        self.llm_config = llm_config
        self.embedding_manager = embedding_manager
        self.client = self._create_client()
        self._sources = []
    
    def _create_client(self) -> OpenAI:
        """创建OpenAI客户端"""
        if self.llm_config.base_url:
            return OpenAI(
                base_url=self.llm_config.base_url,
                api_key=self.llm_config.api_key or "ollama"
            )
        else:
            return OpenAI(api_key=self.llm_config.api_key)
    
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """检索相关文档"""
        try:
            results = self.chroma_storage.search_similar(query, n_results=k)
            self._sources = results
            return results
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}")
            return []
    
    def generate(self, query: str, context: List[Dict[str, Any]]) -> str:
        """生成回答"""
        # 构建上下文
        context_text = ""
        for i, item in enumerate(context):
            context_text += f"""## 参考资料 {i+1}

{item['document']}

"""
        
        # 构建提示词
        prompt = f"""请根据以下参考资料回答用户的问题。如果参考资料中没有相关信息，请基于你的知识回答，但要明确说明信息来源。

## 用户问题
{query}

## 参考资料
{context_text}

请生成详细、准确的回答，并在回答末尾列出使用的参考资料编号。
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.llm_config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的代码分析助手，擅长基于提供的代码和文档回答问题。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.llm_config.temperature,
                max_tokens=self.llm_config.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return f"Error generating response: {e}"
    
    def rag(self, query: str, k: int = 5) -> Dict[str, Any]:
        """执行RAG流程"""
        # 检索相关文档
        context = self.retrieve(query, k)
        
        # 生成回答
        answer = self.generate(query, context)
        
        return {
            "answer": answer,
            "sources": self._sources
        }
    
    def get_sources(self) -> List[Dict[str, Any]]:
        """获取引用的来源"""
        return self._sources