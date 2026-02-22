# 模块: llm_agent

# llm_agent

# llm_agent 模块文档

## 1. 模块概述
`llm_agent` 模块是一个用于文档生成的 LLM（大语言模型）代理工具，旨在封装不同 LLM 提供商的交互逻辑，提供统一的接口以简化文档生成流程。模块支持多种 LLM 提供商（如 Ollama、DeepSeek、GLM、Kimi、OpenAI），通过配置化的方式管理不同提供商的参数（如基础 URL、默认模型、API 密钥需求），并内置预设的提示模板库（`PromptTemplates`），方便快速构建文档生成任务。

设计意图：  
- **统一接口**：屏蔽不同 LLM 提供商的底层差异，让调用方无需关心具体提供商的实现细节。  
- **配置化管理**：通过 `PROVIDER_CONFIGS` 集中管理各提供商的默认配置，便于扩展新提供商。  
- **模板化提示**：提供预设的提示模板（如项目概览文档模板），减少重复构建提示的工作量。  


## 2. 主要类说明

### 2.1 LLMProvider
**职责**：定义支持的 LLM 提供商枚举，用于标识和区分不同的 LLM 服务。  
**关键属性**：  
- `OLLAMA`：Ollama 本地 LLM 服务（默认基础 URL：`http://localhost:11434/v1`，无需 API 密钥）。  
- `DEEPSEEK`：DeepSeek 云服务（默认基础 URL：`https://api.deepseek.com/v1`，需要 API 密钥）。  
- `GLM`：GLM 云服务（默认基础 URL：`https://open.bigmodel.cn/api/paas/v4`，需要 API 密钥）。  
- `KIMI`：Kimi 云服务（默认基础 URL：`https://api.moonshot.cn/v1`，需要 API 密钥）。  
- `OPENAI`：OpenAI 云服务（默认基础 URL：`https://api.openai.com/v1`，需要 API 密钥）。  


### 2.2 LLMAgent
**职责**：LLM 交互的核心封装类，支持多提供商切换、文档生成、流式输出和多轮对话。  
**关键方法**：  
- `__init__(provider: LLMProvider, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None)`：初始化代理，指定提供商、API 密钥、基础 URL 和模型。  
- `_init_client()`：根据提供商配置初始化对应的 LLM 客户端（如 OpenAI 客户端）。  
- `generate_document(prompt: str, context: Dict) -> str`：生成文档内容，将上下文数据格式化为 JSON 并插入提示模板。  
- `generate_stream(prompt: str, context: Dict) -> Generator[str, None, None]`：流式生成文档内容，适用于需要实时输出的场景。  
- `chat(messages: List[Dict[str, str]], stream: bool = False) -> Union[str, Generator[str, None, None]]`：多轮对话接口，支持流式和非流式输出。  
- `_assemble_prompt(prompt: str, context: Dict) -> str`：组装提示，将上下文数据插入模板占位符。  
- `_clean_markdown(content: str) -> str`：清理 LLM 输出的 Markdown 格式（如去除多余空行、标准化标题）。  


### 2.3 PromptTemplates
**职责**：提示模板库，提供预设的文档生成模板，简化提示构建。  
**关键属性**：  
- `OVERVIEW_TEMPLATE`：项目概览文档模板，包含项目结构、统计信息、入口点、配置文件等章节，要求生成项目简介、技术栈、项目结构说明等。  


## 3. 函数清单
| 函数名          | 用途                                                                 | 参数                                                                 |
|-----------------|----------------------------------------------------------------------|----------------------------------------------------------------------|
| `__init__`      | 初始化 LLMAgent 实例，设置提供商、API 密钥、基础 URL 和模型               | `provider: LLMProvider`, `api_key: Optional[str] = None`, `base_url: Optional[str] = None`, `model: Optional[str] = None` |
| `_init_client`  | 根据提供商配置初始化 LLM 客户端                                       | 无                                                                   |
| `generate_document` | 生成文档内容，将上下文数据插入提示模板                                 | `prompt: str`, `context: Dict`                                         |
| `generate_stream` | 流式生成文档内容，返回生成器                                           | `prompt: str`, `context: Dict`                                         |
| `chat`          | 多轮对话接口，支持流式和非流式输出                                     | `messages: List[Dict[str, str]]`, `stream: bool = False`                 |
| `_assemble_prompt` | 组装提示，将上下文数据插入模板占位符                                   | `prompt: str`, `context: Dict`                                         |
| `_clean_markdown` | 清理 LLM 输出的 Markdown 格式                                         | `content: str`                                                        |


## 4. 使用示例
### 4.1 初始化 LLMAgent 并生成文档
```python
from llm_agent import LLMAgent, LLMProvider, PromptTemplates

# 初始化代理（使用 Ollama 本地服务）
agent = LLMAgent(provider=LLMProvider.OLLAMA)

# 准备上下文数据（项目结构、统计信息等）
context = {
    "project_structure": "src/\n  __init__.py\n  main.py\n  utils/\n    __init__.py\n    helper.py",
    "statistics": "文件数：10，代码行数：500",
    "entry_points": "main.py",
    "config_files": "config.yaml"
}

# 使用预设模板生成项目概览文档
overview = agent.generate_document(
    prompt=PromptTemplates.OVERVIEW_TEMPLATE,
    context=context
)

print(overview)
```

### 4.2 多轮对话（流式输出）
```python
# 初始化代理（使用 DeepSeek 云服务）
agent = LLMAgent(provider=LLMProvider.DEEPSEEK, api_key="your_api_key")

# 发起多轮对话
messages = [
    {"role": "user", "content": "请介绍 Python 的装饰器"},
    {"role": "assistant", "content": "装饰器是 Python 中的一种特殊语法..."},
    {"role": "user", "content": "能否举个例子？"}
]

# 流式输出对话结果
for chunk in agent.chat(messages, stream=True):
    print(chunk, end="")
```


## 5. 依赖说明
- **依赖模块**：`openai`（LLM 客户端）、`typing`（类型提示）、`json`（数据序列化）、`logging`（日志）、`enum`（枚举）。  
- **被依赖情况**：当前模块无被依赖记录（`dependents_count: 0`）。  

模块通过配置化的方式管理 LLM 提供商，无需额外依赖即可支持多种 LLM 服务，适合作为文档生成工具的核心交互层。
