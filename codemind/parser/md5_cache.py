"""MD5 cache for incremental parsing"""

import json
import os
from pathlib import Path
from typing import Dict, Optional
import hashlib

from codemind.core.utils import load_json, save_json
from codemind.core.logger import logger

class MD5Cache:
    """MD5 cache for incremental parsing"""
    
    def __init__(self, cache_path: str = ".codemind/cache.json"):
        """Initialize MD5 cache"""
        self.cache_path = Path(cache_path)
        # Create directory if it doesn't exist
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, dict]:
        """Load cache from file"""
        data = load_json(self.cache_path)
        return data or {}
    
    def save(self) -> bool:
        """Save cache to file"""
        return save_json(self.cache_path, self.cache)
    
    def get(self, file_path: str) -> Optional[dict]:
        """Get file info from cache"""
        return self.cache.get(file_path)
    
    def set(self, file_path: str, file_info: dict) -> None:
        """Set file info in cache"""
        self.cache[file_path] = file_info
        self.save()
    
    def remove(self, file_path: str) -> None:
        """Remove file from cache"""
        if file_path in self.cache:
            del self.cache[file_path]
            self.save()
    
    def clear(self) -> None:
        """Clear cache"""
        self.cache.clear()
        self.save()
    
    def has_changed(self, file_path: str, current_md5: str) -> bool:
        """Check if file has changed"""
        cached = self.get(file_path)
        return not cached or cached.get('md5') != current_md5
    
    def needs_update(self, file_path: str) -> bool:
        """Check if file needs update"""
        if not os.path.exists(file_path):
            return False
        
        # Calculate current MD5
        try:
            with open(file_path, 'rb') as f:
                current_md5 = hashlib.md5(f.read()).hexdigest()
        except Exception:
            return True
        
        return self.has_changed(file_path, current_md5)
    
    def update(self, file_path: str) -> None:
        """Update file in cache"""
        if not os.path.exists(file_path):
            return
        
        try:
            with open(file_path, 'rb') as f:
                current_md5 = hashlib.md5(f.read()).hexdigest()
            
            file_info = {
                'md5': current_md5,
                'modified': os.path.getmtime(file_path)
            }
            self.set(file_path, file_info)
        except Exception as e:
            logger.error(f"Failed to update cache for {file_path}: {e}")
    
    def get_cache(self) -> Dict[str, dict]:
        """Get entire cache"""
        return self.cache