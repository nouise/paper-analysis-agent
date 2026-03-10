"""
阅读节点: 论文列表 → LLM逐篇提取信息 → 结构化数据 + 存入知识库

流程:
  1. 从 search_results 获取论文列表
  2. 对每篇论文: 构造prompt → LLM提取 → ExtractedPaperData
  3. 验证提取结果非空
  4. 存入向量知识库供后续检索
  5. 返回 ExtractedPapersData
"""

import asyncio
import json
from typing import List, Dict, Any, Optional

from autogen_agentchat.agents import AssistantAgent

from src.core.model_client import create_reading_model_client
from src.core.state_models import (
    State, ExecutionState, BackToFrontData,
    ExtractedPaperData, ExtractedPapersData,
)
from src.core.config import config
from src.knowledge.knowledge import knowledge_base
from src.utils.log_utils import setup_logger
from src.utils.core_utils import (
    retry_with_backoff, RetryConfig,
    PaperProcessingError, get_metrics
)

logger = setup_logger(__name__)
metrics = get_metrics()


# ============================================================
# 常量配置
# ============================================================

class ReadingConfig:
    """阅读节点配置常量"""
    # 并发控制
    MAX_CONCURRENT_PAPERS = 2

    # 重试配置
    MAX_RETRIES = 2
    RETRY_DELAY_BASE = 2  # 秒
    RETRY_EXPONENTIAL_BASE = 2.0

    # 内容限制
    MAX_SUMMARY_LENGTH = 2000
    MAX_AUTHORS_DISPLAY = 5
    MAX_TITLE_LENGTH = 60

    # 超时
    OPERATION_TIMEOUT = 300.0  # 5分钟


# ============================================================
# Prompt 模板
# ============================================================

READING_PROMPT = """你是学术信息抽取专家。请根据用户提供的一篇论文信息，严格按照系统指定的 JSON Schema 输出结构化数据。

【抽取规则】
1. core_problem: 用"尽管…但…"或"为了…"句式概括核心研究问题。
2. key_methodology.name: 优先取原文中模型/算法/框架的名称。
3. key_methodology.principle: 用1-2句话描述技术路线。
4. key_methodology.novelty: 若原文有"首次""我们提出"等字样直接引用，否则写 null。
5. datasets_used: 列出数据集名称及规模（如 "SST-2 (67k sentences)"）。
6. evaluation_metrics: 仅保留主实验的指标。
7. main_results: 必须带数值和对照基线。
8. limitations: 通常出现在 Discussion 或 Conclusion 中。
9. contributions: 用3-5条短语列出。

【格式要求】
- 严格按照系统指定的 JSON Schema 输出，不添加任何解释。
- 信息缺失时用 null。
- 不要包裹在 ```json``` 中。
"""


# ============================================================
# 单篇论文处理
# ============================================================

async def _read_one_paper(
    paper: Dict[str, Any],
    index: int,
    total: int
) -> Optional[ExtractedPaperData]:
    """
    对单篇论文调用 LLM 提取结构化信息

    Args:
        paper: 论文元数据
        index: 当前论文索引
        total: 论文总数

    Returns:
        ExtractedPaperData 或 None（如果提取失败）
    """
    title = paper.get("title", "Unknown")[:ReadingConfig.MAX_TITLE_LENGTH]
    paper_id = paper.get("paper_id", f"unknown_{index}")

    print(f"[阅读] [{index + 1}/{total}] 正在阅读: {title}...")
    logger.debug(f"[Reading] 处理论文 {index + 1}/{total}: {paper_id}")

    # 精简传给 LLM 的内容
    simplified = {
        "paper_id": paper_id,
        "title": paper.get("title"),
        "authors": paper.get("authors", [])[:ReadingConfig.MAX_AUTHORS_DISPLAY],
        "summary": paper.get("summary", "")[:ReadingConfig.MAX_SUMMARY_LENGTH],
        "published_date": paper.get("published_date"),
        "url": paper.get("url"),
        "primary_category": paper.get("primary_category"),
    }

    # 每篇论文创建独立的 Agent 实例（避免状态污染）
    model_client = create_reading_model_client()
    read_agent = AssistantAgent(
        name=f"read_agent_{index}",
        model_client=model_client,
        system_message=READING_PROMPT,
        output_content_type=ExtractedPaperData,
    )

    async def do_read() -> ExtractedPaperData:
        """执行阅读（用于重试）"""
        result = await read_agent.run(task=str(simplified))
        parsed: ExtractedPaperData = result.messages[-1].content

        # 补充 paper_id 和 title
        if parsed.paper_id is None:
            parsed.paper_id = paper_id
        if parsed.title is None:
            parsed.title = paper.get("title")

        return parsed

    try:
        # 使用重试机制
        parsed = await retry_with_backoff(
            do_read,
            config=RetryConfig(
                max_attempts=ReadingConfig.MAX_RETRIES + 1,  # +1 因为 retry_with_backoff 的计数方式
                base_delay=ReadingConfig.RETRY_DELAY_BASE,
                exponential_base=ReadingConfig.RETRY_EXPONENTIAL_BASE,
                retryable_exceptions=(Exception,),
            )
        )

        # 验证提取结果非空
        if parsed.is_empty():
            logger.warning(f"[Reading] 论文 {paper_id} 提取结果为空")
            return None

        # 记录指标
        metrics.increment("papers_read_success")

        print(f"[完成] [{index + 1}/{total}] 阅读完成")
        return parsed

    except Exception as e:
        logger.error(f"[Reading] 论文 {paper_id} 提取失败: {e}")
        metrics.increment("papers_read_failed")
        return None


