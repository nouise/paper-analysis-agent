"""
主运行脚本 - 面试讲解演示
可以运行所有模块或指定模块

用法:
  python run_demos.py           # 运行所有模块
  python run_demos.py 1         # 运行模块 1 (基础设施)
  python run_demos.py 2         # 运行模块 2 (数据层)
  python run_demos.py 3         # 运行模块 3 (LangGraph)
  python run_demos.py 4         # 运行模块 4 (AutoGen)
  python run_demos.py list      # 列出所有模块
"""

import sys
import subprocess
from pathlib import Path

# 模块定义
MODULES = {
    1: ("基础设施层", "demo_module_01_core.py", "配置系统 + 模型客户端 + 状态管理"),
    2: ("数据层", "demo_module_02_data.py", "论文搜索 + 知识库 + 文档解析"),
    3: ("工作流层", "demo_module_03_orchestrator.py", "LangGraph 工作流编排"),
    4: ("代理层", "demo_module_04_autogen.py", "AutoGen 多代理系统"),
}


def list_modules():
    """列出所有模块"""
    print("=" * 60)
    print("可用模块列表")
    print("=" * 60)
    for num, (name, file, desc) in MODULES.items():
        print(f"\n模块 {num}: {name}")
        print(f"  文件: {file}")
        print(f"  内容: {desc}")
    print("\n" + "=" * 60)


def run_module(module_num: int):
    """运行指定模块"""
    if module_num not in MODULES:
        print(f"❌ 模块 {module_num} 不存在")
        list_modules()
        return False

    name, file, desc = MODULES[module_num]
    demo_path = Path(__file__).parent / file

    if not demo_path.exists():
        print(f"❌ 文件不存在: {demo_path}")
        return False

    print(f"\n🚀 运行模块 {module_num}: {name}")
    print(f"   {desc}")
    print("=" * 60)

    result = subprocess.run([sys.executable, str(demo_path)])
    return result.returncode == 0


def run_all():
    """运行所有模块"""
    print("\n" + "=" * 60)
    print("🎯 Paper Analysis Agent - 面试讲解演示")
    print("=" * 60)

    results = {}
    for num in sorted(MODULES.keys()):
        success = run_module(num)
        results[num] = success

        if num < max(MODULES.keys()):
            input("\n按 Enter 键继续到下一个模块...")

    # 总结
    print("\n" + "=" * 60)
    print("📊 运行总结")
    print("=" * 60)
    for num, success in results.items():
        name = MODULES[num][0]
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  模块 {num} ({name}): {status}")

    all_success = all(results.values())
    print("\n" + ("🎉 所有模块运行成功!" if all_success else "⚠️  部分模块运行失败"))
    return all_success


def main():
    """主函数"""
    if len(sys.argv) < 2:
        # 无参数，运行所有模块
        return run_all()

    command = sys.argv[1].lower()

    if command == "list":
        list_modules()
        return True

    if command.isdigit():
        module_num = int(command)
        return run_module(module_num)

    if command == "all":
        return run_all()

    print(f"❌ 未知命令: {command}")
    print("\n用法:")
    print("  python run_demos.py           # 运行所有模块")
    print("  python run_demos.py 1         # 运行模块 1")
    print("  python run_demos.py list      # 列出所有模块")
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
