"""Symbol extractor"""

from typing import List, Dict, Optional
from pathlib import Path

from codemind.core.logger import logger
from codemind.parser.tree_sitter_parser import TreeSitterParser
from codemind.parser.models.symbol import Symbol

class SymbolExtractor:
    """Symbol extractor"""
    
    def __init__(self):
        """Initialize symbol extractor"""
        self.parser = TreeSitterParser()
    
    def extract_from_file(self, file_path: str) -> List[Symbol]:
        """Extract symbols from file"""
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()
            
            tree = self.parser.parse(source_code, file_path)
            if not tree:
                return []
            
            symbols = self.extract_from_tree(tree, file_path)
            logger.info(f"Extracted {len(symbols)} symbols from {file_path}")
            return symbols
            
        except Exception as e:
            logger.error(f"Failed to extract symbols from {file_path}: {e}")
            return []
    
    def extract_from_tree(self, tree, file_path: str) -> List[Symbol]:
        """Extract symbols from tree"""
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()
            
            symbols = self.parser.extract_symbols(tree, source_code, file_path)
            return symbols
            
        except Exception as e:
            logger.error(f"Failed to extract symbols from tree: {e}")
            return []
    
    def extract_from_files(self, files: List[str]) -> Dict[str, List[Symbol]]:
        """Extract symbols from multiple files"""
        results = {}
        
        for file_path in files:
            symbols = self.extract_from_file(file_path)
            if symbols:
                results[file_path] = symbols
        
        total_symbols = sum(len(syms) for syms in results.values())
        logger.info(f"Total symbols extracted: {total_symbols} from {len(results)} files")
        return results
    
    def build_symbol_map(self, symbols: List[Symbol]) -> Dict[str, Symbol]:
        """Build symbol map by ID"""
        symbol_map = {}
        for symbol in symbols:
            symbol_map[symbol.id] = symbol
        return symbol_map
    
    def build_symbol_index(self, symbols: List[Symbol]) -> Dict[str, List[Symbol]]:
        """Build symbol index by name"""
        index = {}
        for symbol in symbols:
            if symbol.name not in index:
                index[symbol.name] = []
            index[symbol.name].append(symbol)
        return index