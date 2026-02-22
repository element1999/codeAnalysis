# 模块: Core Module

# Core Module

# Core Module 模块文档

## 1. 模块概述
**职责**：提供应用程序的核心工具函数、全局常量定义及日志记录功能，作为 CodeMind 架构的基础支撑模块。  
**定位**：贯穿整个应用的底层依赖模块，封装通用逻辑以避免重复代码。  
**设计意图**：通过集中管理基础功能，确保代码的一致性和可维护性，同时为上层模块提供标准化的工具和配置。


## 2. 包含文件
| 文件路径                     | 作用描述                     |
|------------------------------|------------------------------|
| `codemind/core/__init__.py`    | 模块初始化文件，用于统一导出核心功能 |
| `codemind/core/constants.py`   | 定义全局常量（如配置参数、路径等） |
| `codemind/core/logger.py`      | 提供日志记录功能，支持多级别日志输出 |
| `codemind/core/utils.py`       | 封装通用工具函数（如 JSON 处理、路径操作、哈希计算等） |


## 3. 核心功能
- **常量管理**：通过 `constants.py` 集中定义全局配置参数、路径等常量，便于统一维护。  
- **日志记录**：通过 `logger.py` 实现结构化日志输出，支持不同级别（如 DEBUG、INFO、ERROR）的日志记录。  
- **工具函数**：通过 `utils.py` 提供通用工具，包括 JSON 序列化/反序列化、路径操作、哈希计算等功能。  
- **模块导出**：通过 `__init__.py` 统一导出核心功能，简化上层模块的导入路径。


## 4. 关键组件
| 文件路径                     | 关键组件类型       | 说明                     |
|------------------------------|--------------------|--------------------------|
| `codemind/core/constants.py`   | 常量定义           | 全局配置参数（如 `LOG_LEVEL`、`DATA_DIR` 等） |
| `codemind/core/logger.py`      | 日志记录器         | 基于 Python `logging` 模块的日志工具 |
| `codemind/core/utils.py`       | 工具函数           | JSON 处理（`json_load`/`json_dump`）、路径操作（`Path` 相关函数）、哈希计算（`hash_file`）等 |


## 5. 使用方法
### 5.1 导入常量
```python
from codemind.core.constants import LOG_LEVEL, DATA_DIR
print(f"日志级别: {LOG_LEVEL}, 数据目录: {DATA_DIR}")
```

### 5.2 使用日志记录
```python
from codemind.core.logger import get_logger

logger = get_logger(__name__)
logger.info("这是一条信息日志")
logger.error("这是一条错误日志")
```

### 5.3 调用工具函数
```python
from codemind.core.utils import json_load, hash_file

# 加载 JSON 文件
data = json_load("config.json")

# 计算文件哈希值
file_hash = hash_file("example.txt")
```


## 6. 依赖关系
| 文件路径                     | 依赖模块               | 依赖说明                     |
|------------------------------|------------------------|------------------------------|
| `codemind/core/logger.py`      | `logging`              | Python 标准日志模块，用于日志记录 |
| `codemind/core/logger.py`      | `pathlib`              | 路径操作（如 `Path` 类）       |
| `codemind/core/logger.py`      | `os`                   | 操作系统相关功能（如环境变量）  |
| `codemind/core/utils.py`       | `json`                 | JSON 序列化/反序列化          |
| `codemind/core/utils.py`       | `pathlib`              | 路径操作                     |
| `codemind/core/utils.py`       | `hashlib`              | 哈希计算（如 MD5、SHA256）    |
| `codemind/core/utils.py`       | `typing`               | 类型提示支持                 |

> 注：`codemind/core/__init__.py` 和 `codemind/core/constants.py` 无外部依赖。
