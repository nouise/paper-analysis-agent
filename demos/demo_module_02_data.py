"""
模块 2: 论文搜索 + 知识库系统演示
可以独立运行，展示数据获取和存储能力
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def demo_paper_search():
    """演示论文搜索模块"""
    print("=" * 60)
    print("模块 2.1: 论文搜索 (tasks/paper_search.py)")
    print("=" * 60)

    from src.tasks.paper_search import PaperSearcher

    searcher = PaperSearcher()

    # 演示日期格式化
    print("\n📅 日期格式化功能:")
    test_dates = ["2024-01-15", "2024/03/20", "2023", "2024年5月"]
    for date in test_dates:
        formatted = searcher._format_date(date)
        print(f"  '{date}' -> '{formatted}'")

    # 演示搜索 (需要网络)
    print("\n🔍 论文搜索示例 (使用测试关键词 'transformer')...")
    print("  注意: 需要网络连接和 arXiv API 可用")

    try:
        results = await searcher.search_papers(
            querys=["transformer"],
            max_results=3,
            start_date="2024-01-01"
        )

        print(f"\n  ✓ 找到 {len(results)} 篇论文")

        for i, paper in enumerate(results[:2], 1):
            print(f"\n  论文 {i}:")
            print(f"    ID: {paper.get('paper_id')}")
            print(f"    标题: {paper.get('title', 'N/A')[:60]}...")
            print(f"    作者: {', '.join(paper.get('authors', [])[:2])}")
            print(f"    年份: {paper.get('published')}")

    except Exception as e:
        print(f"  ⚠️  搜索失败 (可能是网络问题): {e}")

    print("\n✅ 论文搜索演示完成")
    return True


async def demo_knowledge_base():
    """演示知识库系统"""
    print("\n" + "=" * 60)
    print("模块 2.2: 知识库系统 (knowledge/)")
    print("=" * 60)

    from src.knowledge.knowledge import knowledge_base
    from src.knowledge.knowledge.factory import KnowledgeBaseFactory

    # 展示知识库管理器信息
    print("\n📚 知识库管理器信息:")
    stats = knowledge_base.get_statistics()
    print(f"  总数据库数: {stats.get('total_databases', 0)}")
    print(f"  总文件数: {stats.get('total_files', 0)}")
    print(f"  知识库类型: {list(stats.get('kb_types', {}).keys())}")

    # 展示支持的知识库类型
    print("\n🏷️  支持的知识库类型:")
    kb_types = knowledge_base.get_supported_kb_types()
    for kb_type, info in kb_types.items():
        print(f"  - {kb_type}: {info.get('description', 'N/A')}")

    # 展示实例信息
    print("\n📦 知识库实例信息:")
    instance_info = knowledge_base.get_kb_instance_info()
    for kb_type, info in instance_info.items():
        print(f"  {kb_type}:")
        print(f"    工作目录: {info.get('work_dir', 'N/A')}")
        print(f"    数据库数: {info.get('database_count', 0)}")
        print(f"    文件数: {info.get('file_count', 0)}")

    # 展示所有数据库
    print("\n📂 现有数据库列表:")
    databases = knowledge_base.get_databases()
    db_list = databases.get('databases', [])
    if db_list:
        for db in db_list[:5]:  # 只显示前5个
            print(f"  - {db.get('name')} (ID: {db.get('id', 'N/A')[:8]}...)")
    else:
        print("  (暂无数据库)")

    print("\n✅ 知识库系统演示完成")
    return True


async def demo_parsers():
    """演示文档解析系统"""
    print("\n" + "=" * 60)
    print("模块 2.3: 文档解析 (parsers/)")
    print("=" * 60)

    from src.parsers.factory import ParserFactory

    # 展示支持的文件类型
    print("\n📄 支持的文件类型:")
    supported = ParserFactory.get_supported_extensions()
    for ext, parser_type in supported.items():
        print(f"  {ext} -> {parser_type}")

    # 测试解析器创建
    print("\n🔧 解析器工厂测试:")
    test_files = ["test.pdf", "test.docx", "test.md", "test.txt", "test.unknown"]
    for filename in test_files:
        is_supported = ParserFactory.is_supported(filename)
        status = "✓ 支持" if is_supported else "✗ 不支持"
        print(f"  {filename}: {status}")

    print("\n✅ 文档解析演示完成")
    return True


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("模块 2: 数据层演示")
    print("=" * 60)
    print("\n包含:")
    print("  - 论文搜索 (tasks/paper_search.py)")
    print("  - 知识库系统 (knowledge/)")
    print("  - 文档解析 (parsers/)")

    try:
        await demo_paper_search()
        await demo_knowledge_base()
        await demo_parsers()

        print("\n" + "=" * 60)
        print("✅ 模块 2 演示全部完成!")
        print("=" * 60)

        print("\n💡 面试要点:")
        print("  1. 论文搜索使用 arXiv API，支持日期范围和多格式日期")
        print("  2. 知识库使用工厂模式管理多种类型 (ChromaDB等)")
        print("  3. 全局元数据统一管理所有知识库")
        print("  4. 文档解析使用工厂模式，统一接口")
        print("  5. 所有操作都是异步的")

        return True

    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
