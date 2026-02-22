"""Context assembler for LLM documentation generation"""

import json
import logging
from typing import List, Dict, Any
from codemind.parser.models.symbol import Symbol, SymbolType

logger = logging.getLogger(__name__)


class ContextAssembler:
    """
    Assemble context information for LLM documentation generation
    Strategy: Select relevant symbols based on document type and build structured context
    """
    
    def __init__(self, symbols: List[Symbol], dependencies: Dict):
        self.symbols = symbols
        self.dependencies = dependencies
        self.symbol_map = {s.id: s for s in symbols}
    
    def assemble_for_overview(self) -> Dict[str, Any]:
        """Assemble context for project overview"""
        logger.info("Assembling overview context...")
        
        # Collect top-level modules
        logger.info("Collecting top-level modules...")
        modules = [s for s in self.symbols if s.type == SymbolType.MODULE]
        logger.info(f"Found {len(modules)} top-level modules")
        for module in modules:
            logger.info(f"  - {module.name} ({module.file_path})")
        
        # Collect entry points (files containing main function or app creation)
        logger.info("Collecting entry points...")
        entry_points = []
        for sym in self.symbols:
            if sym.type == SymbolType.FUNCTION and sym.name in ['main', 'create_app', 'run']:
                entry_points.append(sym)
                logger.info(f"  - Entry point function: {sym.name} ({sym.file_path}:{sym.line_start})")
            if 'config' in sym.name.lower() and sym.type == SymbolType.MODULE:
                entry_points.append(sym)
                logger.info(f"  - Config module: {sym.name} ({sym.file_path})")
        
        # Collect configuration information (requirements.txt, package.json, etc.)
        logger.info("Finding configuration files...")
        config_files = self._find_config_files()
        logger.info(f"Found {len(config_files)} configuration files")
        for config in config_files:
            logger.info(f"  - {config['name']}")
        
        # Statistics
        logger.info("Calculating project statistics...")
        stats = self._calculate_stats()
        logger.info(f"Statistics: {json.dumps(stats, ensure_ascii=False)}")
        
        # Extract key dependencies
        logger.info("Extracting key dependencies...")
        dependencies = self._extract_key_dependencies()
        logger.info(f"Key dependencies: {dependencies}")
        
        # Build project structure
        logger.info("Building project tree structure...")
        tree_structure = self._build_tree_structure()
        logger.info(f"Project structure:\n{tree_structure}")
        
        context = {
            "project_structure": tree_structure,
            "modules": [self._summarize_symbol(m) for m in modules[:20]],  # Limit quantity
            "entry_points": [self._summarize_symbol(ep) for ep in entry_points],
            "config_files": config_files,
            "statistics": stats,
            "dependencies": dependencies
        }
        
        logger.info("Overview context assembled successfully")
        return context
    
    def assemble_for_module(self, module_symbol: Symbol) -> Dict[str, Any]:
        """Assemble context for specific module"""
        logger.info(f"Assembling context for module: {module_symbol.name} ({module_symbol.file_path})")
        
        # Get all symbols in the module
        logger.info("Collecting symbols in module...")
        module_symbols = [
            s for s in self.symbols 
            if s.file_path == module_symbol.file_path and s.id != module_symbol.id
        ]
        logger.info(f"Found {len(module_symbols)} symbols in module")
        
        # Categorize
        logger.info("Categorizing module symbols...")
        classes = [s for s in module_symbols if s.type == SymbolType.CLASS]
        functions = [s for s in module_symbols if s.type == SymbolType.FUNCTION]
        imports = [s for s in module_symbols if s.type == SymbolType.IMPORT]
        
        logger.info(f"  - Classes: {len(classes)}")
        for cls in classes:
            logger.info(f"    - {cls.name} ({cls.line_start}-{cls.line_end})")
        
        logger.info(f"  - Functions: {len(functions)}")
        for func in functions:
            logger.info(f"    - {func.name} ({func.line_start}-{func.line_end})")
        
        logger.info(f"  - Imports: {len(imports)}")
        for imp in imports:
            logger.info(f"    - {imp.name}")
        
        # Get module dependencies
        logger.info("Analyzing module dependencies...")
        module_deps = self._get_module_dependencies(module_symbol.file_path)
        logger.info(f"Module dependencies: {json.dumps(module_deps, ensure_ascii=False)}")
        
        # Get source code preview
        source_preview = module_symbol.source_code[:500] if hasattr(module_symbol, 'source_code') else ''
        logger.debug(f"Module source code preview: {source_preview}")
        
        context = {
            "module_info": self._summarize_symbol(module_symbol, detailed=True),
            "classes": [self._summarize_symbol(c, detailed=True) for c in classes],
            "functions": [self._summarize_symbol(f) for f in functions],
            "imports": [self._summarize_symbol(i) for i in imports],
            "dependencies": module_deps,
            "source_code": module_symbol.source_code[:2000]  # Limit length
        }
        
        logger.info("Module context assembled successfully")
        return context
    
    def assemble_for_architecture(self) -> Dict[str, Any]:
        """Assemble context for architecture analysis"""
        logger.info("Assembling architecture context...")
        
        # Build dependency graph summary
        logger.info("Summarizing dependency graph...")
        graph_summary = self._summarize_dependency_graph()
        logger.info(f"Dependency graph summary: {json.dumps(graph_summary, ensure_ascii=False)}")
        
        # Identify key components (highly connected nodes)
        logger.info("Identifying key components...")
        key_components = self._identify_key_components()
        logger.info(f"Found {len(key_components)} key components:")
        for component in key_components:
            logger.info(f"  - {component['name']} ({component['type']}) in {component['file']} with {component['connections']} connections")
        
        # Identify layered structure (e.g., MVC, layered architecture)
        logger.info("Identifying architecture layers...")
        layers = self._identify_layers()
        logger.info(f"Architecture layers: {json.dumps(layers, ensure_ascii=False)}")
        
        # Detect design patterns
        logger.info("Detecting design patterns...")
        design_patterns = self._detect_design_patterns()
        logger.info(f"Design patterns detected: {design_patterns}")
        
        context = {
            "dependency_graph": graph_summary,
            "key_components": key_components,
            "layers": layers,
            "design_patterns": design_patterns
        }
        
        logger.info("Architecture context assembled successfully")
        return context
    
    def _summarize_symbol(self, sym: Symbol, detailed: bool = False) -> Dict:
        """Convert symbol to summary information"""
        summary = {
            "name": sym.name,
            "type": sym.type.value,
            "file": sym.file_path,
            "line": sym.line_start,
            "docstring": sym.docstring[:200] if sym.docstring else None
        }
        
        if detailed:
            summary.update({
                "source_preview": sym.source_code[:500],
                "dependencies_count": len(getattr(sym, 'dependencies', [])),
                "dependents_count": len(getattr(sym, 'dependents', []))
            })
            
            if hasattr(sym, 'parameters'):
                summary['signature'] = self._build_signature(sym)
        
        return summary
    
    def _build_signature(self, sym) -> str:
        """Build function signature"""
        if hasattr(sym, 'parameters'):
            params = ", ".join([
                f"{p.get('name', 'arg')}: {p.get('type', 'Any')}" 
                for p in sym.parameters
            ])
            ret = f" -> {sym.return_type}" if hasattr(sym, 'return_type') and sym.return_type else ""
            return f"def {sym.name}({params}){ret}"
        return sym.name
    
    def _build_tree_structure(self) -> str:
        """Build project tree structure text"""
        tree = {}
        for sym in self.symbols:
            if sym.type == SymbolType.MODULE:
                parts = sym.file_path.split('/')
                current = tree
                for part in parts:
                    current = current.setdefault(part, {})
        
        def render(node, prefix=""):
            lines = []
            items = sorted(node.items())
            for i, (name, subtree) in enumerate(items):
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{name}")
                if subtree:
                    extension = "    " if is_last else "│   "
                    lines.extend(render(subtree, prefix + extension))
            return lines
        
        return "\n".join(render(tree))
    
    def _calculate_stats(self) -> Dict:
        """Calculate project statistics"""
        return {
            "total_files": len(set(s.file_path for s in self.symbols if s.type == SymbolType.MODULE)),
            "total_classes": len([s for s in self.symbols if s.type == SymbolType.CLASS]),
            "total_functions": len([s for s in self.symbols if s.type == SymbolType.FUNCTION]),
            "total_lines": sum(s.line_end - s.line_start for s in self.symbols)
        }
    
    def _find_config_files(self) -> List[Dict]:
        """Find configuration files"""
        configs = []
        for sym in self.symbols:
            if sym.type == SymbolType.MODULE:
                fname = sym.file_path.lower()
                if any(x in fname for x in ['requirements', 'package', 'pyproject', 'setup', 'dockerfile', 'makefile']):
                    configs.append({
                        "name": sym.file_path,
                        "preview": sym.source_code[:500]
                    })
        return configs
    
    def _extract_key_dependencies(self) -> List[str]:
        """Extract key external dependencies"""
        imports = set()
        for sym in self.symbols:
            if sym.type == SymbolType.IMPORT and hasattr(sym, 'module_path'):
                module = sym.module_path.split('.')[0]
                if module not in ['sys', 'os', 'typing', 'collections', 'json']:
                    imports.add(module)
        return sorted(list(imports))[:20]
    
    def _get_module_dependencies(self, file_path: str) -> Dict:
        """Get module-level dependencies"""
        module_syms = [s for s in self.symbols if s.file_path == file_path]
        
        incoming = []
        outgoing = []
        
        for sym in module_syms:
            # Outgoing dependencies
            dependencies = getattr(sym, 'dependencies', [])
            for dep_id in dependencies:
                dep_sym = self.symbol_map.get(dep_id)
                if dep_sym and dep_sym.file_path != file_path:
                    outgoing.append({
                        "symbol": sym.name,
                        "depends_on": dep_sym.name,
                        "in_file": dep_sym.file_path
                    })
            
            # Incoming dependencies
            for dep_sym in self.symbols:
                dep_dependencies = getattr(dep_sym, 'dependencies', [])
                if sym.id in dep_dependencies and dep_sym.file_path != file_path:
                    incoming.append({
                        "symbol": dep_sym.name,
                        "in_file": dep_sym.file_path,
                        "depends_on": sym.name
                    })
        
        return {"incoming": incoming[:10], "outgoing": outgoing[:10]}
    
    def _summarize_dependency_graph(self) -> Dict:
        """Summarize dependency graph"""
        nodes = self.dependencies.get('nodes', [])
        edges = self.dependencies.get('edges', [])
        
        # Statistics
        file_deps = {}
        for edge in edges:
            from_node = next((n for n in nodes if n['id'] == edge['from']), None)
            to_node = next((n for n in nodes if n['id'] == edge['to']), None)
            if from_node and to_node:
                from_file = from_node.get('file', '')
                to_file = to_node.get('file', '')
                if from_file != to_file:
                    file_deps.setdefault(from_file, []).append(to_file)
        
        return {
            "total_symbols": len(nodes),
            "total_relations": len(edges),
            "file_dependencies": {k: list(set(v))[:5] for k, v in list(file_deps.items())[:10]}
        }
    
    def _identify_key_components(self) -> List[Dict]:
        """Identify key components (high-connection nodes)"""
        node_connections = {}
        for edge in self.dependencies.get('edges', []):
            node_connections[edge['from']] = node_connections.get(edge['from'], 0) + 1
            node_connections[edge['to']] = node_connections.get(edge['to'], 0) + 1
        
        sorted_nodes = sorted(
            node_connections.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        result = []
        for node_id, count in sorted_nodes:
            sym = self.symbol_map.get(node_id)
            if sym:
                result.append({
                    "name": sym.name,
                    "type": sym.type.value,
                    "file": sym.file_path,
                    "connections": count
                })
        
        return result
    
    def _identify_layers(self) -> List[Dict]:
        """Identify architecture layers (heuristic)"""
        layers = {
            "api": [],      # Contains route, view, controller
            "service": [],  # Contains service, business
            "data": [],     # Contains model, repository, db
            "util": []      # Others
        }
        
        for sym in self.symbols:
            path = sym.file_path.lower()
            name = sym.name.lower()
            
            if any(x in path for x in ['route', 'view', 'controller', 'api', 'endpoint']):
                layers['api'].append(sym.file_path)
            elif any(x in path for x in ['service', 'business', 'logic']):
                layers['service'].append(sym.file_path)
            elif any(x in path for x in ['model', 'repository', 'db', 'data', 'entity']):
                layers['data'].append(sym.file_path)
            else:
                layers['util'].append(sym.file_path)
        
        # Deduplicate and limit
        return [
            {"name": k, "files": list(set(v))[:5]} 
            for k, v in layers.items() if v
        ]
    
    def _detect_design_patterns(self) -> List[str]:
        """Detect possible design patterns (heuristic)"""
        patterns = []
        
        # Check singleton pattern
        singleton_candidates = [
            s for s in self.symbols 
            if s.type == SymbolType.CLASS and 'instance' in s.source_code.lower()
        ]
        if singleton_candidates:
            patterns.append("Singleton (疑似)")
        
        # Check factory pattern
        factory_candidates = [
            s for s in self.symbols
            if 'factory' in s.name.lower() or 'create' in s.name.lower()
        ]
        if factory_candidates:
            patterns.append("Factory (疑似)")
        
        # Check dependency injection
        di_candidates = [
            s for s in self.symbols
            if hasattr(s, 'parameters') and any('inject' in str(p).lower() for p in s.parameters)
        ]
        if di_candidates:
            patterns.append("Dependency Injection (疑似)")
        
        return patterns
