# 模块: commands

# commands

# 模块文档：`data_processor`

## 1. 模块概述
`data_processor` 模块是数据处理层，核心职责是**统一处理数据的清洗、转换和预处理流程**，设计意图是将数据获取与业务逻辑解耦，为上层模块提供高质量、结构化的数据。该模块通过封装标准化的数据处理逻辑，支持多种数据源（如CSV、数据库、API）和格式，确保数据在进入业务层前满足一致性要求（如缺失值处理、异常值检测、特征工程等）。


## 2. 主要类说明
### 2.1 `DataCleaner`
- **职责**：负责数据清洗，解决数据质量问题（缺失值、异常值、重复值等），是数据预处理的第一步。
- **关键方法**：
  - `__init__(config: dict)`：初始化清洗配置（如缺失值处理方法、异常值阈值、重复值判断规则）。
  - `clean(data: pd.DataFrame) -> pd.DataFrame`：执行完整清洗流程（缺失值处理→异常值检测→重复值删除），返回清洗后的数据。
  - `handle_missing(data: pd.DataFrame, method: str = 'mean') -> pd.DataFrame`：根据指定方法（均值/中位数/删除）处理缺失值，支持自定义填充逻辑。

### 2.2 `DataTransformer`
- **职责**：负责数据转换，将原始数据转换为适合模型或业务逻辑的格式（如特征工程、归一化、独热编码）。
- **关键方法**：
  - `__init__(transformer_config: dict)`：初始化转换配置（如目标特征列表、转换方法、归一化范围）。
  - `transform(data: pd.DataFrame) -> pd.DataFrame`：根据配置对指定特征执行转换（如标准化年龄、独热编码城市），返回转换后的数据。


## 3. 函数清单
### 3.1 `process_data(data: pd.DataFrame, config: dict) -> pd.DataFrame`
- **用途**：统一整合清洗和转换流程，简化上层调用（无需手动实例化类）。
- **参数**：
  - `data`：待处理的数据（`pd.DataFrame`）。
  - `config`：处理配置字典，包含`clean`（清洗配置）和`transform`（转换配置）子字典。
- **返回值**：处理后的数据（`pd.DataFrame`）。


## 4. 使用示例
```python
# 导入模块
from data_processor import DataCleaner, DataTransformer, process_data
import pandas as pd

# 示例数据（模拟从数据库/CSV读取）
data = pd.DataFrame({
    'age': [25, 30, None, 40, 25],
    'salary': [5000, 6000, 7000, 8000, 5000],
    'city': ['北京', '上海', '广州', '深圳', '北京']
})

# 配置：清洗+转换
config = {
    "clean": {
        "missing_method": "mean",  # 缺失值用均值填充
        "outlier_threshold": 3     # 异常值阈值（3倍标准差）
    },
    "transform": {
        "features": ["age", "salary"],  # 需转换的特征
        "methods": {
            "age": "standardize",      # 标准化年龄
            "salary": "normalize"      # 归一化薪资
        }
    }
}

# 方式1：手动分步处理
cleaner = DataCleaner(config["clean"])
cleaned_data = cleaner.clean(data)

transformer = DataTransformer(config["transform"])
transformed_data = transformer.transform(cleaned_data)

# 方式2：统一处理（推荐）
processed_data = process_data(data, config)

print(processed_data.head())
```


## 5. 依赖说明
- **依赖模块**：
  - `pandas`：核心数据处理库（`DataFrame`操作）。
  - `numpy`：数值计算支持（均值、标准差、归一化）。
  - `logging`：日志记录（调试/监控数据处理流程）。
- **被依赖模块**：
  - `business_logic_module`：业务逻辑层，依赖本模块获取处理后的数据。
  - `api_module`：API服务层，依赖本模块处理请求中的数据（如用户输入清洗）。
