"""Code chunk models"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class ChunkType(str, Enum):
    """Chunk type enum"""
    SOURCE = "source"
    DOCSTRING = "docstring"
    SIGNATURE = "signature"
    CLASS_HEADER = "class_header"
    METHOD = "method"
    FUNCTION = "function"
    CONTROL_BLOCK = "control_block"
    LOGIC_BLOCK = "logic_block"
    FEATURE_BLOCK = "feature_block"

class CodeChunk(BaseModel):
    """Code chunk"""
    id: str = Field(..., description="Chunk ID")
    symbol_id: str = Field(..., description="Associated symbol ID")
    content: str = Field(..., description="Chunk content")
    chunk_type: ChunkType = Field(..., description="Chunk type")
    start_line: int = Field(..., description="Start line")
    end_line: int = Field(..., description="End line")
    token_count: int = Field(default=0, description="Token count")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")