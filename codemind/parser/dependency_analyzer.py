"""Dependency analyzer"""

from typing import List, Dict, Tuple, Set
from collections import defaultdict

from codemind.core.logger import logger
from codemind.parser.models.symbol import Symbol, FunctionSymbol, SymbolType

class DependencyAnalyzer:
    """Dependency analyzer"""
    
    def __init__(self):
        """Initialize dependency analyzer"""
        pass
    
    def analyze(self, symbols: List[Symbol]) -> Tuple[List[Tuple[str, str, str]], Dict[str, List[str]]]:
        """Analyze dependencies"""
        dependencies = []
        symbol_map = {s.id: s for s in symbols}
        symbol_name_index = self._build_name_index(symbols)
        
        # Analyze function calls
        for symbol in symbols:
            if isinstance(symbol, FunctionSymbol):
                for call in symbol.calls:
                    # Find matching symbols
                    matching_symbols = symbol_name_index.get(call.split('.')[0], [])
                    for match in matching_symbols:
                        if match.id != symbol.id:
                            dependencies.append((symbol.id, match.id, 'calls'))
        
        # Analyze class inheritance
        for symbol in symbols:
            if symbol.type == SymbolType.CLASS and hasattr(symbol, 'bases'):
                for base in symbol.bases:
                    matching_symbols = symbol_name_index.get(base, [])
                    for match in matching_symbols:
                        if match.type in [SymbolType.CLASS]:
                            dependencies.append((symbol.id, match.id, 'inherits'))
        
        # Analyze imports
        for symbol in symbols:
            if symbol.type == SymbolType.IMPORT:
                imported_names = symbol.imported_names
                for name in imported_names:
                    matching_symbols = symbol_name_index.get(name, [])
                    for match in matching_symbols:
                        dependencies.append((symbol.id, match.id, 'imports'))
        
        # Build dependency graph
        dependency_graph = defaultdict(list)
        for from_id, to_id, dep_type in dependencies:
            dependency_graph[from_id].append((to_id, dep_type))
        
        logger.info(f"Found {len(dependencies)} dependencies")
        return dependencies, dependency_graph
    
    def _build_name_index(self, symbols: List[Symbol]) -> Dict[str, List[Symbol]]:
        """Build symbol index by name"""
        index = defaultdict(list)
        for symbol in symbols:
            index[symbol.name].append(symbol)
        return index
    
    def detect_cycles(self, dependencies: List[Tuple[str, str, str]]) -> List[List[str]]:
        """Detect dependency cycles"""
        # Build adjacency list
        adj = defaultdict(list)
        for from_id, to_id, _ in dependencies:
            adj[from_id].append(to_id)
        
        # Detect cycles using DFS
        visited = set()
        recursion_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in recursion_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:])
                return True
            if node in visited:
                return False
            
            visited.add(node)
            recursion_stack.add(node)
            path.append(node)
            
            for neighbor in adj.get(node, []):
                dfs(neighbor, path.copy())
            
            recursion_stack.remove(node)
            path.pop()
            return False
        
        for node in adj:
            if node not in visited:
                dfs(node, [])
        
        logger.info(f"Found {len(cycles)} cycles")
        return cycles