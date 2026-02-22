from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings
from codemind.parser.models.chunk import CodeChunk


class ChromaStorage:
    """ChromaDB向量存储"""
    
    def __init__(self, collection_name: str = "codemind", persist_dir: str = ".codemind/chroma"):
        """初始化ChromaDB存储
        
        Args:
            collection_name: 集合名称
            persist_dir: 持久化目录
        """
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "CodeMind code chunks"}
        )
    
    def add_chunks(self, chunks: List[CodeChunk]) -> List[str]:
        """添加代码块到向量存储
        
        Args:
            chunks: 代码块列表
        
        Returns:
            添加成功的ID列表
        """
        if not chunks:
            return []
        
        ids = [chunk.id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = []
        
        for chunk in chunks:
            metadata = {
                "chunk_type": chunk.chunk_type
            }
            if hasattr(chunk, 'file_path'):
                metadata["file_path"] = chunk.file_path
            elif hasattr(chunk, 'context') and 'file_path' in chunk.context:
                metadata["file_path"] = chunk.context['file_path']
            if hasattr(chunk, 'start_line'):
                metadata["start_line"] = chunk.start_line
            if hasattr(chunk, 'end_line'):
                metadata["end_line"] = chunk.end_line
            if hasattr(chunk, 'language'):
                metadata["language"] = chunk.language
            metadatas.append(metadata)
        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        return ids
    
    def search_similar(self, query: str, n_results: int = 5, where: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """搜索相似的代码块
        
        Args:
            query: 搜索查询
            n_results: 返回结果数量
            where: 过滤条件
        
        Returns:
            相似代码块列表
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )
        
        # 格式化结果
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "score": results["distances"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i]
            })
        
        return formatted_results
    
    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取代码块
        
        Args:
            chunk_id: 代码块ID
        
        Returns:
            代码块信息
        """
        results = self.collection.get(ids=[chunk_id])
        if results["ids"]:
            return {
                "id": results["ids"][0],
                "document": results["documents"][0],
                "metadata": results["metadatas"][0]
            }
        return None
    
    def delete_chunk(self, chunk_id: str) -> None:
        """删除代码块
        
        Args:
            chunk_id: 代码块ID
        """
        self.collection.delete(ids=[chunk_id])
    
    def clear(self) -> None:
        """清空向量存储"""
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            metadata={"description": "CodeMind code chunks"}
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息
        
        Returns:
            统计信息
        """
        return {
            "count": self.collection.count(),
            "name": self.collection.name
        }