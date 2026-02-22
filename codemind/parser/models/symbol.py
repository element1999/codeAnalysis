"""Symbol models"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class SymbolType(str, Enum):
    """Symbol type enum"""
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"

class Symbol(BaseModel):
    """Code symbol base class"""
    id: str = Field(..., description="Global unique identifier")
    name: str
    type: SymbolType
    file_path: str
    absolute_path: str
    line_start: int
    line_end: int
    column_start: int = 0
    column_end: int = 0
    source_code: str
    docstring: Optional[str] = None
    parent_id: Optional[str] = None
    children_ids: List[str] = []
    dependencies: List[str] = []
    dependents: List[str] = []
    metadata: Dict[str, Any] = Field(default_factory=dict)
    token_count: int = 0

    def get_full_name(self) -> str:
        """Get full qualified name"""
        if self.parent_id:
            return f"{self.parent_id}.{self.name}"
        return self.name

class FunctionSymbol(Symbol):
    """Function symbol"""
    type: SymbolType = SymbolType.FUNCTION
    parameters: List[Dict[str, str]] = []
    return_type: Optional[str] = None
    is_async: bool = False
    is_generator: bool = False
    decorators: List[str] = []
    calls: List[str] = []

class ClassSymbol(Symbol):
    """Class symbol"""
    type: SymbolType = SymbolType.CLASS
    bases: List[str] = []
    methods: List[str] = []
    attributes: List[str] = []
    is_dataclass: bool = False
    is_abstract: bool = False

class ImportSymbol(Symbol):
    """Import symbol"""
    type: SymbolType = SymbolType.IMPORT
    module_path: str
    imported_names: List[str] = []
    is_from_import: bool = False
    is_relative: bool = False