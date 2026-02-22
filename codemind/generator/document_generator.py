"""Document generator module"""

import json
from typing import List, Dict, Optional
from pathlib import Path
import logging
import os

from codemind.parser.models.symbol import Symbol, SymbolType
from codemind.parser.models.document import Document, DocumentSection, DocType
from codemind.generator.llm_agent import LLMAgent, PromptTemplates
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
        self.llm_agent = LLMAgent(llm_config)
        self.writer = DocumentWriter(str(self.wiki_path))
        self.templates = PromptTemplates()
        
    def generate_all(self) -> Dict:
        """
        Generate complete Wiki documentation

        Returns:
            Generation statistics
        """
        documents = []

        # 1. Generate code map first
        logger.info("=== Step 0: Generating code map ===")
        code_map = self._generate_code_map()
        logger.info(f"✓ Generated code map with {len(code_map['files'])} files")

        # 2. Get project background from README.md and other project files
        logger.info("=== Step 1: Getting project background from README.md ===")
        project_background = self._extract_project_background()
        logger.info("✓ Extracted project background information")
        logger.debug(f"Project background: {project_background[:500]}...")

        # 3. Ask LLM to analyze code map and suggest module divisions with project background
        logger.info("=== Step 2: Asking LLM to analyze code map and suggest module divisions ===")
        module_divisions = self._ask_llm_for_module_divisions(code_map, project_background)
        logger.info(f"✓ LLM suggested {len(module_divisions)} modules")
        for i, module in enumerate(module_divisions):
            logger.info(f"  Module {i+1}: {module['name']} - {len(module['files'])} files")

        # 4. Generate architecture document based on module divisions
        logger.info("=== Step 3: Generating architecture document ===")
        arch_doc = self._generate_architecture(code_map, module_divisions)
        documents.append(arch_doc)
        logger.info(f"✓ Generated architecture document: {arch_doc.file_path}")
        logger.debug(f"Architecture document details: {arch_doc}")

        # 5. Generate module documents (for each important module)
        logger.info("=== Step 4: Generating module documents ===")
        module_docs = self._generate_module_docs(code_map, module_divisions)
        documents.extend(module_docs)
        logger.info(f"✓ Generated {len(module_docs)} module documents")
        for doc in module_docs:
            logger.info(f"  - {doc.file_path}")
            logger.debug(f"Module document details: {doc}")

        # 6. Generate final project overview document based on all collected information
        logger.info("=== Step 5: Generating final project overview document ===")
        logger.debug(f"Project path: {self.project_path}")
        logger.debug(f"Storage path: {self.storage_path}")
        logger.debug(f"Wiki path: {self.wiki_path}")

        overview_doc = self._generate_overview(code_map, module_divisions, project_background, module_docs)
        documents.insert(0, overview_doc)  # Insert at beginning
        logger.info(f"✓ Generated overview document: {overview_doc.file_path}")
        logger.debug(f"Overview document details: {overview_doc}")

        # 7. Write all documents
        logger.info("=== Step 6: Writing documents to disk ===")
        logger.debug(f"Total documents to write: {len(documents)}")
        self.writer.write_documents(documents)
        logger.info(f"✓ All documents written to: {self.wiki_path}")

        result = {
            "total_documents": len(documents),
            "overview": overview_doc.file_path,
            "architecture": arch_doc.file_path,
            "modules": len(module_docs),
            "wiki_path": str(self.wiki_path)
        }

        logger.debug(f"Generation result: {result}")
        return result
    
    def _generate_overview(self, code_map: Dict, module_divisions: List[Dict], project_background: str, module_docs: List[Document]) -> Document:
        """Generate project overview document based on all collected information"""
        logger.info("Assembling context for final project overview document...")

        # Extract module information from module_docs
        module_infos = []
        for module_doc in module_docs:
            module_infos.append({
                "name": module_doc.title,
                "file_path": module_doc.file_path,
                "content_preview": module_doc.sections[0].content[:500] if module_doc.sections else ""
            })

        # Create context based on all collected information
        context = {
            "project_background": project_background,
            "project_structure": "\n".join(self._tree_to_string(code_map['file_tree'])),
            "statistics": code_map['statistics'],
            "module_divisions": module_divisions,
            "module_infos": module_infos,
            "entry_points": [],
            "config_files": [],
            "dependencies": []
        }

        logger.debug(f"Overview context assembled: {json.dumps(context, indent=2, ensure_ascii=False)[:1000]}...")

        logger.info("Calling LLM to generate final project overview document...")
        logger.info(f"Using template: OVERVIEW_TEMPLATE")
        logger.info(f"Provider: {self.llm_agent.provider.value}")
        logger.info(f"Model: {self.llm_agent.model}")

        # Create a custom prompt that includes all the collected information
        # Fix: Use chr(10) instead of \n in f-string
        tree_str = chr(10).join(self._tree_to_string(code_map['file_tree']))
        prompt = f"""
基于以下项目信息，生成详细的项目概览文档（Markdown 格式）。

## 项目背景
{project_background}

## 项目结构
```text
{tree_str}
```

## 统计信息
{json.dumps(code_map['statistics'], indent=2, ensure_ascii=False)}

## 模块划分
{json.dumps(module_divisions, indent=2, ensure_ascii=False)}

## 模块信息
{json.dumps(module_infos, indent=2, ensure_ascii=False)}

请生成包含以下章节的项目概览文档：
1. 项目简介（基于项目背景和模块分析，提供详细的项目目标和定位）
2. 技术栈（基于代码分析，列出主要技术、框架、版本）
3. 项目结构说明（基于模块划分，解释主要模块的职责）
4. 核心功能（基于模块分析，列出主要功能模块）
5. 快速开始（安装、配置、运行步骤）
6. 架构特点（基于模块依赖和架构分析，简要说明架构设计亮点）

要求：
- 使用中文撰写
- 技术术语保留英文
- 使用 Markdown 格式
- 适当使用列表和表格增强可读性
- 综合考虑项目背景、模块分析和代码结构，提供全面准确的项目概览
"""

        content = self.llm_agent.generate_document(
            prompt,
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
    
    def _generate_architecture(self, code_map: Dict, module_divisions: List[Dict]) -> Document:
        """Generate architecture document based on module divisions suggested by LLM"""
        logger.info("Assembling context for architecture document...")

        # Create context based on module divisions
        context = {
            "dependency_graph": {
                "module_dependencies": self._extract_module_dependencies(module_divisions),
                "total_symbols": len(self.symbols),
                "total_relations": len(self.dependencies.get('edges', []))
            },
            "key_components": self._extract_key_components_from_modules(module_divisions),
            "layers": self._extract_architecture_layers_from_modules(module_divisions),
            "design_patterns": self._identify_design_patterns(code_map),
            "class_diagram": "",
            "dependency_graph_mermaid": "",
            "project_statistics": code_map['statistics'],
            "module_divisions": module_divisions,
            "file_tree": self._tree_to_string(code_map['file_tree'])
        }

        logger.debug(f"Architecture context assembled: {json.dumps(context, indent=2, ensure_ascii=False)[:1000]}...")

        logger.info("Generating Mermaid diagrams...")
        # Generate architecture diagram based on module divisions
        arch_diagram = self._generate_module_architecture_diagram(module_divisions)
        logger.debug(f"Architecture diagram: {arch_diagram}")

        # Add diagram to context
        context['dependency_graph_mermaid'] = arch_diagram

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
        full_content = f"{content}\n\n## 系统架构图\n\n```mermaid\n{arch_diagram}\n```"

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
    
    def _generate_module_docs(self, code_map: Dict, module_divisions: List[Dict]) -> List[Document]:
        """Generate documents for modules based on LLM analysis of code map"""
        logger.info("=== Generating documents for suggested modules ===")
        documents = []
        for module in module_divisions:
            try:
                logger.debug(f"Generating document for module: {module['name']}")
                logger.debug(f"Module files: {module['files']}")

                module_doc = self._generate_module_doc_from_division(module)
                documents.append(module_doc)

                logger.info(f"✓ Generated module document: {module_doc.title} - {module_doc.file_path}")
                logger.debug(f"Module document details: {module_doc}")
            except Exception as e:
                logger.error(f"Failed to generate doc for module {module['name']}: {e}")
                logger.debug(f"Module details: {module}")

        logger.debug(f"Total modules generated: {len(documents)}")
        return documents
    
    def _generate_code_map(self) -> Dict:
        """Generate comprehensive code map based on file tree"""
        files = []
        file_tree = {}
        
        # Walk through project directory to build file tree
        for root, dirs, filenames in os.walk(self.project_path):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', '.venv']]
            
            for filename in filenames:
                if filename.endswith('.py'):
                    file_path = os.path.relpath(os.path.join(root, filename), self.project_path)
                    file_info = {
                        "path": file_path,
                        "name": filename,
                        "extension": ".py",
                        "size": os.path.getsize(os.path.join(root, filename)),
                        "directory": os.path.relpath(root, self.project_path)
                    }
                    files.append(file_info)
                    
                    # Build file tree structure
                    parts = file_path.split('/')
                    current = file_tree
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = None
        
        # Get symbol information for Python files
        python_files = [f for f in files if f['extension'] == '.py']
        
        return {
            "files": files,
            "file_tree": file_tree,
            "python_files": len(python_files),
            "total_files": len(files),
            "statistics": {
                "total_files": len(files),
                "python_files": len(python_files),
                "other_files": len(files) - len(python_files)
            }
        }
    
    def _tree_to_string(self, tree, prefix=""):
        """Convert file tree to string representation"""
        result = []
        for key, value in sorted(tree.items()):
            result.append(f"{prefix}{key}/")
            if isinstance(value, dict):
                result.extend(self._tree_to_string(value, prefix + "  "))
            elif value is None:
                result.append(f"{prefix}  {key}")
        return result
    
    def _generate_architecture_diagram(self, file_tree):
        """Generate simple architecture diagram based on file tree"""
        # Generate a simple flowchart based on directory structure
        nodes = []
        edges = []
        node_id = 0
        node_map = {}
        
        def traverse_tree(tree, parent_id=None):
            nonlocal node_id
            for key, value in sorted(tree.items()):
                current_id = f"node{node_id}"
                node_id += 1
                node_map[key] = current_id
                
                if isinstance(value, dict):
                    # Directory node
                    nodes.append(f"{current_id}[{key}]")
                    if parent_id:
                        edges.append(f"{parent_id} --> {current_id}")
                    traverse_tree(value, current_id)
                elif value is None:
                    # File node
                    nodes.append(f"{current_id}[{key}]")
                    if parent_id:
                        edges.append(f"{parent_id} --> {current_id}")
        
        traverse_tree(file_tree)
        
        # Build Mermaid diagram
        diagram = "flowchart TD\n"
        diagram += "\n".join([f"  {node}" for node in nodes]) + "\n"
        diagram += "\n".join([f"  {edge}" for edge in edges])
        
        return diagram
    
    def _ask_llm_for_module_divisions(self, code_map: Dict, project_background: str) -> List[Dict]:
        """Ask LLM to analyze code map and suggest module divisions with project background"""
        # Convert file tree to string representation
        file_tree_str = "\n".join(self._tree_to_string(code_map['file_tree']))
        
        prompt = f"""
You are a software architecture expert. Based on the following code map and project background, analyze the project structure and suggest logical module divisions.

## Project Background
{project_background}

## Project Overview
- Total files: {code_map['statistics']['total_files']}
- Python files: {code_map['statistics']['python_files']}
- Other files: {code_map['statistics']['other_files']}

## File Tree
{file_tree_str}

## Key Files
{chr(10).join([f"- {f['path']}" for f in code_map['files'][:20]])}

Please analyze this project structure and suggest logical module divisions based on:
1. Directory structure and organization
2. Functional cohesion
3. Architectural layers
4. Domain boundaries
5. Project background and purpose

For each suggested module, provide:
- Module name (descriptive and concise)
- Brief description of the module's purpose
- List of files that belong to this module
- Brief explanation of why these files belong together

Format your response as a JSON array with the following structure:
[
  {{
    "name": "Module Name",
    "description": "Brief description",
    "files": ["file1.py", "file2.py"],
    "reason": "Why these files belong together"
  }}
]

Limit the number of modules to a reasonable amount (3-8 modules).
"""
        
        # Use chat interface to get structured response
        try:
            response = self.llm_agent.chat([
                {"role": "system", "content": "You are a software architecture expert specializing in codebase analysis and module design."},
                {"role": "user", "content": prompt}
            ])
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\[\s*\{[\s\S]*\}\s*\]', response)
            if json_match:
                module_divisions = json.loads(json_match.group(0))
                return module_divisions
            else:
                logger.warning("LLM response did not contain valid JSON. Using fallback module division.")
                return self._get_fallback_module_divisions(code_map)
        except Exception as e:
            logger.error(f"Failed to get module divisions from LLM: {e}")
            return self._get_fallback_module_divisions(code_map)
    
    def _get_fallback_module_divisions(self, code_map: Dict) -> List[Dict]:
        """Fallback module division when LLM analysis fails"""
        # Group by directory structure as fallback
        directory_modules = {}
        for file_info in code_map['files']:
            directory = file_info['directory'] or 'root'
            if directory not in directory_modules:
                directory_modules[directory] = {
                    "name": directory.replace('/', '_').replace('-', '_'),
                    "description": f"Module for {directory} directory",
                    "files": [],
                    "reason": f"Files in {directory} directory"
                }
            directory_modules[directory]['files'].append(file_info['path'])
        
        return list(directory_modules.values())[:8]
    
    def _generate_module_doc_from_division(self, module: Dict) -> Document:
        """Generate module document from LLM-suggested division"""
        # 提取模块的结构化核心信息
        structured_info = self._extract_structured_module_info(module)
        
        # Create context for this module
        context = {
            "module_info": {
                "name": module['name'],
                "description": module['description'],
                "files": module['files']
            },
            "structured_info": structured_info,
            "reason": module.get('reason', '')
        }
        
        # Generate content using LLM
        content = self.llm_agent.generate_document(
            f"""
            基于以下模块的结构化核心信息，生成模块文档（Markdown 格式）。

            ## 模块信息
            名称: {module['name']}
            描述: {module['description']}
            包含文件: {', '.join(module['files'])}

            ## 模块划分理由
            {module.get('reason', '基于目录结构划分')}

            ## 结构化核心信息
            {json.dumps(structured_info, indent=2, ensure_ascii=False)}

            请生成包含以下章节的模块文档：
            1. 模块概述（职责、定位、设计意图）
            2. 包含文件（列出所有包含的文件及其作用）
            3. 核心功能（基于结构化信息，列出主要功能点）
            4. 关键组件（基于结构化信息，列出重要的类、函数）
            5. 使用方法（基于结构化信息，简要说明如何使用）
            6. 依赖关系（基于结构化信息，说明与其他模块的关系）

            要求：
            - 使用中文撰写
            - 技术术语保留英文
            - 使用 Markdown 格式
            - 适当使用列表和表格增强可读性
            - 基于提供的结构化信息生成文档，不要虚构信息
            """,
            context
        )
        
        # Generate file name
        safe_name = module['name'].replace(' ', '_').replace('/', '_').replace('-', '_')
        file_name = f"modules/{safe_name}.md"
        
        doc = Document(
            id=f"doc_mod_{safe_name}",
            doc_type=DocType.MODULE,
            title=f"模块: {module['name']}",
            file_path=file_name,
            sections=[
                DocumentSection(
                    title=module['name'],
                    level=1,
                    content=content,
                    order=0
                )
            ],
            source_symbols=[]
        )
        
        return doc
    
    def _load_symbols(self) -> List[Symbol]:
        """Load parsed symbols"""
        symbols_file = self.storage_path / "symbols.json"
        if not symbols_file.exists():
            logger.warning("Symbols not found. Returning empty list.")
            return []
        
        try:
            data = json.loads(symbols_file.read_text())
            return [Symbol(**s) for s in data]
        except Exception as e:
            logger.error(f"Failed to load symbols: {e}")
            return []
    
    def _load_dependencies(self) -> Dict:
        """Load dependency graph"""
        return {"nodes": [], "edges": []}

    def _extract_project_background(self) -> str:
        """Extract project background information from README.md and other project files"""
        project_background = ""
        
        # Check if README.md exists
        readme_path = self.project_path / "README.md"
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                project_background = f"# README.md Content\n\n{readme_content}\n\n"
                logger.info(f"Extracted project background from README.md")
            except Exception as e:
                logger.error(f"Failed to read README.md: {e}")
        else:
            logger.warning("README.md not found, using code structure as background")
        
        # If README.md doesn't exist or is empty, use code structure as background
        if not project_background.strip():
            code_map = self._generate_code_map()
            project_background = f"# Project Structure\n\n"
            project_background += f"## Total Files: {code_map['statistics']['total_files']}\n"
            project_background += f"## Python Files: {code_map['statistics']['python_files']}\n"
            project_background += f"## Other Files: {code_map['statistics']['other_files']}\n\n"
            project_background += "## File Tree\n"
            project_background += "\n".join(self._tree_to_string(code_map['file_tree']))
        
        # Ask LLM to summarize the project background
        try:
            summary_prompt = f"""
Please summarize the following project information into a concise project background (200-300 words). Focus on:
1. What is this project about?
2. What problem does it solve?
3. What are its main features?
4. What technology stack does it use?

Project Information:
{project_background[:3000]}...

Provide a clear, concise summary that captures the essence of the project.
"""
            
            summary = self.llm_agent.chat([
                {"role": "system", "content": "You are a technical documentation expert specializing in project analysis and summarization."},
                {"role": "user", "content": summary_prompt}
            ])
            
            logger.info("✓ Generated project background summary from LLM")
            return summary
        except Exception as e:
            logger.error(f"Failed to generate project background summary: {e}")
            # Return original background if LLM summarization fails
            return project_background[:1000]

    def _extract_structured_module_info(self, module: Dict) -> Dict:
        """Extract structured core information from module files using Tree-sitter"""
        from codemind.parser.tree_sitter_parser import TreeSitterParser
        from codemind.parser.symbol_extractor import SymbolExtractor
        from codemind.parser.models.symbol import SymbolType, FunctionSymbol, ClassSymbol, ImportSymbol
        
        parser = TreeSitterParser()
        symbol_extractor = SymbolExtractor()
        
        structured_info = {
            "module_name": module['name'],
            "files": []
        }
        
        for file_path in module['files']:
            try:
                # Full path to the file
                full_file_path = self.project_path / file_path
                if not full_file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue
                
                # Parse file with Tree-sitter
                tree = parser.parse_file(str(full_file_path))
                if not tree:
                    logger.warning(f"Failed to parse file: {file_path}")
                    continue
                
                # Extract symbols
                symbols = symbol_extractor.extract_from_tree(tree, str(full_file_path))
                
                # Structure the information
                file_info = {
                    "file_path": file_path,
                    "classes": [],
                    "functions": [],
                    "dependencies": []
                }
                
                # Group symbols by type
                class_symbols = [s for s in symbols if isinstance(s, ClassSymbol)]
                function_symbols = [s for s in symbols if isinstance(s, FunctionSymbol)]
                import_symbols = [s for s in symbols if isinstance(s, ImportSymbol)]
                
                # Process classes
                for class_sym in class_symbols:
                    class_info = {
                        "name": class_sym.name,
                        "parent_class": ", ".join(class_sym.bases) if class_sym.bases else "",
                        "docstring": class_sym.docstring or "",
                        "attributes": [],
                        "methods": []
                    }
                    
                    # Get class methods (referenced by name in class_sym.methods)
                    # We need to find the actual method symbols
                    for method_name in class_sym.methods:
                        # Find the method symbol by name
                        method_sym = next((s for s in function_symbols if s.name == method_name and s.parent_id == class_sym.id), None)
                        if method_sym:
                            method_info = {
                                "name": method_sym.name,
                                "parameters": method_sym.parameters,
                                "return_type": method_sym.return_type or "",
                                "docstring": method_sym.docstring or "",
                                "core_code": method_sym.source_code[:500] if method_sym.source_code else ""  # Truncate source code if too long
                            }
                            class_info["methods"].append(method_info)
                    
                    file_info["classes"].append(class_info)
                
                # Process standalone functions (not methods)
                for func_sym in function_symbols:
                    # Skip methods (they're already processed with their classes)
                    if func_sym.parent_id:
                        continue
                    
                    function_info = {
                        "name": func_sym.name,
                        "parameters": func_sym.parameters,
                        "return_type": func_sym.return_type or "",
                        "docstring": func_sym.docstring or "",
                        "core_code": func_sym.source_code[:500] if func_sym.source_code else ""  # Truncate source code if too long
                    }
                    file_info["functions"].append(function_info)
                
                # Extract dependencies from import symbols
                dependencies = set()
                for import_sym in import_symbols:
                    # Extract module name from module_path
                    module_name = import_sym.module_path.split('.')[0]
                    dependencies.add(module_name)
                file_info["dependencies"] = list(dependencies)
                
                structured_info["files"].append(file_info)
            except Exception as e:
                logger.error(f"Error extracting structured info from {file_path}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return structured_info
    
    def _extract_file_dependencies(self, code_map: Dict) -> Dict:
        """Extract file dependencies from code map"""
        # For now, we'll create a simple dependency map based on directory structure
        # In a more sophisticated implementation, this would analyze import statements
        dependencies = {}
        for file_info in code_map['files']:
            file_path = file_info['path']
            directory = file_info['directory']
            if directory not in dependencies:
                dependencies[directory] = []
            dependencies[directory].append(file_path)
        return dependencies
    
    def _extract_key_components(self, code_map: Dict) -> List[str]:
        """Extract key components from code map"""
        # Identify key components based on directory structure
        key_components = []
        directories = set()
        for file_info in code_map['files']:
            directory = file_info['directory']
            if directory:
                directories.add(directory)
        # Add top-level directories as key components
        for directory in sorted(directories):
            if '/' not in directory:  # Only top-level directories
                key_components.append(directory)
        # Add main files if they exist
        main_files = ['main.py', 'app.py', '__init__.py']
        for file_info in code_map['files']:
            if file_info['name'] in main_files:
                key_components.append(file_info['path'])
        return key_components
    
    def _extract_architecture_layers(self, code_map: Dict) -> List[str]:
        """Extract architecture layers from code map"""
        # Identify architecture layers based on common directory patterns
        layers = []
        layer_patterns = {
            'core': ['core', 'common', 'utils'],
            'parser': ['parser', 'analysis', 'analyzer'],
            'storage': ['storage', 'db', 'database'],
            'generator': ['generator', 'gen', 'generate'],
            'cli': ['cli', 'command', 'cmd'],
            'chat': ['chat', 'interface', 'ui']
        }
        
        for layer_name, patterns in layer_patterns.items():
            for pattern in patterns:
                for file_info in code_map['files']:
                    if pattern in file_info['path']:
                        layers.append(layer_name)
                        break
        
        # Remove duplicates and return sorted list
        return sorted(list(set(layers)))
    
    def _identify_design_patterns(self, code_map: Dict) -> List[str]:
        """Identify potential design patterns from code map"""
        # This is a simple heuristic-based approach
        # In a more sophisticated implementation, this would analyze code structure
        design_patterns = []

        # Check for common design pattern indicators
        pattern_indicators = {
            'Singleton': ['singleton', 'instance', 'get_instance'],
            'Factory': ['factory', 'create', 'builder'],
            'Strategy': ['strategy', 'algorithm', 'policy'],
            'Observer': ['observer', 'listener', 'callback'],
            'Decorator': ['decorator', 'wrap', 'wrapper'],
            'Facade': ['facade', 'api', 'interface'],
            'Command': ['command', 'action', 'handler'],
            'Template Method': ['template', 'abstract', 'base']
        }

        for pattern_name, indicators in pattern_indicators.items():
            for indicator in indicators:
                for file_info in code_map['files']:
                    if indicator in file_info['path'].lower():
                        design_patterns.append(pattern_name)
                        break

        return sorted(list(set(design_patterns)))

    def _extract_module_dependencies(self, module_divisions: List[Dict]) -> Dict:
        """Extract module dependencies from module divisions"""
        # For now, we'll create a simple dependency map based on module structure
        # In a more sophisticated implementation, this would analyze import statements between modules
        dependencies = {}
        for module in module_divisions:
            module_name = module['name']
            dependencies[module_name] = {
                'files': module['files'],
                'dependencies': []
            }
        
        # Identify potential dependencies based on file paths and common patterns
        for i, module1 in enumerate(module_divisions):
            for j, module2 in enumerate(module_divisions):
                if i != j:
                    # Check if module1 might depend on module2
                    module1_files = module1['files']
                    module2_name = module2['name'].lower()
                    
                    for file_path in module1_files:
                        if module2_name.replace(' ', '_') in file_path.lower():
                            if module2['name'] not in dependencies[module1['name']]['dependencies']:
                                dependencies[module1['name']]['dependencies'].append(module2['name'])
                            break
        
        return dependencies

    def _extract_key_components_from_modules(self, module_divisions: List[Dict]) -> List[str]:
        """Extract key components from module divisions"""
        key_components = []
        for module in module_divisions:
            key_components.append(module['name'])
        return key_components

    def _extract_architecture_layers_from_modules(self, module_divisions: List[Dict]) -> List[str]:
        """Extract architecture layers from module divisions"""
        # Identify architecture layers based on module names and common patterns
        layers = []
        layer_patterns = {
            'core': ['core', 'common', 'utils', 'base'],
            'parser': ['parser', 'analysis', 'analyzer', 'parse'],
            'storage': ['storage', 'db', 'database', 'vector', 'chroma'],
            'generator': ['generator', 'gen', 'generate', 'document', 'wiki'],
            'cli': ['cli', 'command', 'cmd', 'interface'],
            'chat': ['chat', 'qa', 'rag', 'query'],
            'embedding': ['embed', 'embedding', 'vector']
        }
        
        for module in module_divisions:
            module_name = module['name'].lower()
            for layer_name, patterns in layer_patterns.items():
                for pattern in patterns:
                    if pattern in module_name:
                        layers.append(layer_name)
                        break
        
        # Remove duplicates and return sorted list
        return sorted(list(set(layers)))

    def _generate_module_architecture_diagram(self, module_divisions: List[Dict]):
        """Generate architecture diagram based on module divisions"""
        # Generate a flowchart based on module structure
        nodes = []
        edges = []
        node_id = 0
        node_map = {}
        
        # Create nodes for each module
        for module in module_divisions:
            module_name = module['name']
            node_id_str = f"node{node_id}"
            node_id += 1
            node_map[module_name] = node_id_str
            nodes.append(f"{node_id_str}[{module_name}]")
        
        # Create edges based on potential dependencies
        # For simplicity, we'll create a basic flow from core to higher-level modules
        # In a more sophisticated implementation, this would use actual dependency analysis
        layer_order = ['core', 'parser', 'storage', 'embedding', 'generator', 'chat', 'cli']
        
        # Create a simple layered architecture
        for i in range(len(module_divisions) - 1):
            current_module = module_divisions[i]['name']
            next_module = module_divisions[i + 1]['name']
            edges.append(f"{node_map[current_module]} --> {node_map[next_module]}")
        
        # Build Mermaid diagram
        diagram = "flowchart TD\n"
        diagram += "\n".join([f"  {node}" for node in nodes]) + "\n"
        diagram += "\n".join([f"  {edge}" for edge in edges])
        
        return diagram

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

            # Generate code map and module divisions for architecture generation
            code_map = self._generate_code_map()
            module_divisions = self._ask_llm_for_module_divisions(code_map)
            
            arch = self._generate_architecture(code_map, module_divisions)
            self.writer.write_document(arch)
            logger.info("Updated overview and architecture")
    
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
    
    def _list_existing_docs(self) -> List[Document]:
        """List existing documents (for incremental update)"""
        # Simplified implementation: read from index
        index_file = self.wiki_path / ".index.json"
        if not index_file.exists():
            return []
        
        try:
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
        except Exception as e:
            logger.error(f"Failed to list existing docs: {e}")
            return []
