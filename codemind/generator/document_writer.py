import json
import logging
from pathlib import Path
from typing import List
from codemind.parser.models.document import Document, DocumentSection, DocType

logger = logging.getLogger(__name__)


class DocumentWriter:
    """Manage document writing and updating"""
    
    def __init__(self, wiki_path: str):
        self.wiki_path = Path(wiki_path)
        self.wiki_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.wiki_path / "modules").mkdir(exist_ok=True)
        (self.wiki_path / "api").mkdir(exist_ok=True)
        (self.wiki_path / "assets").mkdir(exist_ok=True)
    
    def write_document(self, doc: Document):
        """Write single document"""
        logger.info(f"Writing document: {doc.file_path}")
        logger.info(f"Document type: {doc.doc_type.value}")
        logger.info(f"Document title: {doc.title}")
        
        file_path = self.wiki_path / doc.file_path
        logger.info(f"Full file path: {file_path}")
        
        # Ensure directory exists
        logger.info(f"Ensuring directory exists: {file_path.parent}")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        content = doc.to_markdown()
        logger.info(f"Content length: {len(content)} characters")
        logger.debug(f"Content preview: {content[:500]}...")
        
        file_path.write_text(content, encoding='utf-8')
        logger.info(f"✓ Document written successfully: {doc.file_path}")
        
        # Update index
        logger.info(f"Updating document index for: {doc.file_path}")
        self._update_index(doc)
        logger.info(f"✓ Index updated successfully")
    
    def write_documents(self, docs: List[Document]):
        """Batch write documents"""
        logger.info(f"=== Batch writing {len(docs)} documents ===")
        
        for doc in docs:
            self.write_document(doc)
        
        # Generate navigation file
        logger.info("Generating navigation files...")
        self._generate_nav_file(docs)
        logger.info("✓ Navigation files generated successfully")
        
        # Generate README.md
        logger.info("Generating Wiki README.md...")
        readme_content = self._generate_readme(docs)
        readme_path = self.wiki_path / "README.md"
        readme_path.write_text(readme_content, encoding='utf-8')
        logger.info(f"✓ README.md written: {readme_path}")
        
        logger.info(f"=== All {len(docs)} documents written successfully ===")
    
    def _update_index(self, doc: Document):
        """Update document index (for quick lookup)"""
        index_file = self.wiki_path / ".index.json"
        
        index = {}
        if index_file.exists():
            index = json.loads(index_file.read_text())
        
        index[doc.file_path] = {
            "title": doc.title,
            "type": doc.doc_type.value,
            "updated_at": doc.updated_at.isoformat(),
            "symbols": doc.source_symbols
        }
        
        index_file.write_text(json.dumps(index, indent=2))
    
    def _generate_nav_file(self, docs: List[Document]):
        """Generate navigation file (_sidebar.md or README)"""
        # Group by type
        groups = {}
        for doc in docs:
            groups.setdefault(doc.doc_type.value, []).append(doc)
        
        lines = ["# 文档导航\n"]
        
        # Overview and architecture first
        for doc_type in ['overview', 'architecture', 'module', 'api']:
            if doc_type in groups:
                type_name = {
                    'overview': '项目概览',
                    'architecture': '架构设计',
                    'module': '模块文档',
                    'api': 'API 文档'
                }.get(doc_type, doc_type)
                
                lines.append(f"## {type_name}")
                for doc in sorted(groups[doc_type], key=lambda d: d.file_path):
                    lines.append(f"- [{doc.title}]({doc.file_path})")
                lines.append("")
        
        nav_content = "\n".join(lines)
        (self.wiki_path / "_sidebar.md").write_text(nav_content, encoding='utf-8')
        
        # Also update homepage README
        readme_content = self._generate_readme(docs)
        (self.wiki_path / "README.md").write_text(readme_content, encoding='utf-8')
    
    def _generate_readme(self, docs: List[Document]) -> str:
        """Generate Wiki homepage"""
        lines = [
            "# CodeMind 生成的项目文档",
            "",
            "> 本文档由 CodeMind 自动生成，基于代码静态分析。",
            "> 最后更新：" + docs[0].updated_at.strftime("%Y-%m-%d %H:%M") if docs else "",
            "",
            "## 快速导航",
            "",
            "- [项目概览](00-overview.md)",
            "- [架构设计](01-architecture.md)",
            "- [模块文档](./modules/)",
            "",
            "## 使用说明",
            "",
            "本文档包含以下类型的内容：",
            "- **项目概览**：项目目标、技术栈、快速开始",
            "- **架构设计**：系统架构、核心流程、设计决策",
            "- **模块文档**：各模块的详细说明",
            "",
            "---",
            "",
            "*Generated by CodeMind*"
        ]
        
        return "\n".join(lines)
    
    def clean(self):
        """Clean all generated documents"""
        import shutil
        if self.wiki_path.exists():
            shutil.rmtree(self.wiki_path)
            self.wiki_path.mkdir(parents=True, exist_ok=True)
