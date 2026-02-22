"""Core utilities"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

def get_file_hash(file_path: Path) -> str:
    """Get file hash"""
    with open(file_path, 'rb') as f:
        content = f.read()
        return hashlib.md5(content).hexdigest()

def load_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

def save_json(file_path: Path, data: Dict[str, Any]) -> bool:
    """Save JSON file"""
    try:
        file_path.parent.mkdir(exist_ok=True, parents=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def ensure_dir(dir_path: Path) -> None:
    """Ensure directory exists"""
    dir_path.mkdir(exist_ok=True, parents=True)

def get_relative_path(path: Path, base: Path) -> str:
    """Get relative path"""
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)

def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."