"""Constants"""

# Directory names
CODEMIND_DIR = ".codemind"
VECTORS_DIR = "vectors"
INDEX_DIR = "index"
WIKI_DIR = "wiki"
CACHE_DIR = "cache"
LOGS_DIR = "logs"

# File names
CONFIG_FILE = "config.json"
STATE_FILE = "state.json"
FILES_JSON = "files.json"
SYMBOLS_JSON = "symbols.json"
DEPENDENCIES_JSON = "dependencies.json"

# Default values
DEFAULT_LANGUAGE = "python"
DEFAULT_LLM_PROVIDER = "ollama"
DEFAULT_LLM_MODEL = "llama3.2"
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_EMBEDDING_DIMENSION = 384

# Limits
MAX_FILE_SIZE = 1024 * 1024  # 1MB
MAX_CHUNK_SIZE = 512  # tokens
MAX_CONTEXT_SIZE = 3000  # tokens