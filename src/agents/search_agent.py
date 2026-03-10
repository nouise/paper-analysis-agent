"""
搜索代理 - 已迁移到 src/nodes/search.py

此文件保留用于向后兼容的导入，实际实现已移至 nodes 模块。

使用方式:
    from src.nodes.search import search_node
"""

# 向后兼容导入
from src.nodes.search import search_node, SearchQuery

__all__ = ['search_node', 'SearchQuery']
