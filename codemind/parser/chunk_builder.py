"""Code chunk builder"""

from typing import List, Optional
from pathlib import Path

from codemind.core.logger import logger
from codemind.parser.models.symbol import Symbol, FunctionSymbol, ClassSymbol
from codemind.parser.models.chunk import CodeChunk, ChunkType

class ChunkBuilder:
    """Code chunk builder"""
    
    def __init__(self, max_chunk_size: int = 512):
        """Initialize chunk builder"""
        self.max_chunk_size = max_chunk_size
    
    def build_chunks(self, file_path: str, tree=None, symbols: List[Symbol] = None) -> List[CodeChunk]:
        """Build chunks from symbols or file"""
        chunks = []
        chunk_id_counter = 0
        
        if symbols:
            for symbol in symbols:
                symbol_chunks = self._build_chunks_for_symbol(symbol, chunk_id_counter)
                chunks.extend(symbol_chunks)
                chunk_id_counter += len(symbol_chunks)
            
            logger.info(f"Built {len(chunks)} chunks from {len(symbols)} symbols")
        
        return chunks
    
    def _build_chunks_for_symbol(self, symbol: Symbol, chunk_id_counter: int) -> List[CodeChunk]:
        """Build chunks for specific symbol"""
        chunks = []
        
        if isinstance(symbol, ClassSymbol):
            # Class header chunk
            header_chunk = self._build_class_header_chunk(symbol, chunk_id_counter)
            if header_chunk:
                chunks.append(header_chunk)
            
        elif isinstance(symbol, FunctionSymbol):
            # Function chunk
            function_chunk = self._build_function_chunk(symbol, chunk_id_counter)
            if function_chunk:
                chunks.append(function_chunk)
        
        # Docstring chunk
        if symbol.docstring:
            docstring_chunk = self._build_docstring_chunk(symbol, chunk_id_counter + len(chunks))
            chunks.append(docstring_chunk)
        
        return chunks
    
    def _build_class_header_chunk(self, symbol: ClassSymbol, chunk_id_counter: int) -> Optional[CodeChunk]:
        """Build class header chunk"""
        content = f"class {symbol.name}"
        if symbol.bases:
            content += f"({', '.join(symbol.bases)})"
        content += ":\n"
        
        if symbol.docstring:
            content += f"    \"\"\"{symbol.docstring}\"\"\"\n"
        
        return CodeChunk(
            id=f"chunk_{symbol.id}_header_{chunk_id_counter}",
            symbol_id=symbol.id,
            content=content,
            chunk_type=ChunkType.CLASS_HEADER,
            start_line=symbol.line_start,
            end_line=symbol.line_start + 5,
            context={"file_path": symbol.file_path}
        )
    
    def _build_function_chunk(self, symbol: FunctionSymbol, chunk_id_counter: int) -> Optional[CodeChunk]:
        """Build function chunk"""
        return CodeChunk(
            id=f"chunk_{symbol.id}_{chunk_id_counter}",
            symbol_id=symbol.id,
            content=symbol.source_code,
            chunk_type=ChunkType.FUNCTION,
            start_line=symbol.line_start,
            end_line=symbol.line_end,
            context={"file_path": symbol.file_path}
        )
    
    def _build_docstring_chunk(self, symbol: Symbol, chunk_id_counter: int) -> Optional[CodeChunk]:
        """Build docstring chunk"""
        return CodeChunk(
            id=f"chunk_{symbol.id}_docstring_{chunk_id_counter}",
            symbol_id=symbol.id,
            content=symbol.docstring,
            chunk_type=ChunkType.DOCSTRING,
            start_line=symbol.line_start,
            end_line=symbol.line_start + 1,
            context={"file_path": symbol.file_path}
        )