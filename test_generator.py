#!/usr/bin/env python3
"""Test script to debug wiki generation"""

import json
import traceback
from pathlib import Path

print("Step 1: Importing required modules...")
try:
    from codemind.config.manager import ConfigManager
    from codemind.storage.manager import StorageManager
    from codemind.generator import DocumentGenerator
    print("✓ All modules imported successfully")
except Exception as e:
    print(f"✗ Import error: {e}")
    traceback.print_exc()
    exit(1)

print("\nStep 2: Loading config...")
try:
    config_manager = ConfigManager(".")
    config = config_manager.load()
    print(f"✓ Config loaded: {config.project.name}")
except Exception as e:
    print(f"✗ Config error: {e}")
    traceback.print_exc()
    exit(1)

print("\nStep 3: Initializing storage...")
try:
    storage_manager = StorageManager()
    print(f"✓ Storage initialized: {storage_manager.storage_path}")
except Exception as e:
    print(f"✗ Storage error: {e}")
    traceback.print_exc()
    exit(1)

print("\nStep 4: Creating DocumentGenerator...")
try:
    # Convert config format
    llm_config_dict = {
        "provider": config.llm.provider,
        "model": config.llm.model,
        "api_key": config.llm.api_key,
        "base_url": config.llm.base_url,
        "temperature": config.llm.temperature,
        "max_tokens": config.llm.max_tokens
    }
    
    generator = DocumentGenerator(
        project_path=".",
        storage_path=storage_manager.storage_path,
        llm_config=llm_config_dict
    )
    print("✓ DocumentGenerator created successfully")
except Exception as e:
    print(f"✗ Generator creation error: {e}")
    traceback.print_exc()
    exit(1)

print("\nStep 5: Loading symbols...")
try:
    symbols = generator._load_symbols()
    print(f"✓ Loaded {len(symbols)} symbols")
except Exception as e:
    print(f"✗ Symbol loading error: {e}")
    traceback.print_exc()
    exit(1)

print("\nStep 6: Testing context assembly...")
try:
    context = generator.context_assembler.assemble_for_overview()
    print("✓ Context assembly successful")
    print(f"  - Project structure: {len(context['project_structure'])} characters")
    print(f"  - Modules: {len(context['modules'])}")
    print(f"  - Entry points: {len(context['entry_points'])}")
except Exception as e:
    print(f"✗ Context assembly error: {e}")
    traceback.print_exc()
    exit(1)

print("\n✓ All tests passed! Wiki generation should work now.")
