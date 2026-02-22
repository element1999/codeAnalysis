# 模块: Embedding & Vector Storage

# Embedding & Vector Storage

# Embedding & Vector Storage 模块文档

## 1. 模块概述
### 职责
本模块负责**文本嵌入生成（Text Embedding Generation）** 和**向量数据库存储（Vector Database Storage）**，核心功能是将原始文本转换为高维向量表示（即嵌入），并将这些向量存储到不同的后端（如ChromaDB、文件、内存等），以便后续进行相似性检索或语义搜索。

### 定位
作为数据预处理和存储的核心组件，本模块是构建语义检索、知识库等应用的基础层，为上层应用提供结构化的向量数据支持。

### 设计意图
- **解耦嵌入与存储**：将嵌入生成逻辑与存储逻辑分离，使两者可独立扩展（如更换嵌入模型或存储后端）。
- **多后端支持**：支持多种向量存储后端（ChromaDB、文件、内存等），满足不同场景的需求（如开发调试用内存存储，生产用ChromaDB）。
- **统一接口**：通过抽象基类（`BaseEmbedding`、`BaseStorage`）定义统一的接口，简化上层应用的调用逻辑。


## 2. 包含文件
本模块包含两个子目录：`embedding`（嵌入相关）和`storage`（存储相关），具体文件及作用如下：

### 2.1 embedding 目录
| 文件路径 | 作用 |
|----------|------|
| `codemind/embedding/base.py` | 定义嵌入基类 `BaseEmbedding`，抽象嵌入生成的基本接口（如 `generate_embedding` 方法）。 |
| `codemind/embedding/fastembed.py` | 实现 `BaseEmbedding` 的具体子类 `FastEmbedEmbedding`，使用 `fastembed` 库生成文本嵌入。 |
| `codemind/embedding/manager.py` | 嵌入管理器 `EmbeddingManager`，负责管理嵌入模型实例、批量生成嵌入等。 |
| `codemind/embedding/__init__.py` | 模块初始化文件，导出核心类（如 `EmbeddingManager`）。 |

### 2.2 storage 目录
| 文件路径 | 作用 |
|----------|------|
| `codemind/storage/base.py` | 定义存储基类 `BaseStorage`，抽象向量存储的基本接口（如 `store_vectors`、`query_vectors` 方法）。 |
| `codemind/storage/chroma.py` | 实现 `BaseStorage` 的具体子类 `ChromaStorage`，使用 `ChromaDB` 作为存储后端。 |
| `codemind/storage/file.py` | 实现 `BaseStorage` 的具体子类 `FileStorage`，将向量存储到文件（如CSV、JSON）。 |
| `codemind/storage/memory.py` | 实现 `BaseStorage` 的具体子类 `MemoryStorage`，将向量存储在内存中（如字典）。 |
| `codemind/storage/manager.py` | 存储管理器 `StorageManager`，负责管理存储后端实例、统一存储接口调用。 |
| `codemind/storage/__init__.py` | 模块初始化文件，导出核心类（如 `StorageManager`）。 |


## 3. 核心功能
本模块的核心功能包括：
- **文本嵌入生成**：将输入文本转换为高维向量（如使用 `fastembed` 模型）。
- **向量存储**：将生成的向量存储到指定的后端（如ChromaDB、文件、内存）。
- **向量检索**：从存储后端查询与输入文本相似的向量（如通过余弦相似度）。
- **多后端支持**：支持多种存储后端，可根据需求灵活切换（如开发用内存存储，生产用ChromaDB）。


## 4. 关键组件
### 4.1 嵌入模块（embedding）
| 组件名称 | 类型 | 作用 |
|----------|------|------|
| `BaseEmbedding` | 抽象基类 | 定义嵌入生成的接口，所有嵌入实现需继承此类并实现 `generate_embedding` 方法。 |
| `FastEmbedEmbedding` | 类 | 使用 `fastembed` 库生成文本嵌入的具体实现，支持多种预训练模型（如 `BAAI/bge-small-en`）。 |
| `EmbeddingManager` | 类 | 嵌入管理器，负责初始化嵌入模型、批量生成嵌入、管理模型生命周期。 |

### 4.2 存储模块（storage）
| 组件名称 | 类型 | 作用 |
|----------|------|------|
| `BaseStorage` | 抽象基类 | 定义向量存储的接口，所有存储实现需继承此类并实现 `store_vectors`、`query_vectors` 等方法。 |
| `ChromaStorage` | 类 | 使用 `ChromaDB` 作为存储后端的实现，支持向量索引、相似性检索。 |
| `FileStorage` | 类 | 将向量存储到文件（如CSV）的实现，适合小规模数据或离线场景。 |
| `MemoryStorage` | 类 | 将向量存储在内存中的实现，适合开发调试或临时存储。 |
| `StorageManager` | 类 | 存储管理器，负责初始化存储后端、统一存储接口调用（如自动选择后端）。 |


## 5.