async def _process_papers_concurrent(
    papers: List[Dict],
    max_concurrent: int = ReadingConfig.MAX_CONCURRENT_PAPERS
) -> List[ExtractedPaperData]:
    """
    并发读取论文，用信号量控制并发数

    Args:
        papers: 论文列表
        max_concurrent: 最大并发数

    Returns:
        成功提取的论文数据列表
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    total = len(papers)

    async def _with_semaphore(paper: Dict, idx: int) -> Optional[ExtractedPaperData]:
        async with semaphore:
            return await _read_one_paper(paper, idx, total)

    tasks = [_with_semaphore(paper, i) for i, paper in enumerate(papers)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 过滤成功结果
    valid = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error(f"[Reading] 论文 {i + 1} 处理异常: {r}")
            metrics.increment("papers_read_error")
        elif r is not None:
            valid.append(r)

    return valid


# ============================================================
# 知识库存储
# ============================================================

async def _add_papers_to_kb(
    papers: List[Dict],
    extracted: ExtractedPapersData,
    state_queue: asyncio.Queue
) -> Optional[str]:
    """
    将提取的论文数据存入向量知识库

    Args:
        papers: 原始论文元数据
        extracted: 提取的论文数据
        state_queue: 状态队列（用于报告进度）

    Returns:
        知识库 ID 或 None（如果失败）
    """
    try:
        embedding_dic = config.get("embedding-model", {})
        embedding_provider = embedding_dic.get("model-provider")
        provider_dic = config.get(embedding_provider, {})

        if not provider_dic:
            logger.error(f"[Reading] 未找到 Embedding 提供商配置: {embedding_provider}")
            return None

        embed_info = {
            "name": embedding_dic.get("model"),
            "dimension": embedding_dic.get("dimension"),
            "base_url": provider_dic.get("base_url"),
            "api_key": provider_dic.get("api_key"),
        }

        kb_type = config.get("KB_TYPE", "chroma")

        # 创建临时知识库
        db_info = await knowledge_base.create_database(
            "临时知识库",
            "本次报告临时知识库",
            kb_type=kb_type,
            embed_info=embed_info,
            llm_info=None,
        )
        db_id = db_info.get("db_id")

        if not db_id:
            logger.error("[Reading] 创建知识库失败，未返回 db_id")
            return None

        config.set("tmp_db_id", db_id)

        # 准备文档数据
        documents = [
            json.dumps(p.model_dump(), ensure_ascii=False)
            for p in extracted.papers
        ]

        metadatas = []
        for paper in papers[:len(extracted.papers)]:
            metadatas.append({
                "paper_id": str(paper.get("paper_id", "")),
                "title": str(paper.get("title", "")),
                "published_date": str(paper.get("published_date", "")),
                "url": str(paper.get("url", "")),
                "primary_category": str(paper.get("primary_category", "")),
            })

        ids = [f"paper_{i}" for i in range(len(documents))]

        # 存入知识库
        await knowledge_base.add_processed_content(db_id, {
            "documents": documents,
            "metadatas": metadatas,
            "ids": ids,
        })

        logger.info(f"[Reading] 已将 {len(documents)} 篇论文存入知识库 {db_id}")
        metrics.increment("papers_added_to_kb", len(documents))

        return db_id

    except Exception as e:
        logger.error(f"[Reading] 存入知识库失败: {e}")
        return None


# ============================================================
# 阅读节点入口
# ============================================================

async def reading_node(state: State) -> State:
    """
    阅读节点: 论文列表 → LLM逐篇提取 → 结构化数据

    Args:
        state: LangGraph 状态

    Returns:
        更新后的状态
    """
    state_queue = state["state_queue"]
    current_state = state["value"]
    current_state.current_step = ExecutionState.READING

    await state_queue.put(BackToFrontData(
        step=ExecutionState.READING,
        state="initializing"
    ))

    # 记录指标
    with metrics.timer("reading_node_total"):
        try:
            papers = current_state.search_results or []

            if not papers:
                logger.warning("[Reading] 没有论文可供阅读")
                current_state.extracted_data = ExtractedPapersData(papers=[])
                await state_queue.put(BackToFrontData(
                    step=ExecutionState.READING,
                    state="completed",
                    data="没有论文可供阅读"
                ))
                return {"value": current_state}

            print(f"\n[书籍] 开始阅读 {len(papers)} 篇论文 (最多{ReadingConfig.MAX_CONCURRENT_PAPERS}篇并发)...\n")

            # 并发读取
            valid_papers = await _process_papers_concurrent(
                papers,
                max_concurrent=ReadingConfig.MAX_CONCURRENT_PAPERS
            )

            extracted = ExtractedPapersData(papers=valid_papers)

            success_count = len(valid_papers)
            fail_count = len(papers) - success_count

            print(f"\n[统计] 阅读统计: 成功 {success_count} 篇, 失败 {fail_count} 篇")
            logger.info(f"[Reading] 完成: 成功 {success_count}/{len(papers)}")

            # 存入知识库
            if valid_papers:
                await _add_papers_to_kb(papers, extracted, state_queue)

            current_state.extracted_data = extracted

            await state_queue.put(BackToFrontData(
                step=ExecutionState.READING,
                state="completed",
                data=f"论文阅读完成，成功提取 {success_count} 篇"
            ))

            return {"value": current_state}

        except Exception as e:
            err_msg = f"Reading failed: {e}"
            logger.error(f"[Reading] {err_msg}", exc_info=True)
            metrics.increment("reading_node_errors")

            current_state.error.reading_node_error = err_msg
            await state_queue.put(BackToFrontData(
                step=ExecutionState.READING,
                state="error",
                data=err_msg
            ))
            return {"value": current_state}
