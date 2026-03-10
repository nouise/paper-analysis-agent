"""
配置管理 - 支持验证和类型安全

使用 Pydantic 模型验证配置，确保关键配置项正确设置。
"""

import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator, ValidationError

from src.utils.log_utils import setup_logger

logger = setup_logger(__name__)


# ============================================================
# Pydantic 模型定义
# ============================================================

class Provider(str, Enum):
    """支持的模型提供商"""
    DASHSCOPE = "dashscope"
    SILICONFLOW = "siliconflow"
    OPENAI = "openai"
    ARK = "ark"


class ModelConfig(BaseModel):
    """模型配置"""
    model_provider: Provider = Field(..., alias="model-provider")
    model: str = Field(..., min_length=1)
    enable_thinking: bool = False
    timeout: str = "default"  # default/quick/long

    class Config:
        populate_by_name = True


class EmbeddingModelConfig(BaseModel):
    """Embedding 模型配置"""
    model_provider: Provider = Field(..., alias="model-provider")
    model: str = Field(..., min_length=1)
    dimension: int = Field(default=1024, gt=0)

    class Config:
        populate_by_name = True


class APIKeyConfig(BaseModel):
    """API 密钥配置"""
    api_key: str = Field(..., min_length=1)
    base_url: str = Field(..., min_length=1)


class KnowledgeBaseConfig(BaseModel):
    """知识库配置"""
    kb_type: str = Field(default="chroma", alias="KB_TYPE")
    save_dir: str = Field(default="./data", alias="SAVE_DIR")

    @validator('kb_type')
    def validate_kb_type(cls, v):
        allowed = {'chroma', 'milvus'}
        if v not in allowed:
            raise ValueError(f"不支持的知识库类型: {v}，可选: {allowed}")
        return v

    class Config:
        populate_by_name = True


class ValidatedConfig(BaseModel):
    """完整的验证后配置"""
    # 默认配置
    default_model: ModelConfig = Field(..., alias="default-model")
    default_embedding_model: EmbeddingModelConfig = Field(..., alias="default-embedding-model")

    # 知识库配置
    kb_config: KnowledgeBaseConfig

    # 提供商配置
    providers: Dict[Provider, APIKeyConfig]

    class Config:
        populate_by_name = True


# ============================================================
# 配置管理类
# ============================================================

