"""Configuration manager"""

import os
import json
from pathlib import Path
from typing import Optional, List

from codemind.config.schemas import (
    CodeMindConfig, ProjectConfig, LLMConfig, 
    EmbeddingConfig, ParserConfig, GeneratorConfig,
    LLMProvider, EmbeddingProvider
)
from codemind.core.logger import logger

class ConfigManager:
    """Configuration manager for CodeMind"""
    
    CONFIG_DIR = ".codemind"
    CONFIG_FILE = "config.json"
    
    def __init__(self, project_path: str = "."):
        """Initialize config manager"""
        self.project_path = Path(project_path).resolve()
        self.config_dir = self.project_path / self.CONFIG_DIR
        self.config_path = self.config_dir / self.CONFIG_FILE
        self.config: Optional[CodeMindConfig] = None
    
    def initialize(self) -> CodeMindConfig:
        """Initialize configuration"""
        # Create config directory
        self.config_dir.mkdir(exist_ok=True)
        
        # Create default config
        default_config = self._create_default_config()
        
        # Save config
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config.model_dump(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Initialized config at {self.config_path}")
        self.config = default_config
        return default_config
    
    def load(self) -> CodeMindConfig:
        """Load configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        self.config = CodeMindConfig(**config_data)
        logger.info(f"Loaded config from {self.config_path}")
        return self.config
    
    def save(self, config: CodeMindConfig) -> None:
        """Save configuration"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved config to {self.config_path}")
        self.config = config
    
    def _create_default_config(self) -> CodeMindConfig:
        """Create default configuration"""
        return CodeMindConfig(
            project=ProjectConfig(
                name=self.project_path.name,
                path=str(self.project_path),
                language="python",
                entry_points=self._find_entry_points()
            ),
            llm=LLMConfig(
                provider=LLMProvider.OLLAMA,
                model="llama3.2",
                api_key=None,
                base_url="http://localhost:11434/v1",
                temperature=0.3,
                max_tokens=4000
            ),
            embedding=EmbeddingConfig(
                provider=EmbeddingProvider.FASTEMBED,
                model="BAAI/bge-small-en-v1.5",
                dimension=384
            ),
            parser=ParserConfig(
                exclude_dirs=[".git", "node_modules", "__pycache__", ".codemind"],
                include_patterns=["*.py"],
                max_file_size=1024 * 1024
            ),
            generator=GeneratorConfig(
                doc_language="zh",
                max_workers=4
            )
        )
    
    def _find_entry_points(self) -> List[str]:
        """Find potential entry points"""
        entry_points = []
        common_entry_points = ["src/main.py", "main.py", "app.py", "run.py"]
        
        for entry_point in common_entry_points:
            if (self.project_path / entry_point).exists():
                entry_points.append(entry_point)
        
        return entry_points or ["src/main.py"]