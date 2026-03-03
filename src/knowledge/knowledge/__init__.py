import os

from src.core.config import config
from .factory import KnowledgeBaseFactory
from .implementations.chroma import ChromaKB
from .manager import KnowledgeBaseManager

# 注册知识库类型
KnowledgeBaseFactory.register("chroma", ChromaKB, {"description": "基于 ChromaDB 的轻量级向量知识库，适合开发和小规模"})


# 创建知识库管理器
# 使用相对路径，避免硬编码绝对路径
save_dir = config.get("SAVE_DIR", None)
if save_dir is None or not os.path.isabs(save_dir):
    # 默认放在项目根目录下的 data 目录
    save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
work_dir = os.path.join(save_dir, "knowledge_base_data")
knowledge_base = KnowledgeBaseManager(work_dir)


__all__ = ["knowledge_base"]