class Config:
    """
    配置管理类（单例模式）

    功能:
    - 加载 .env 环境变量
    - 加载 YAML 配置文件
    - 支持 Pydantic 验证
    - 敏感信息过滤
    """

    _instance: Optional['Config'] = None
    _initialized: bool = False

    # 敏感键名（用于过滤）
    SENSITIVE_KEYS: Set[str] = {'api_key', 'password', 'secret', 'token', 'private_key'}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        logger.info("[Config] 初始化配置管理类")

        self._config: Dict[str, Any] = {}
        self._validated_config: Optional[ValidatedConfig] = None

        # 加载配置
        self._load_env()
        self._load_yaml_config()
        self._resolve_config_references()

        # 尝试验证（不强制，保持向后兼容）
        try:
            self._validate_config()
        except ValidationError as e:
            logger.warning(f"[Config] 配置验证警告: {e}")

        self._initialized = True
        logger.info("[Config] 配置加载完成")

    def _load_env(self) -> None:
        """加载 .env 文件中的环境变量"""
        env_path = Path(__file__).parent.parent.parent / ".env"

        if env_path.exists():
            load_dotenv(env_path)
            logger.debug(f"[Config] 加载环境变量: {env_path}")
        else:
            logger.warning(f"[Config] 未找到 .env 文件: {env_path}")

        # 将所有环境变量添加到配置
        for key, value in os.environ.items():
            self._config[key] = value

    def _load_yaml_config(self) -> None:
        """加载 YAML 配置文件"""
        yaml_files = [
            ("models.yaml", Path(__file__).parent / "models.yaml"),
            ("system_params.yaml", Path(__file__).parent / "system_params.yaml"),
        ]

        for name, path in yaml_files:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        yaml_config = yaml.safe_load(f)
                        if yaml_config:
                            self._merge_config(self._config, yaml_config)
                            logger.debug(f"[Config] 加载 YAML: {name}")
                except yaml.YAMLError as e:
                    logger.error(f"[Config] 解析 {name} 失败: {e}")
                except Exception as e:
                    logger.error(f"[Config] 加载 {name} 失败: {e}")
            else:
                logger.warning(f"[Config] 未找到 {name}")

    def _merge_config(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """深度合并配置字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_config(target[key], value)
            else:
                target[key] = value

    def _resolve_config_references(self) -> None:
        """解析配置中的环境变量引用"""
        try:
            providers = self._config.get('model-provider', [])
            if not isinstance(providers, list):
                providers = [providers]

            for provider in providers:
                provider_config = self._config.get(provider)
                if isinstance(provider_config, dict) and 'api_key' in provider_config:
                    api_key_ref = provider_config['api_key']
                    # 如果 api_key 是环境变量名，替换为实际值
                    if isinstance(api_key_ref, str) and api_key_ref in self._config:
                        provider_config['api_key'] = self._config[api_key_ref]
        except Exception as e:
            logger.warning(f"[Config] 解析配置引用时出错: {e}")

    def _validate_config(self) -> None:
        """使用 Pydantic 验证配置"""
        try:
            # 构建验证后的配置
            providers = {}
            for provider in Provider:
                config = self._config.get(provider.value, {})
                if config and 'api_key' in config and 'base_url' in config:
                    providers[provider] = APIKeyConfig(
                        api_key=config['api_key'],
                        base_url=config['base_url']
                    )

            self._validated_config = ValidatedConfig(
                default_model=self._config.get('default-model', {}),
                default_embedding_model=self._config.get('default-embedding-model', {}),
                kb_config={
                    'KB_TYPE': self._config.get('KB_TYPE', 'chroma'),
                    'SAVE_DIR': self._config.get('SAVE_DIR', './data'),
                },
                providers=providers
            )

            logger.info("[Config] 配置验证通过")

        except ValidationError as e:
            logger.error(f"[Config] 配置验证失败: {e}")
            raise

    # ============================================================
    # 公共 API
    # ============================================================

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持点表示法访问嵌套配置

        例如:
            config.get('siliconflow.api_key')
            config.get('default-model.model')
        """
        if '.' in key:
            keys = key.split('.')
            value = self._config
            for k in keys:
                if not isinstance(value, dict) or k not in value:
                    return default
                value = value[k]
            return value

        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置值，支持点表示法"""
        if '.' in key:
            keys = key.split('.')
            config = self._config
            for k in keys[:-1]:
                if k not in config or not isinstance(config[k], dict):
                    config[k] = {}
                config = config[k]
            config[keys[-1]] = value
        else:
            self._config[key] = value

    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔类型的配置值"""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1', 'y', 't', 'on')
        return bool(value)

    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数类型的配置值"""
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点数类型的配置值"""
        value = self.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_list(self, key: str, default: Optional[list] = None) -> list:
        """获取列表类型的配置值"""
        if default is None:
            default = []

        value = self.get(key, default)
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [item.strip() for item in value.split(',') if item.strip()]
        return default

    def get_required(self, key: str) -> Any:
        """获取必需的配置值，如果不存在则抛出异常"""
        value = self.get(key)
        if value is None:
            raise KeyError(f"必需的配置项缺失: {key}")
        return value

    def has(self, key: str) -> bool:
        """检查配置中是否包含指定的键"""
        return key in self

    def __contains__(self, key: str) -> bool:
        """检查配置中是否包含指定的键"""
        if '.' in key:
            keys = key.split('.')
            value = self._config
            for k in keys:
                if not isinstance(value, dict) or k not in value:
                    return False
                value = value[k]
            return True

        return key in self._config

    def __getitem__(self, key: str) -> Any:
        """支持字典风格的配置访问"""
        if '.' in key:
            return self.get(key)
        return self._config[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """支持字典风格的配置设置"""
        self.set(key, value)

    def __str__(self) -> str:
        """返回配置的字符串表示（过滤敏感信息）"""
        filtered = self._filter_sensitive_info(self._config.copy())
        return yaml.dump(filtered, allow_unicode=True, default_flow_style=False)

    def _filter_sensitive_info(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """过滤配置中的敏感信息"""
        for key, value in config.items():
            if isinstance(value, dict):
                config[key] = self._filter_sensitive_info(value)
            elif any(s in key.lower() for s in self.SENSITIVE_KEYS):
                config[key] = '****'
        return config

    def to_dict(self) -> Dict[str, Any]:
        """返回原始配置字典的副本（过滤敏感信息）"""
        return self._filter_sensitive_info(self._config.copy())


# ============================================================
# 全局实例
# ============================================================

config = Config()


# 测试入口
if __name__ == "__main__":
    print("配置内容:")
    print(config)
    print(f"\nKB_TYPE: {config.get('KB_TYPE')}")
    print(f"包含 default-model: {'default-model' in config}")
