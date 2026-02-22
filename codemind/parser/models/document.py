"""Document models"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DocType(str, Enum):
    """Document type enum"""
    OVERVIEW = "overview"           # 项目概览
    ARCHITECTURE = "architecture"   # 架构分析
    MODULE = "module"               # 模块文档
    API = "api"                     # API 文档
    GUIDE = "guide"                 # 使用指南


class DocumentSection(BaseModel):
    """Document section"""
    title: str
    level: int                      # 标题级别（1-6）
    content: str                    # Markdown 内容
    order: int                      # 排序
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Document(BaseModel):
    """Document object"""
    id: str
    doc_type: DocType
    title: str
    file_path: str                  # 相对 wiki/ 目录的路径
    sections: List[DocumentSection] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    source_symbols: List[str] = []  # 基于哪些符号生成
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_markdown(self) -> str:
        """Convert to Markdown text"""
        lines = [f"# {self.title}\n"]
        
        for section in sorted(self.sections, key=lambda s: s.order):
            prefix = "#" * section.level
            lines.append(f"{prefix} {section.title}\n")
            lines.append(section.content)
            lines.append("")  # 空行
        
        return "\n".join(lines)


class WikiStructure(BaseModel):
    """Wiki structure definition"""
    project_name: str
    documents: List[Document] = []
    nav_order: List[str] = []       # 导航顺序
    
    def get_nav_tree(self) -> Dict:
        """Generate navigation tree"""
        tree = {}
        for doc in self.documents:
            parts = doc.file_path.split('/')
            current = tree
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {"_docs": []}
                current = current[part]
            current.setdefault("_docs", []).append({
                "title": doc.title,
                "path": doc.file_path,
                "type": doc.doc_type.value
            })
        return tree
