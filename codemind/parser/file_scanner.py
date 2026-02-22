"""File scanner"""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from codemind.core.logger import logger
from codemind.config.schemas import ParserConfig
from codemind.config.manager import ConfigManager

@dataclass
class FileInfo:
    """File information"""
    relative_path: str
    absolute_path: str
    size: int
    mtime: float
    md5: str
    language: str

class FileScanner:
    """File scanner for project"""
    
    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
    }
    
    DEFAULT_EXCLUDE = {
        '.git', '__pycache__', '.codemind', 'node_modules',
        '.venv', 'venv', '.env', 'dist', 'build', '.pytest_cache'
    }
    
    DEFAULT_INCLUDE = [
        '*.py', '*.js', '*.ts', '*.java', '*.go', '*.rs'
    ]
    
    def __init__(self, project_path: str = ".", config: Optional[ParserConfig] = None):
        """Initialize file scanner"""
        self.project_path = Path(project_path).resolve()
        
        # Use provided config or create default
        if config:
            self.config = config
        else:
            # Create default config
            config_manager = ConfigManager(project_path)
            try:
                # Try to load existing config
                code_mind_config = config_manager.load()
                self.config = code_mind_config.parser
            except Exception:
                # Create default ParserConfig if load fails
                self.config = ParserConfig(
                    exclude_dirs=[".git", "node_modules", "__pycache__", ".codemind"],
                    include_patterns=["*.py"],
                    max_file_size=1024 * 1024
                )
        
        self.exclude_dirs = set(self.config.exclude_dirs) | self.DEFAULT_EXCLUDE
        self.include_patterns = self.config.include_patterns or self.DEFAULT_INCLUDE
    
    def scan(self) -> List[str]:
        """Scan project files and return absolute paths"""
        logger.info(f"Scanning project: {self.project_path}")
        
        files = []
        
        for pattern in self.include_patterns:
            for file_path in self.project_path.rglob(pattern):
                if self._should_skip(file_path):
                    continue
                
                files.append(str(file_path))
        
        logger.info(f"Found {len(files)} files")
        return sorted(files)
    
    def scan_with_info(self) -> List[FileInfo]:
        """Scan project files and return FileInfo objects"""
        logger.info(f"Scanning project: {self.project_path}")
        
        files = []
        
        for pattern in self.include_patterns:
            for file_path in self.project_path.rglob(pattern):
                if self._should_skip(file_path):
                    continue
                
                file_info = self._get_file_info(file_path)
                files.append(file_info)
        
        logger.info(f"Found {len(files)} files")
        return sorted(files, key=lambda f: f.relative_path)
    
    def compute_changes(self, current_files: List[FileInfo], 
                       indexed_files: Dict[str, dict]) -> Tuple[List, List, List]:
        """Compute file changes"""
        current_map = {f.relative_path: f for f in current_files}
        indexed_map = {k: v for k, v in indexed_files.items()}
        
        added = []
        modified = []
        deleted = []
        
        # Added and modified files
        for rel_path, file_info in current_map.items():
            if rel_path not in indexed_map:
                added.append(file_info)
            elif indexed_map[rel_path]['md5'] != file_info.md5:
                modified.append(file_info)
        
        # Deleted files
        for rel_path in indexed_map:
            if rel_path not in current_map:
                deleted.append(rel_path)
        
        logger.info(f"Changes: added={len(added)}, modified={len(modified)}, deleted={len(deleted)}")
        return added, modified, deleted
    
    def _should_skip(self, path: Path) -> bool:
        """Check if path should be skipped"""
        # Check exclude directories
        for part in path.parts:
            if part in self.exclude_dirs:
                return True
        
        # Check hidden files
        if any(p.startswith('.') for p in path.parts):
            return True
            
        # Check file size
        max_size = getattr(self.config, 'max_file_size', 1024 * 1024)  # Default 1MB
        if path.stat().st_size > max_size:
            logger.debug(f"Skipping large file: {path}")
            return True
            
        return False
    
    def _get_file_info(self, path: Path) -> FileInfo:
        """Get file information"""
        stat = path.stat()
        with open(path, 'rb') as f:
            content = f.read()
        
        return FileInfo(
            relative_path=str(path.relative_to(self.project_path)),
            absolute_path=str(path),
            size=stat.st_size,
            mtime=stat.st_mtime,
            md5=hashlib.md5(content).hexdigest(),
            language=self._detect_language(path)
        )
    
    def _detect_language(self, path: Path) -> str:
        """Detect language from extension"""
        return self.LANGUAGE_MAP.get(path.suffix.lower(), 'unknown')