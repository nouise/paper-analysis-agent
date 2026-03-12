"""
Paper-Agent 统一数据模型 (Single Source of Truth)
所有节点共享同一套数据结构，避免重复定义导致的类型混乱
"""

from asyncio import Queue
from typing import List, Dict, Any, Optional, TypedDict
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# ============================================================
# 执行状态
# ============================================================

class ExecutionState(str, Enum):
    """工作流执行状态"""
    INITIALIZING = "initializing"
    SEARCHING = "searching"
    READING = "reading"
    ANALYZING = "analyzing"
    WRITING = "writing"
    WRITING_DIRECTOR = "writing_director"
    SECTION_WRITING = "section_writing"
    REPORTING = "reporting"
    COMPLETED = "completed"
    FAILED = "failed"
    FINISHED = "finished"


# ============================================================
# 前后端通信
# ============================================================

class BackToFrontData(BaseModel):
    """SSE 前后端通信数据结构"""
    step: str = Field(description="环节名称")
    state: str = Field(description="环节状态")
    data: Any = Field(default=None, description="原始数据（向后兼容）")
    # 新增字段用于折叠面板展示
    summary: Optional[str] = Field(default=None, description="环节摘要")
    detail: Optional[str] = Field(default=None, description="详细内容")
    stream_content: Optional[str] = Field(default=None, description="流式输出内容片段")
    progress: int = Field(default=0, description="进度百分比 (0-100)")
    collapsible: bool = Field(default=True, description="是否可折叠")
    default_collapsed: bool = Field(default=False, description="默认是否折叠")


# ============================================================
# 论文数据结构 — 唯一定义
# ============================================================

class KeyMethodology(BaseModel):
    """论文关键方法"""
    name: Optional[str] = Field(default=None, description="方法名称")
    principle: Optional[str] = Field(default=None, description="核心原理")
    novelty: Optional[str] = Field(default=None, description="创新点")


class ExtractedPaperData(BaseModel):
    """单篇论文的提取结果"""
    paper_id: Optional[str] = Field(default=None, description="论文ID")
    title: Optional[str] = Field(default=None, description="论文标题")
    core_problem: Optional[str] = Field(default=None, description="核心问题")
    key_methodology: Optional[KeyMethodology] = Field(default=None, description="关键方法")
    datasets_used: Optional[List[str]] = Field(default=None, description="使用的数据集")
    evaluation_metrics: Optional[List[str]] = Field(default=None, description="评估指标")
    main_results: Optional[str] = Field(default=None, description="主要结果")
    limitations: Optional[str] = Field(default=None, description="局限性")
    contributions: Optional[List[str]] = Field(default=None, description="贡献")

    @field_validator('datasets_used', 'evaluation_metrics', 'contributions', mode='before')
    @classmethod
    def convert_none_to_empty_list(cls, v):
        """将 None 转换为空列表"""
        return v if v is not None else []

    def is_empty(self) -> bool:
        """检查提取结果是否为空（所有关键字段都缺失）"""
        return (
            self.core_problem is None
            and self.key_methodology is None
            and self.main_results is None
            and len(self.contributions or []) == 0
        )


class ExtractedPapersData(BaseModel):
    """所有论文的提取结果集合"""
    papers: List[ExtractedPaperData] = Field(default_factory=list, description="提取的论文数据列表")


# ============================================================
# 错误信息
# ============================================================

class NodeError(BaseModel):
    search_node_error: Optional[str] = Field(default=None)
    reading_node_error: Optional[str] = Field(default=None)
    analyse_node_error: Optional[str] = Field(default=None)
    writing_node_error: Optional[str] = Field(default=None)
    report_node_error: Optional[str] = Field(default=None)


# ============================================================
# 全局工作流状态
# ============================================================

class PaperAgentState(BaseModel):
    """工作流全局状态"""
    # 用户输入
    user_request: str = Field(description="用户的原始查询")
    max_papers: int = Field(default=10, description="最大论文数量")

    # 执行状态
    current_step: ExecutionState = Field(default=ExecutionState.INITIALIZING)
    error: NodeError = Field(default_factory=NodeError)

    # 各节点的数据 — 按流水线顺序填充
    search_results: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="搜索到的论文元数据")
    extracted_data: Optional[ExtractedPapersData] = Field(default=None, description="阅读提取的结构化数据")
    analyse_results: Optional[str] = Field(default=None, description="分析结果(JSON)")
    writted_sections: Optional[List[str]] = Field(default=None, description="写作完成的章节列表")
    report_markdown: Optional[str] = Field(default=None, description="最终Markdown报告")

    # 配置
    config: Dict[str, Any] = Field(default_factory=dict)


# ============================================================
# LangGraph 兼容状态
# ============================================================

class State(TypedDict):
    """LangGraph 兼容的状态定义"""
    state_queue: Queue
    value: PaperAgentState


class ConfigSchema(TypedDict):
    """LangGraph 兼容的配置定义"""
    state_queue: Queue
    value: Dict[str, Any]
