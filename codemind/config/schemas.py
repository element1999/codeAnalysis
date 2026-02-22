"""Configuration schemas"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class LLMProvider(str, Enum):
    """LLM provider enum"""
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"
    GLM = "glm"
    KIMI = "kimi"
    OPENAI = "openai"

class EmbeddingProvider(str, Enum):
    """Embedding provider enum"""
    FASTEMBED = "fastembed"
    OPENAI = "openai"

class ProjectConfig(BaseModel):
    """Project configuration"""
    name: str = Field(default="my-project", description="Project name")
    path: str = Field(..., description="Project path")
    language: str = Field(default="python", description="Project language")
    entry_points: List[str] = Field(default=["src/main.py"], description="Entry points")

class LLMConfig(BaseModel):
    """LLM configuration"""
    provider: LLMProvider = Field(default=LLMProvider.OLLAMA, description="LLM provider")
    model: str = Field(default="llama3.2", description="LLM model")
    api_key: Optional[str] = Field(default=None, description="API key")
    base_url: Optional[str] = Field(default=None, description="Base URL")
    temperature: float = Field(default=0.3, description="Temperature")
    max_tokens: int = Field(default=4000, description="Max tokens")

class EmbeddingConfig(BaseModel):
    """Embedding configuration"""
    provider: EmbeddingProvider = Field(default=EmbeddingProvider.FASTEMBED, description="Embedding provider")
    model: str = Field(default="BAAI/bge-small-en-v1.5", description="Embedding model")
    dimension: int = Field(default=384, description="Embedding dimension")

class ParserConfig(BaseModel):
    """Parser configuration"""
    exclude_dirs: List[str] = Field(
        default=[".git", "node_modules", "__pycache__", ".codemind"],
        description="Directories to exclude"
    )
    include_patterns: List[str] = Field(default=["*.py"], description="Include patterns")
    max_file_size: int = Field(default=1024 * 1024, description="Max file size (bytes)")

class GeneratorConfig(BaseModel):
    """Generator configuration"""
    doc_language: str = Field(default="zh", description="Documentation language")
    max_workers: int = Field(default=4, description="Max workers")

class CodeMindConfig(BaseModel):
    """CodeMind configuration"""
    project: ProjectConfig
    llm: LLMConfig
    embedding: EmbeddingConfig
    parser: ParserConfig
    generator: GeneratorConfig