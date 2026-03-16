"""
模块 1: 配置系统 + 模型客户端演示
可以独立运行，展示项目的配置管理和模型初始化能力
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def demo_config():
    """演示配置系统"""
    print("=" * 60)
    print("模块 1.1: 配置系统 (core/config.py)")
    print("=" * 60)

    from src.core.config import config

    # 展示配置访问能力
    print("\n📋 配置访问示例:")
    print(f"  KB_TYPE: {config.get('KB_TYPE', 'chroma')}")
    print(f"  SAVE_DIR: {config.get('SAVE_DIR', './data')}")

    # 展示嵌套配置访问
    print("\n📋 嵌套配置访问 (点表示法):")
    default_model = config.get('default-model', {})
    if default_model:
        print(f"  default-model.model-provider: {default_model.get('model-provider', 'N/A')}")
        print(f"  default-model.model: {default_model.get('model', 'N/A')}")
    else:
        print("  (未配置 default-model)")

    # 展示类型转换
    print("\n📋 类型安全访问:")
    print(f"  get_bool example: {config.get_bool('SOME_BOOL', True)}")
    print(f"  get_int example: {config.get_int('SOME_INT', 42)}")

    # 展示敏感信息过滤
    print("\n📋 敏感信息过滤:")
    config_str = str(config)
    if '****' in config_str:
        print("  ✓ 配置输出中敏感信息已自动过滤")
    else:
        print("  (当前配置中无敏感信息)")

    print("\n✅ 配置系统演示完成")
    return True


async def demo_model_client():
    """演示模型客户端"""
    print("\n" + "=" * 60)
    print("模块 1.2: 模型客户端 (core/model_client.py)")
    print("=" * 60)

    from src.core.model_client import (
        ModelClient,
        TimeoutConfig,
        TIMEOUT_CONFIGS,
        create_default_client
    )

    # 展示超时配置
    print("\n⏱️  预定义超时配置:")
    for name, timeout in TIMEOUT_CONFIGS.items():
        print(f"  {name}: connect={timeout.connect}s, read={timeout.read}s, total={timeout.total}s")

    # 展示模型家族映射
    print("\n🏷️  模型家族映射:")
    for provider, family in ModelClient.FAMILY_MAP.items():
        print(f"  {provider} -> {family}")

    # 尝试创建默认客户端
    print("\n🤖 尝试创建默认模型客户端...")
    try:
        client = create_default_client()
        print(f"  ✓ 客户端创建成功")
        print(f"  模型: {client._model}")
        print(f"  基础URL: {client._base_url}")
    except Exception as e:
        print(f"  ⚠️  客户端创建失败 (正常，可能未配置API密钥): {e}")

    print("\n✅ 模型客户端演示完成")
    return True


def demo_state_models():
    """演示状态模型"""
    print("\n" + "=" * 60)
    print("模块 1.3: 状态管理 (core/state_models.py)")
    print("=" * 60)

    from src.core.state_models import (
        ExecutionState,
        PaperAgentState,
        BackToFrontData,
        NodeError,
        ExtractedPaperData
    )

    # 展示执行状态枚举
    print("\n📊 工作流执行状态:")
    for state in ExecutionState:
        print(f"  - {state.value}")

    # 创建示例状态
    print("\n📋 创建工作流状态实例:")
    state = PaperAgentState(
        user_request="分析大语言模型在医学领域的应用",
        max_papers=10
    )
    print(f"  用户请求: {state.user_request}")
    print(f"  最大论文数: {state.max_papers}")
    print(f"  当前步骤: {state.current_step.value}")

    # 展示前后端通信数据
    print("\n📡 SSE 通信数据结构:")
    sse_data = BackToFrontData(
        step="searching",
        state="completed",
        summary="找到 10 篇论文",
        detail="使用关键词: LLM, medical",
        progress=100
    )
    print(f"  步骤: {sse_data.step}")
    print(f"  状态: {sse_data.state}")
    print(f"  摘要: {sse_data.summary}")
    print(f"  进度: {sse_data.progress}%")

    # 展示错误模型
    print("\n⚠️  错误处理模型:")
    error = NodeError()
    print(f"  是否有错误: {any([error.search_node_error, error.reading_node_error])}")

    print("\n✅ 状态管理演示完成")
    return True


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("模块 1: 基础设施层演示")
    print("=" * 60)
    print("\n包含:")
    print("  - 配置系统 (core/config.py)")
    print("  - 模型客户端 (core/model_client.py)")
    print("  - 状态管理 (core/state_models.py)")

    try:
        # 运行各个演示
        demo_config()
        await demo_model_client()
        demo_state_models()

        print("\n" + "=" * 60)
        print("✅ 模块 1 演示全部完成!")
        print("=" * 60)

        print("\n💡 面试要点:")
        print("  1. 配置系统使用单例模式 + Pydantic 验证")
        print("  2. 支持点表示法访问嵌套配置")
        print("  3. 模型客户端统一管理多提供商 LLM")
        print("  4. 状态模型定义工作流数据结构")
        print("  5. SSE 格式实现前后端实时通信")

        return True

    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
