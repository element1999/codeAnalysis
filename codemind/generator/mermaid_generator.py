from typing import List, Dict, Optional
from codemind.parser.models.symbol import Symbol, SymbolType


class MermaidGenerator:
    """Generate Mermaid diagrams for architecture visualization"""
    
    def generate_class_diagram(self, symbols: List[Symbol]) -> str:
        """Generate class diagram"""
        lines = ["classDiagram"]
        
        classes = [s for s in symbols if s.type == SymbolType.CLASS]
        
        for cls in classes:
            lines.append(f"    class {cls.name}{{")
            if hasattr(cls, 'methods'):
                for method_id in cls.methods[:5]:  # Limit methods
                    method_sym = next((s for s in symbols if s.id == method_id), None)
                    if method_sym:
                        lines.append(f"        +{method_sym.name}()")
            lines.append("    ")
            
            # Inheritance relationships
            if hasattr(cls, 'bases') and cls.bases:
                for base in cls.bases:
                    lines.append(f"    {base} <|-- {cls.name}")
        
        return "\n".join(lines)
    
    def generate_flowchart(self, entry_symbol: Symbol, symbols: List[Symbol], depth: int = 3) -> str:
        """Generate flowchart (call chain from entry function)"""
        lines = ["flowchart TD"]
        
        visited = set()
        queue = [(entry_symbol, 0)]
        
        while queue:
            current, level = queue.pop(0)
            if current.id in visited or level > depth:
                continue
            visited.add(current.id)
            
            node_id = current.id.replace('-', '_')
            lines.append(f'    {node_id}["{current.name}"]')
            
            # Find called functions
            if hasattr(current, 'calls'):
                for call_name in current.calls[:5]:  # Limit branches
                    target = self._find_symbol_by_name(call_name, symbols)
                    if target:
                        target_id = target.id.replace('-', '_')
                        lines.append(f"    {node_id} --> {target_id}")
                        queue.append((target, level + 1))
        
        return "\n".join(lines)
    
    def generate_dependency_graph(self, dependencies: Dict) -> str:
        """Generate dependency graph (file level)"""
        lines = ["graph LR"]
        
        nodes = dependencies.get('nodes', [])
        edges = dependencies.get('edges', [])
        
        # Group by file
        file_deps = {}
        for edge in edges:
            from_node = next((n for n in nodes if n['id'] == edge['from']), None)
            to_node = next((n for n in nodes if n['id'] == edge['to']), None)
            if from_node and to_node:
                from_file = from_node['file']
                to_file = to_node['file']
                if from_file != to_file:
                    file_deps.setdefault(from_file, set()).add(to_file)
        
        # Generate edges (limit to avoid complexity)
        rendered_files = set()
        for from_file, to_files in list(file_deps.items())[:10]:
            from_name = self._file_to_id(from_file)
            lines.append(f'    {from_name}["{from_file}"]')
            rendered_files.add(from_file)
            
            for to_file in list(to_files)[:3]:
                to_name = self._file_to_id(to_file)
                if to_file not in rendered_files:
                    lines.append(f'    {to_name}["{to_file}"]')
                    rendered_files.add(to_file)
                lines.append(f"    {from_name} --> {to_name}")
        
        return "\n".join(lines)
    
    def _find_symbol_by_name(self, name: str, symbols: List[Symbol]) -> Optional[Symbol]:
        """Find symbol by name"""
        for sym in symbols:
            if sym.name == name:
                return sym
        return None
    
    def _file_to_id(self, file_path: str) -> str:
        """Convert file path to Mermaid ID"""
        return "f_" + file_path.replace('/', '_').replace('.', '_').replace('-', '_')
