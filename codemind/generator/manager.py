from typing import Optional, Dict, Any
from codemind.generator import DocumentGenerator
from codemind.config.schemas import LLMConfig, GeneratorConfig


class GeneratorManager:
    """生成器管理器"""
    
    def __init__(self, llm_config: Optional[LLMConfig] = None,
                 generator_config: Optional[GeneratorConfig] = None):
        """初始化生成器管理器
        
        Args:
            llm_config: LLM配置
            generator_config: 生成器配置
        """
        self.llm_config = llm_config
        self.generator_config = generator_config
    
    def generate_docs(self, project_path: str, storage_path: str) -> Dict:
        """
        生成项目文档
        
        Args:
            project_path: 项目根路径
            storage_path: 存储路径
        
        Returns:
            生成统计信息
        """
        from codemind.generator import DocumentGenerator
        
        # 转换配置格式
        llm_config_dict = {
            "provider": self.llm_config.provider,
            "model": self.llm_config.model,
            "api_key": self.llm_config.api_key,
            "base_url": self.llm_config.base_url,
            "temperature": self.llm_config.temperature,
            "max_tokens": self.llm_config.max_tokens
        }
        
        generator = DocumentGenerator(
            project_path=project_path,
            storage_path=storage_path,
            llm_config=llm_config_dict
        )
        
        return generator.generate_all()
    
    def update_docs(self, project_path: str, storage_path: str, changed_files: list) -> Dict:
        """
        更新文档
        
        Args:
            project_path: 项目根路径
            storage_path: 存储路径
            changed_files: 变更的文件列表
        
        Returns:
            更新统计信息
        """
        from codemind.generator import DocumentGenerator
        
        # 转换配置格式
        llm_config_dict = {
            "provider": self.llm_config.provider,
            "model": self.llm_config.model,
            "api_key": self.llm_config.api_key,
            "base_url": self.llm_config.base_url,
            "temperature": self.llm_config.temperature,
            "max_tokens": self.llm_config.max_tokens
        }
        
        generator = DocumentGenerator(
            project_path=project_path,
            storage_path=storage_path,
            llm_config=llm_config_dict
        )
        
        generator.incremental_update(changed_files)
        return {"updated_files": len(changed_files)}
