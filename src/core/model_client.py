"""
模型客户端 - 统一管理 LLM 和 Embedding 客户端创建
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from httpx import Timeout

from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo
from openai import OpenAI

from .config import config
from src.utils.log_utils import setup_logger

logger = setup_logger(__name__)


@dataclass
class TimeoutConfig:
    """API 调用超时配置"""
    connect: float = 60.0      # 连接超时（秒）
    read: float = 300.0        # 读取超时（秒）
    total: float = 600.0       # 总超时（秒）
    pool: float = 5.0          # 连接池超时（秒）

    def to_httpx_timeout(self) -> Timeout:
        """转换为 httpx Timeout 对象"""
        return Timeout(
            self.total,
            connect=self.connect,
            read=self.read,
            pool=self.pool
        )


# 预定义超时配置
TIMEOUT_CONFIGS = {
    'default': TimeoutConfig(connect=60.0, read=300.0, total=600.0),
    'quick': TimeoutConfig(connect=10.0, read=30.0, total=60.0),      # 快速操作
    'long': TimeoutConfig(connect=60.0, read=600.0, total=1200.0),    # 长文本处理
    'embedding': TimeoutConfig(connect=30.0, read=120.0, total=300.0), # Embedding 操作
}


@dataclass
class ModelCapabilities:
    """模型能力配置"""
    vision: bool = True
    function_calling: bool = True
    json_output: bool = True
    structured_output: bool = True

    def to_model_info(self, family: str) -> ModelInfo:
        """转换为 ModelInfo 对象"""
        return ModelInfo(
            vision=self.vision,
            function_calling=self.function_calling,
            json_output=self.json_output,
            family=family,
            structured_output=self.structured_output
        )


class ModelClientError(Exception):
    """模型客户端错误"""
    pass


class ModelClient:
    """OpenAIChatCompletionClient 的封装类，简化模型客户端的创建和配置"""

    # 模型家族映射
    FAMILY_MAP = {
        'siliconflow': 'Qwen',
        'openai': 'GPT',
        'dashscope': 'Qwen',
        'ark': 'Qwen',
    }

    @staticmethod
    def create_client(
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        capabilities: Optional[ModelCapabilities] = None,
        family: Optional[str] = None,
        timeout_config: Optional[TimeoutConfig] = None,
    ) -> OpenAIChatCompletionClient:
        """
        创建并返回一个配置好的 OpenAIChatCompletionClient 实例

        Args:
            provider: 模型提供商，如 'siliconflow', 'openai' 等
            model: 模型名称，如果为 None 则从配置中获取
            api_key: API 密钥，如果为 None 则从配置中获取
            base_url: API 基础 URL，如果为 None 则从配置中获取
            capabilities: 模型能力配置
            family: 模型家族名称
            timeout_config: 超时配置

        Returns:
            配置好的 OpenAIChatCompletionClient 实例

        Raises:
            ModelClientError: 配置无效时抛出
        """
        # 从配置加载默认值
        provider_config = config.get(provider) or {}

        # 填充缺失参数
        api_key = api_key or provider_config.get("api_key")
        base_url = base_url or provider_config.get("base_url")

        # 验证必要参数
        if not model:
            raise ModelClientError(
                f"未指定模型名称，请在参数中提供或在配置文件中设置 {provider}.model"
            )
        if not base_url:
            raise ModelClientError(
                f"未指定 API 基础 URL，请在参数中提供或在配置文件中设置 {provider}.base_url"
            )
        if not api_key:
            raise ModelClientError(
                f"未指定 API 密钥，请在参数中提供或在配置文件中设置 {provider}.api_key"
            )

        # 确定模型家族
        if family is None:
            family = ModelClient.FAMILY_MAP.get(provider, provider.capitalize())

        # 创建 ModelInfo
        capabilities = capabilities or ModelCapabilities()
        model_info = capabilities.to_model_info(family)

        # 创建超时配置
        timeout = (timeout_config or TIMEOUT_CONFIGS['default']).to_httpx_timeout()

        logger.debug(f"创建模型客户端: provider={provider}, model={model}, family={family}")

        return OpenAIChatCompletionClient(
            model=model,
            api_key=api_key,
            base_url=base_url,
            model_info=model_info,
            timeout=timeout
        )

    @staticmethod
    def create_embedding_client(
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_config: Optional[TimeoutConfig] = None,
    ) -> OpenAI:
        """
        创建 Embedding 客户端

        Args:
            provider: 模型提供商
            model: 模型名称
            api_key: API 密钥
            base_url: API 基础 URL
            timeout_config: 超时配置

        Returns:
            OpenAI 客户端实例
        """
        provider_config = config.get(provider) or {}

        api_key = api_key or provider_config.get("api_key")
        base_url = base_url or provider_config.get("base_url")

        if not model:
            raise ModelClientError(f"未指定 Embedding 模型名称")
        if not base_url:
            raise ModelClientError(f"未指定 API 基础 URL")
        if not api_key:
            raise ModelClientError(f"未指定 API 密钥")

        # Embedding 操作使用较短的超时
        timeout = (timeout_config or TIMEOUT_CONFIGS['embedding']).to_httpx_timeout()

        return OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            default_headers={"X-Model": model}
        )


def _apply_thinking_mode(
    client: OpenAIChatCompletionClient,
    enable_thinking: bool
) -> OpenAIChatCompletionClient:
    """
    为客户端开启深度思考模式

    适用于支持思考模式的模型，如 Qwen3/Qwen3.5 系列。
    开启后模型会先进行深度思考再给出回答，提升复杂任务的准确性。
    """
    try:
        # 注入 extra_body 到 create_args
        client._create_args["extra_body"] = {"enable_thinking": enable_thinking}
        if enable_thinking:
            logger.info("[完成] 已开启深度思考模式 (enable_thinking=True)")
    except AttributeError:
        logger.warning("无法设置思考模式，客户端不支持 _create_args 属性")
    return client


def create_model_client(
    client_type: str,
    fallback_to_default: bool = True
) -> OpenAIChatCompletionClient:
    """
    创建指定类型的模型客户端

    Args:
        client_type: 客户端类型，如 'search-model', 'reading-model' 等
        fallback_to_default: 配置缺失时是否回退到默认配置

    Returns:
        配置好的模型客户端
    """
    try:
        model_config = config.get(client_type, {})
        provider = model_config.get("model-provider")
        model = model_config.get("model")
        enable_thinking = model_config.get("enable_thinking", False)
        timeout_type = model_config.get("timeout", "default")

        if not provider or not model:
            if fallback_to_default:
                logger.warning(f"未配置 {client_type} 模型，使用默认模型代替")
                return create_default_client()
            raise ModelClientError(f"未配置 {client_type} 模型")

        # 根据任务类型选择超时配置
        timeout_config = TIMEOUT_CONFIGS.get(timeout_type, TIMEOUT_CONFIGS['default'])

        client = ModelClient.create_client(
            provider=provider,
            model=model,
            timeout_config=timeout_config
        )

        return _apply_thinking_mode(client, enable_thinking)

    except Exception as e:
        if fallback_to_default:
            logger.error(f"创建 {client_type} 模型客户端失败: {e}，使用默认模型代替")
            return create_default_client()
        raise ModelClientError(f"创建 {client_type} 模型客户端失败: {e}") from e


def create_embedding_client(client_type: str) -> OpenAI:
    """创建指定类型的 Embedding 客户端"""
    try:
        model_config = config.get(client_type, {})
        provider = model_config.get("model-provider")
        model = model_config.get("model")

        if not provider or not model:
            logger.warning(f"未配置 {client_type} 模型，使用默认模型代替")
            return create_default_embedding_client()

        return ModelClient.create_embedding_client(
            provider=provider,
            model=model,
            timeout_config=TIMEOUT_CONFIGS['embedding']
        )
    except Exception as e:
        logger.error(f"创建 {client_type} Embedding 客户端失败: {e}，使用默认模型代替")
        return create_default_embedding_client()


def create_default_client() -> OpenAIChatCompletionClient:
    """创建默认的模型客户端"""
    default_config = config.get("default-model", {})
    provider = default_config.get("model-provider", "siliconflow")
    model = default_config.get("model", "Qwen/Qwen3-32B")
    enable_thinking = default_config.get("enable_thinking", False)

    logger.info(f"使用默认模型配置: provider={provider}, model={model}, thinking={enable_thinking}")

    client = ModelClient.create_client(
        provider=provider,
        model=model,
        timeout_config=TIMEOUT_CONFIGS['default']
    )
    return _apply_thinking_mode(client, enable_thinking)


def create_default_embedding_client() -> OpenAI:
    """创建默认的 Embedding 客户端"""
    default_config = config.get("default-embedding-model", {})
    provider = default_config.get("model-provider", "siliconflow")
    model = default_config.get("model", "Qwen/Qwen3-Embedding-8B")

    return ModelClient.create_embedding_client(
        provider=provider,
        model=model,
        timeout_config=TIMEOUT_CONFIGS['embedding']
    )


# ========================================
# 便捷工厂函数
# ========================================

def create_search_model_client() -> OpenAIChatCompletionClient:
    """创建搜索模型客户端（快速响应）"""
    return create_model_client("search-model")


def create_reading_model_client() -> OpenAIChatCompletionClient:
    """创建阅读模型客户端（长文本处理）"""
    client = create_model_client("reading-model")
    # 阅读任务可能需要更长超时，重新配置
    return client


def create_subanalyse_cluster_model_client() -> OpenAIChatCompletionClient:
    """创建聚类分析模型客户端"""
    return create_model_client("subanalyse-cluster-model")


def create_subanalyse_deep_analyse_model_client() -> OpenAIChatCompletionClient:
    """创建深度分析模型客户端"""
    return create_model_client("subanalyse-deep-analyse-model")


def create_subanalyse_global_analyse_model_client() -> OpenAIChatCompletionClient:
    """创建全局分析模型客户端"""
    return create_model_client("subanalyse-global-analyse-model")


def create_subwriting_writing_director_model_client() -> OpenAIChatCompletionClient:
    """创建写作主管模型客户端"""
    return create_model_client("subwriting-writing-director-model")


def create_subwriting_writing_model_client() -> OpenAIChatCompletionClient:
    """创建写作模型客户端"""
    return create_model_client("subwriting-writing-model")


def create_subwriting_retrieval_model_client() -> OpenAIChatCompletionClient:
    """创建检索模型客户端"""
    return create_model_client("subwriting-retrieval-model")


def create_report_model_client() -> OpenAIChatCompletionClient:
    """创建报告生成模型客户端"""
    return create_model_client("report-model")


def create_cluster_embedding_client() -> OpenAI:
    """创建聚类 Embedding 客户端"""
    return create_embedding_client("cluster-embedding-model")
