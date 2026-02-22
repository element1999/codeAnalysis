"""Document generator module"""

import json
from typing import List, Dict, Optional
from pathlib import Path
import logging

from codemind.parser.models.symbol import Symbol, SymbolType
from codemind.parser.models.document import Document, DocumentSection, DocType
from codemind.generator.context_assembler import ContextAssembler
from codemind.generator.llm_agent import LLMAgent, PromptTemplates
from codemind.generator.mermaid_generator import MermaidGenerator
from codemind.generator.document_writer import DocumentWriter

logger = logging.getLogger(__name__)


class DocumentGenerator:
    """Main document generator class"""
    
    def __init__(self, project_path: str, storage_path: str, llm_config: Dict):
        self.project_path = Path(project_path)
        self.storage_path = Path(storage_path)
        self.wiki_path = self.storage_path / "wiki"
        
        # Load parsing results
        self.symbols = self._load_symbols()
        self.dependencies = self._load_dependencies()
        
        # Initialize components
        self.context_assembler = ContextAssembler(self.symbols, self.dependencies)
        self.llm_agent = LLMAgent(llm_config)
        self.mermaid = MermaidGenerator()
        self.writer = DocumentWriter(str(self.wiki_path))
        self.templates = PromptTemplates()
        
    def generate_all(self) -> Dict:
        """
        Generate complete Wiki documentation
        
        Returns:
            Generation statistics
        """
        documents = []
        
        # 1. Generate project overview
        logger.info("=== Step 1: Generating project overview document ===")
        overview_doc = self._generate_overview()
        documents.append(overview_doc)
        logger.info(f"✓ Generated overview document: {overview_doc.file_path}")
        
        # 2. Generate architecture document
        logger.info("=== Step 2: Generating architecture document ===")
        arch_doc = self._generate_architecture()
        documents.append(arch_doc)
        logger.info(f"✓ Generated architecture document: {arch_doc.file_path}")
        
        # 3. Generate module documents (for each important module)
        logger.info("=== Step 3: Generating module documents ===")
        module_docs = self._generate_module_docs()
        documents.extend(module_docs)
        logger.info(f"✓ Generated {len(module_docs)} module documents")
        for doc in module_docs:
            logger.info(f"  - {doc.file_path}")
        
        # 4. Write all documents
        logger.info("=== Step 4: Writing documents to disk ===")
        self.writer.write_documents(documents)
        logger.info(f"✓ All documents written to: {self.wiki_path}")
        
        return {
            "total_documents": len(documents),
            "overview": overview_doc.file_path,
            "architecture": arch_doc.file_path,
            "modules": len(module_docs),
            "wiki_path": str(self.wiki_path)
        }
    
    def _generate_overview(self) -> Document:
        """Generate project overview document"""
        logger.info("Assembling context for overview document...")
        context = self.context_assembler.assemble_for_overview()
        logger.debug(f"Overview context assembled: {json.dumps(context, indent=2, ensure_ascii=False)[:1000]}...")
        
        logger.info("Calling LLM to generate overview document...")
        logger.info(f"Using template: OVERVIEW_TEMPLATE")
        logger.info(f"Provider: {self.llm_agent.provider.value}")
        logger.info(f"Model: {self.llm_agent.model}")
        
        content = self.llm_agent.generate_document(
            self.templates.OVERVIEW_TEMPLATE,
            context
        )
        
        logger.info(f"LLM response received, content length: {len(content)} characters")
        logger.debug(f"Generated content preview: {content[:500]}...")
        
        doc = Document(
            id="doc_overview",
            doc_type=DocType.OVERVIEW,
            title="项目概览",
            file_path="00-overview.md",
            sections=[
                DocumentSection(
                    title="项目概览",
                    level=1,
                    content=content,
                    order=0
                )
            ],
            source_symbols=[]  # Based on all symbols
        )
        
        logger.info(f"Overview document created: {doc.file_path}")
        return doc
    
    def _generate_architecture(self) -> Document:
        """Generate architecture document"""
        logger.info("Assembling context for architecture document...")
        context = self.context_assembler.assemble_for_architecture()
        logger.debug(f"Architecture context assembled: {json.dumps(context, indent=2, ensure_ascii=False)[:1000]}...")
        
        logger.info("Generating Mermaid diagrams...")
        class_diagram = self.mermaid.generate_class_diagram(self.symbols)
        dep_graph = self.mermaid.generate_dependency_graph(self.dependencies)
        logger.debug(f"Class diagram: {class_diagram}")
        logger.debug(f"Dependency graph: {dep_graph}")
        
        # Add diagrams to context
        context['class_diagram'] = class_diagram
        context['dependency_graph_mermaid'] = dep_graph
        
        logger.info("Calling LLM to generate architecture document...")
        logger.info(f"Using template: ARCHITECTURE_TEMPLATE")
        logger.info(f"Provider: {self.llm_agent.provider.value}")
        logger.info(f"Model: {self.llm_agent.model}")
        
        content = self.llm_agent.generate_document(
            self.templates.ARCHITECTURE_TEMPLATE,
            context
        )
        
        logger.info(f"LLM response received, content length: {len(content)} characters")
        logger.debug(f"Generated content preview: {content[:500]}...")
        
        # Insert diagrams into content
        full_content = f"{content}\n\n## 系统架构图\n\n```mermaid\n{class_diagram}\n```\n\n## 依赖关系图\n\n```mermaid\n{dep_graph}\n```"
        
        doc = Document(
            id="doc_architecture",
            doc_type=DocType.ARCHITECTURE,
            title="架构设计",
            file_path="01-architecture.md",
            sections=[
                DocumentSection(
                    title="架构设计",
                    level=1,
                    content=full_content,
                    order=0
                )
            ],
            source_symbols=[]
        )
        
        logger.info(f"Architecture document created: {doc.file_path}")
        return doc
    
    def _generate_module_docs(self) -> List[Document]:
        """Generate documents for important modules"""
        logger.info("Analyzing symbols to select important modules...")
        
        # Select important modules (files with较多 symbols)
        file_symbol_counts = {}
        for sym in self.symbols:
            if sym.type != SymbolType.MODULE:
                file_symbol_counts[sym.file_path] = file_symbol_counts.get(sym.file_path, 0) + 1
        
        logger.info(f"Found {len(file_symbol_counts)} files with symbols")
        for file_path, count in file_symbol_counts.items():
            logger.info(f"  - {file_path}: {count} symbols")
        
        # Sort and select top 10 most complex files
        important_files = sorted(
            file_symbol_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        logger.info(f"Selected {len(important_files)} important files for documentation")
        for file_path, count in important_files:
            logger.info(f"  - {file_path}: {count} symbols")
        
        documents = []
        for file_path, count in important_files:
            # Find module symbol
            logger.info(f"Processing module: {file_path}")
            module_sym = next(
                (s for s in self.symbols if s.file_path == file_path and s.type == SymbolType.MODULE),
                None
            )
            if not module_sym:
                logger.warning(f"No module symbol found for: {file_path}")
                continue
            
            try:
                doc = self._generate_single_module(module_sym)
                documents.append(doc)
                logger.info(f"✓ Generated module document: {doc.file_path}")
            except Exception as e:
                logger.error(f"Failed to generate doc for {file_path}: {e}")
        
        return documents
    
    def _generate_single_module(self, module_sym: Symbol) -> Document:
        """Generate document for single module"""
        logger.info(f"Assembling context for module: {module_sym.name}")
        context = self.context_assembler.assemble_for_module(module_sym)
        logger.debug(f"Module context assembled: {json.dumps(context, indent=2, ensure_ascii=False)[:1000]}...")
        
        logger.info(f"Calling LLM to generate module document: {module_sym.name}")
        logger.info(f"Using template: MODULE_TEMPLATE")
        logger.info(f"Provider: {self.llm_agent.provider.value}")
        logger.info(f"Model: {self.llm_agent.model}")
        
        content = self.llm_agent.generate_document(
            self.templates.MODULE_TEMPLATE,
            context
        )
        
        logger.info(f"LLM response received, content length: {len(content)} characters")
        logger.debug(f"Generated content preview: {content[:500]}...")
        
        # Generate file name
        safe_name = module_sym.file_path.replace('/', '_').replace('.py', '')
        file_name = f"modules/{safe_name}.md"
        
        doc = Document(
            id=f"doc_mod_{module_sym.id}",
            doc_type=DocType.MODULE,
            title=f"模块: {module_sym.name}",
            file_path=file_name,
            sections=[
                DocumentSection(
                    title=module_sym.name,
                    level=1,
                    content=content,
                    order=0
                )
            ],
            source_symbols=[module_sym.id] + [s.id for s in self.symbols if s.file_path == module_sym.file_path]
        )
        
        return doc
    
    def _load_symbols(self) -> List[Symbol]:
        """Load parsed symbols"""
        symbols_file = self.storage_path / "symbols.json"
        if not symbols_file.exists():
            raise FileNotFoundError("Symbols not found. Run parser first.")
        
        data = json.loads(symbols_file.read_text())
        return [Symbol(**s) for s in data]
    
    def _load_dependencies(self) -> Dict:
        """Load dependency graph"""
        # 暂时返回空依赖图，因为我们还没有实现依赖图的保存
        return {"nodes": [], "edges": []}
    
    def incremental_update(self, changed_files: List[str]):
        """
        Incrementally update documents for changed files
        
        Args:
            changed_files: List of changed file paths
        """
        # Find affected documents
        affected_docs = []
        for doc in self._list_existing_docs():
            if any(f in doc.source_symbols for f in changed_files):
                affected_docs.append(doc)
        
        # Regenerate affected module documents
        for file_path in changed_files:
            module_sym = next(
                (s for s in self.symbols if s.file_path == file_path and s.type == SymbolType.MODULE),
                None
            )
            if module_sym:
                new_doc = self._generate_single_module(module_sym)
                self.writer.write_document(new_doc)
                logger.info(f"Updated module doc: {file_path}")
        
        # If entry files changed, regenerate overview and architecture
        entry_files = {'main.py', 'app.py', '__init__.py'}
        if any(f in entry_files for f in changed_files):
            overview = self._generate_overview()
            self.writer.write_document(overview)
            
            arch = self._generate_architecture()
            self.writer.write_document(arch)
            logger.info("Updated overview and architecture")
    
    def _list_existing_docs(self) -> List[Document]:
        """List existing documents (for incremental update)"""
        # Simplified implementation: read from index
        index_file = self.wiki_path / ".index.json"
        if not index_file.exists():
            return []
        
        data = json.loads(index_file.read_text())
        docs = []
        for file_path, info in data.items():
            docs.append(Document(
                id=f"existing_{file_path}",
                doc_type=DocType(info['type']),
                title=info['title'],
                file_path=file_path,
                source_symbols=info.get('symbols', [])
            ))
        return docs


# Generator manager class
class GeneratorManager:
    """Generator manager for coordinating document generation"""
    
    def __init__(self, llm_config: Dict, generator_config: Dict = None):
        self.llm_config = llm_config
        self.generator_config = generator_config or {}
    
    def generate_docs(self, project_path: str, storage_path: str) -> Dict:
        """
        Generate documentation for project
        
        Args:
            project_path: Project root path
            storage_path: Storage path for parsed data
        
        Returns:
            Generation statistics
        """
        generator = DocumentGenerator(
            project_path=project_path,
            storage_path=storage_path,
            llm_config=self.llm_config
        )
        
        return generator.generate_all()
    
    def update_docs(self, project_path: str, storage_path: str, changed_files: List[str]) -> Dict:
        """
        Update documentation for changed files
        
        Args:
            project_path: Project root path
            storage_path: Storage path for parsed data
            changed_files: List of changed file paths
        
        Returns:
            Update statistics
        """
        generator = DocumentGenerator(
            project_path=project_path,
            storage_path=storage_path,
            llm_config=self.llm_config
        )
        
        generator.incremental_update(changed_files)
        return {"updated_files": len(changed_files)}
