"""
阅读节点: 论文列表 → LLM逐篇提取信息 → 结构化数据 + 存入知识库

流程:
  1. 从 search_results 获取论文列表
  2. 对每篇论文: 构造prompt → LLM提取 → ExtractedPaperData
  3. 验证提取结果非空
  4. 存入向量知识库供后续检索
  5. 返回 ExtractedPapersData

关键修复:
  - 每篇论文单独创建 Agent（避免共享状态污染）
  - prompt 与 output_content_type 统一为单篇论文格式
  - 提取后验证数据非空
"""

import asyncio
import json
from typing import List, Dict, Any, Optional

from autogen_agentchat.agents import AssistantAgent

from src.core.model_client import create_reading_model_client
from src.core.state_models import (
    State, ExecutionState, BackToFrontData,
    ExtractedPaperData, ExtractedPapersData, KeyMethodology,
)
from src.core.config import config
from src.knowledge.knowledge import knowledge_base
from src.utils.log_utils import setup_logger

logger = setup_logger(__name__)


# ============================================================
# 阅读 prompt — 针对单篇论文，与 output_content_type 一致
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

async def _read_one_paper(paper: Dict[str, Any], index: int, total: int) -> Optional[ExtractedPaperData]:
    """对单篇论文调用 LLM 提取结构化信息"""
    title = paper.get("title", "Unknown")[:60]
    print(f"📖 [{index + 1}/{total}] 正在阅读: {title}...")

    # 精简传给 LLM 的内容
    simplified = {
        "paper_id": paper.get("paper_id"),
        "title": paper.get("title"),
        "authors": paper.get("authors", [])[:5],
        "summary": paper.get("summary", "")[:2000],
        "published_date": paper.get("published_date"),
        "url": paper.get("url"),
        "primary_category": paper.get("primary_category"),
    }

    # 每篇论文创建独立的 Agent 实例（避免状态污染）
    model_client = create_reading_model_client()
    read_agent = AssistantAgent(
        name="read_agent",
        model_client=model_client,
        system_message=READING_PROMPT,
        output_content_type=ExtractedPaperData,  # 单篇论文格式
    )

    max_retries = 2
    for attempt in range(max_retries):
        try:
            result = await read_agent.run(task=str(simplified))
            parsed: ExtractedPaperData = result.messages[-1].content

            # 补充 paper_id 和 title
            if parsed.paper_id is None:
                parsed.paper_id = paper.get("paper_id")
            if parsed.title is None:
                parsed.title = paper.get("title")

            # 验证提取结果非空
            if parsed.is_empty():
                logger.warning(f"[{index + 1}/{total}] 论文提取结果为空，尝试重试...")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
                else:
                    logger.error(f"[{index + 1}/{total}] 论文提取结果为空，放弃")
                    return None

            print(f"✅ [{index + 1}/{total}] 阅读完成: {parsed.core_problem[:50] if parsed.core_problem else 'N/A'}...")
            return parsed

        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"[{index + 1}/{total}] 第 {attempt + 1} 次尝试失败: {e}, 重试中...")
                await asyncio.sleep(2 ** attempt)
            else:
                logger.error(f"[{index + 1}/{total}] 所有尝试失败: {e}")
                return None

    return None


async def _process_papers_concurrent(papers: List[Dict], max_concurrent: int = 2) -> List[ExtractedPaperData]:
    """并发读取论文，用信号量控制并发数"""
    semaphore = asyncio.Semaphore(max_concurrent)
    total = len(papers)

    async def _with_semaphore(paper, idx):
        async with semaphore:
            return await _read_one_paper(paper, idx, total)

    tasks = [_with_semaphore(paper, i) for i, paper in enumerate(papers)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 过滤成功结果
    valid = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error(f"论文 {i + 1} 处理异常: {r}")
        elif r is not None:
            valid.append(r)
    return valid


# ============================================================
# 存入知识库
# ============================================================

async def _add_papers_to_kb(papers: List[Dict], extracted: ExtractedPapersData):
    """将提取的论文数据存入向量知识库"""
    try:
        embedding_dic = config.get("embedding-model", {})
        embedding_provider = embedding_dic.get("model-provider")
        provider_dic = config.get(embedding_provider, {})

        embed_info = {
            "name": embedding_dic.get("model"),
            "dimension": embedding_dic.get("dimension"),
            "base_url": provider_dic.get("base_url"),
            "api_key": provider_dic.get("api_key"),
        }

        kb_type = config.get("KB_TYPE", "chroma")
        db_info = await knowledge_base.create_database(
            "临时知识库", "本次报告临时知识库", kb_type=kb_type, embed_info=embed_info, llm_info=None,
        )
        db_id = db_info["db_id"]
        config.set("tmp_db_id", db_id)

        documents = [json.dumps(p.model_dump(), ensure_ascii=False) for p in extracted.papers]
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

        await knowledge_base.add_processed_content(db_id, {
            "documents": documents,
            "metadatas": metadatas,
            "ids": ids,
        })
        logger.info(f"已将 {len(documents)} 篇论文存入知识库 {db_id}")

    except Exception as e:
        logger.error(f"存入知识库失败: {e}")


# ============================================================
# 阅读节点
# ============================================================

async def reading_node(state: State) -> State:
    """阅读节点: 论文列表 → LLM逐篇提取 → 结构化数据"""
    state_queue = state["state_queue"]
    current_state = state["value"]
    current_state.current_step = ExecutionState.READING
    await state_queue.put(BackToFrontData(step=ExecutionState.READING, state="initializing"))

    try:
        papers = current_state.search_results or []
        if not papers:
            logger.warning("没有论文可供阅读")
            current_state.extracted_data = ExtractedPapersData(papers=[])
            await state_queue.put(BackToFrontData(step=ExecutionState.READING, state="completed", data="没有论文可供阅读"))
            return {"value": current_state}

        print(f"\n📚 开始阅读 {len(papers)} 篇论文 (最多2篇并发)...\n")

        # 并发读取
        valid_papers = await _process_papers_concurrent(papers, max_concurrent=2)

        extracted = ExtractedPapersData(papers=valid_papers)
        print(f"\n📊 阅读统计: 成功 {len(valid_papers)} 篇, 失败 {len(papers) - len(valid_papers)} 篇")

        # 存入知识库
        if valid_papers:
            await _add_papers_to_kb(papers, extracted)

        current_state.extracted_data = extracted
        await state_queue.put(BackToFrontData(
            step=ExecutionState.READING, state="completed",
            data=f"论文阅读完成，成功提取 {len(valid_papers)} 篇"
        ))
        return {"value": current_state}

    except Exception as e:
        err_msg = f"Reading failed: {e}"
        logger.error(err_msg)
        current_state.error.reading_node_error = err_msg
        await state_queue.put(BackToFrontData(step=ExecutionState.READING, state="error", data=err_msg))
        return {"value": current_state}
