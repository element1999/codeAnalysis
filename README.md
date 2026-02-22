# CodeMind

AI-powered code understanding and documentation tool designed to help developers analyze, understand, and document complex codebases.

## Project Overview

CodeMind is a comprehensive code analysis tool that uses AI to automatically generate documentation, analyze code structure, and provide intelligent Q&A capabilities for software projects. It leverages tree-sitter for code parsing, ChromaDB for vector storage, and various LLM providers for intelligent analysis and documentation generation.

## Key Features

- **Automatic Documentation Generation**: Analyze codebase structure and generate structured Wiki documentation with comprehensive coverage
- **Smart Q&A System**: Answer code-related questions based on context using RAG (Retrieval-Augmented Generation) architecture
- **Code Dependency Graph**: Build and visualize dependency relationships between functions, classes, and modules
- **Call Chain Analysis**: Trace function call chains with cycle detection to understand code flow
- **Incremental Updates**: Support partial updates after code changes to save time and resources
- **Debug Mode**: Detailed logging and transparency for development and troubleshooting
- **Multiple LLM Providers**: Support for various LLM models including GLM-4.6v, Ollama, DeepSeek, Kimi, and OpenAI

## Technical Stack

- **Language**: Python 3.8+
- **Code Parsing**: Tree-sitter
- **Vector Database**: ChromaDB
- **Embedding**: FastEmbed (lightweight alternative to sentence-transformers)
- **LLM Integration**: OpenAI-compatible API (supports multiple providers)
- **CLI Framework**: Typer
- **Data Validation**: Pydantic
- **Terminal UI**: Rich
- **Documentation**: Markdown, Mermaid diagrams

## Architecture Overview

CodeMind follows a modular architecture with the following components:

1. **Core**: Configuration management, logging, and base utilities
2. **Parser**: File scanning, code parsing, symbol extraction, and dependency analysis
3. **Storage**: In-memory data structures with JSON persistence and ChromaDB integration
4. **Generator**: Documentation generation using LLM analysis
5. **Chat**: RAG-based Q&A system for code-related questions
6. **CLI**: Command-line interface for user interaction

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation Steps

```bash
# Clone the repository
git clone <repository-url>
cd codemind

# Install in development mode
pip install -e .

# Install required dependencies
pip install -r requirements.txt
```

## Usage

### Initialize Project

```bash
# Initialize CodeMind for the current directory
codemind init

# Initialize CodeMind for a specific directory
codemind init --project-path /path/to/project

# Initialize with debug mode enabled
codemind init --debug
```

### Build Documentation and Indexes

```bash
# Build everything (indexes + documentation)
codemind build

# Full rebuild (clear cache first)
codemind build --full

# Only generate documentation (skip indexing)
codemind build --docs-only

# Build with debug mode enabled
codemind build --debug
```

### Start Chat Session

```bash
# Start interactive chat session
codemind chat

# Ask a specific question non-interactively
codemind chat --query "How does the parser work?"

# Specify number of results to retrieve
codemind chat --query "How does the parser work?" --k 10

# Start chat with debug mode enabled
codemind chat --debug
```

### Check Project Status

```bash
# Check current status of CodeMind project
codemind status

# Check status with debug mode enabled
codemind status --debug
```

### Clean Cache and Indexes

```bash
# Clean default cache (cache + files)
codemind clean

# Clean only cache
codemind clean --cache

# Clean only vector indexes
codemind clean --vectors

# Clean everything (cache + files + vectors)
codemind clean --all

# Clean with debug mode enabled
codemind clean --debug
```

## Configuration

### Config File

CodeMind uses a JSON configuration file located at `.codemind/config.json`.

### Example Configuration

```json
{
  "project": {
    "name": "My Project",
    "path": ".",
    "exclude_patterns": ["*.pyc", "__pycache__", ".git", "venv"]
  },
  "llm": {
    "provider": "glm",
    "model": "glm-4.6v",
    "api_key": "your-api-key",
    "base_url": "https://open.bigmodel.cn/api/paas/v4",
    "temperature": 0.3,
    "max_tokens": 4000
  },
  "embedding": {
    "model": "BAAI/bge-small-en-v1.5",
    "dimensions": 384
  },
  "generator": {
    "wiki_path": ".codemind/wiki",
    "max_chunk_size": 1000,
    "overlap_size": 100
  }
}
```

### Configuration Options

#### Project Configuration
- `name`: Project name
- `path`: Project path
- `exclude_patterns`: List of patterns to exclude from analysis

#### LLM Configuration
- `provider`: LLM provider (glm, ollama, deepseek, kimi, openai)
- `model`: LLM model name
- `api_key`: API key for the LLM provider
- `base_url`: Base URL for the LLM API
- `temperature`: Sampling temperature for LLM responses
- `max_tokens`: Maximum tokens for LLM responses

#### Embedding Configuration
- `model`: Embedding model name
- `dimensions`: Embedding vector dimensions

#### Generator Configuration
- `wiki_path`: Path to store generated wiki documentation
- `max_chunk_size`: Maximum size of code chunks for embedding
- `overlap_size`: Overlap size between consecutive chunks

## Advanced Features

### Debug Mode

Debug mode provides detailed logging of CodeMind's operations, including:

- Scanning and parsing process
- LLM requests and responses
- Document generation steps
- RAG search results
- Storage operations

To enable debug mode, use the `--debug` flag with any command:

```bash
codemind build --docs-only --debug
```

### Custom LLM Providers

CodeMind supports multiple LLM providers. To configure a custom provider, update the `llm` section in the config file:

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4",
    "api_key": "your-openai-api-key"
  }
}
```

### Code Map Analysis

CodeMind generates comprehensive code maps based on file tree structure, which are then used by the LLM to analyze and document the codebase. These code maps include:

- File structure and organization
- Directory hierarchy
- File metadata (size, type, etc.)
- Symbol information (functions, classes, etc.)

## Troubleshooting

### Common Issues

1. **LLM API Error**
   - Check your API key and network connection
   - Verify the base URL is correct for your LLM provider
   - Ensure you have sufficient quota for your LLM provider

2. **Code Parsing Error**
   - Make sure tree-sitter is properly installed
   - Check that your code is syntactically correct
   - Verify that the language is supported by tree-sitter

3. **Embedding Error**
   - Ensure FastEmbed is properly installed
   - Check that you have enough memory for embedding operations

4. **Documentation Generation Failure**
   - Enable debug mode to see detailed error messages
   - Check LLM provider status and API limits
   - Ensure your codebase has a clear structure that can be analyzed

### Debug Logs

Debug logs are stored in `.codemind/logs/codemind.log`. Check these logs for detailed information about errors and operations.

## Contributing

We welcome contributions to CodeMind! To contribute:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes
4. Write tests for your changes
5. Submit a pull request

### Code Style

Please follow the existing code style and conventions:
- Use 4 spaces for indentation
- Follow PEP 8 guidelines
- Write clear, concise docstrings
- Include comments for complex logic

## License

CodeMind is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

## Contact

For questions, issues, or feature requests:

- Open an issue on the GitHub repository
- Contact the maintainers at: [your-email@example.com]

---

**Happy Coding!** 🚀