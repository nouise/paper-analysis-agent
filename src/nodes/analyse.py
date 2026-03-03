"""
分析节点: 提取数据 → 聚类 → 深度分析 → 全局分析

流程:
  1. 接收 ExtractedPapersData
  2. Embedding + KMeans 聚类
  3. 每个聚类并行深度分析
  4. 全局分析汇总
  5. 返回分析结果 JSON
"""

import asyncio
import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult

from src.core.model_client import (
    create_subanalyse_cluster_model_client,
    create_subanalyse_deep_analyse_model_client,
    create_subanalyse_global_analyse_model_client,
    create_cluster_embedding_client,
)
from src.core.prompts import clustering_agent_prompt, deep_analyse_agent_prompt, global_analyse_agent_prompt
from src.core.state_models import (
    State, ExecutionState, BackToFrontData,
    ExtractedPapersData,
)
from src.utils.log_utils import setup_logger

logger = setup_logger(__name__)


# ============================================================
# 数据结构
# ============================================================

@dataclass
class PaperCluster:
    """聚类结果"""
    cluster_id: int
    papers: List[Dict[str, Any]]
    theme: str = ""
    keywords: List[str] = field(default_factory=list)


@dataclass
class DeepAnalyseResult:
    """深度分析结果"""
    cluster_id: int
    theme: str
    keywords: List[str]
    paper_count: int
    deep_analyse: str
    papers: List[Dict[str, Any]]


# ============================================================
# 1. 聚类
# ============================================================

def _get_embedding(texts: List[str]) -> np.ndarray:
    """调用 embedding API 获取向量"""
    client = create_cluster_embedding_client()
    response = client.embeddings.create(
        model=client.default_headers["X-Model"],
        input=texts,
        dimensions=1024,
    )
    return np.array([item.embedding for item in response.data])


def _prepare_text(paper: Dict[str, Any]) -> str:
    """将论文数据转为适合 embedding 的文本"""
    parts = []
    if paper.get("core_problem"):
        parts.append(f"Problem: {paper['core_problem']}")
    if paper.get("key_methodology"):
        m = paper["key_methodology"]
        parts.append(f"Method: {m.get('name', '')} - {m.get('principle', '')}")
    if paper.get("main_results"):
        parts.append(f"Results: {paper['main_results']}")
    if paper.get("contributions"):
        parts.append(f"Contributions: {'; '.join(paper['contributions'])}")
    return " ".join(parts) if parts else "No information available"


def _cluster_papers(papers: List[Dict[str, Any]]) -> List[PaperCluster]:
    """对论文进行 KMeans 聚类"""
    if len(papers) <= 2:
        return [PaperCluster(cluster_id=0, papers=papers)]

    texts = [_prepare_text(p) for p in papers]
    embeddings = _get_embedding(texts)

    # 确定聚类数
    from sklearn.cluster import KMeans
    max_k = min(5, len(papers) - 1)
    if max_k <= 1:
        return [PaperCluster(cluster_id=0, papers=papers)]

    # 简单肘部法则
    inertias = []
    for k in range(1, max_k + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(embeddings)
        inertias.append(km.inertia_)

    if len(inertias) >= 3:
        diffs = [inertias[i - 1] - inertias[i] for i in range(1, len(inertias))]
        n_clusters = diffs.index(max(diffs)) + 2
        n_clusters = min(n_clusters, max_k)
    else:
        n_clusters = min(2, max_k)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(embeddings)

    clusters = []
    for cid in range(n_clusters):
        c_papers = [papers[i] for i, l in enumerate(labels) if l == cid]
        if c_papers:
            clusters.append(PaperCluster(cluster_id=cid, papers=c_papers))
    return clusters


async def _generate_cluster_theme(cluster: PaperCluster) -> Tuple[str, List[str]]:
    """用 LLM 为聚类生成主题和关键词"""
    try:
        summaries = []
        for p in cluster.papers[:3]:
            summaries.append({
                "problem": p.get("core_problem", ""),
                "method": (p.get("key_methodology") or {}).get("name", ""),
                "results": p.get("main_results", ""),
            })

        model_client = create_subanalyse_cluster_model_client()
        agent = AssistantAgent(
            name="cluster_theme_agent",
            model_client=model_client,
            system_message=clustering_agent_prompt,
        )

        prompt = f"""基于以下论文信息，生成主题描述和关键词：
论文信息：{json.dumps(summaries, ensure_ascii=False, indent=2)}
格式：
主题描述：[主题描述]
关键词：[关键词1, 关键词2, 关键词3]"""

        response = await agent.run(task=prompt)
        text = response.messages[-1].content

        import re
        theme_match = re.search(r'主题描述\s*[:：]\s*\[?([^\]\n]+)', text)
        kw_match = re.search(r'关键词\s*[:：]\s*\[?([^\]\n]+)', text)

        theme = theme_match.group(1).strip().strip('"\'[]') if theme_match else "未分类研究主题"
        keywords = []
        if kw_match:
            kw_str = kw_match.group(1).strip().strip('[]')
            for sep in [',', '，', ';', '；']:
                if sep in kw_str:
                    keywords = [k.strip().strip('"\'') for k in kw_str.split(sep) if k.strip()]
                    break
            if not keywords:
                keywords = [kw_str.strip()]
        return theme, keywords[:5]
    except Exception as e:
        logger.error(f"生成聚类主题失败: {e}")
        return "未分类研究主题", ["research"]


# ============================================================
# 2. 深度分析
# ============================================================

async def _deep_analyse_cluster(cluster: PaperCluster) -> DeepAnalyseResult:
    """对单个聚类进行深度分析"""
    try:
        model_client = create_subanalyse_deep_analyse_model_client()
        agent = AssistantAgent(
            name="deep_analyse_agent",
            model_client=model_client,
            system_message=deep_analyse_agent_prompt,
        )

        prompt = f"""基于以下聚类信息进行深入学术分析：
## 聚类主题：{cluster.theme}
## 关键词：{', '.join(cluster.keywords)}
## 论文数量：{len(cluster.papers)}
## 论文数据：
{json.dumps(cluster.papers, ensure_ascii=False, indent=2)}

请以结构化方式组织分析结果。"""

        response = await agent.run(task=prompt)
        content = response.messages[-1].content

        return DeepAnalyseResult(
            cluster_id=cluster.cluster_id,
            theme=cluster.theme,
            keywords=cluster.keywords,
            paper_count=len(cluster.papers),
            deep_analyse=content,
            papers=cluster.papers,
        )
    except Exception as e:
        logger.error(f"深度分析聚类 {cluster.cluster_id} 失败: {e}")
        return DeepAnalyseResult(
            cluster_id=cluster.cluster_id,
            theme=cluster.theme,
            keywords=cluster.keywords,
            paper_count=len(cluster.papers),
            deep_analyse=f"分析失败: {e}",
            papers=cluster.papers,
        )


# ============================================================
# 3. 全局分析
# ============================================================

async def _global_analyse(results: List[DeepAnalyseResult]) -> Dict[str, Any]:
    """汇总所有聚类分析，生成全局分析报告"""
    cluster_summaries = []
    for r in results:
        cluster_summaries.append({
            "cluster_id": r.cluster_id,
            "theme": r.theme,
            "keywords": r.keywords,
            "paper_count": r.paper_count,
            "analyse_summary": r.deep_analyse[:3000],
        })

    model_client = create_subanalyse_global_analyse_model_client()
    agent = AssistantAgent(
        name="global_analyse_agent",
        model_client=model_client,
        system_message=global_analyse_agent_prompt,
    )

    prompt = f"""基于以下多主题聚类分析结果，生成全局分析草稿，覆盖6大核心模块：
1. 技术趋势总结  2. 方法对比  3. 应用领域分析
4. 研究热点识别  5. 局限性总结  6. 建议与展望

聚类分析数据：
{json.dumps(cluster_summaries, ensure_ascii=False, indent=2)}"""

    response = await agent.run(task=prompt)
    global_text = response.messages[-1].content

    return {
        "isSuccess": True,
        "total_clusters": len(results),
        "total_papers": sum(r.paper_count for r in results),
        "cluster_themes": [r.theme for r in results],
        "global_analyse": global_text,
        "cluster_summaries": cluster_summaries,
    }


# ============================================================
# 分析节点入口
# ============================================================

async def analyse_node(state: State) -> State:
    """分析节点: 提取数据 → 聚类 → 深度分析 → 全局分析"""
    state_queue = state["state_queue"]
    current_state = state["value"]
    current_state.current_step = ExecutionState.ANALYZING
    await state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING, state="initializing"))

    try:
        extracted = current_state.extracted_data
        if extracted is None or not extracted.papers:
            err_msg = "没有可分析的论文数据"
            logger.warning(err_msg)
            current_state.error.analyse_node_error = err_msg
            await state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING, state="error", data=err_msg))
            return {"value": current_state}

        papers_dicts = [p.model_dump() for p in extracted.papers]

        # Step 1: 聚类
        print("🔬 正在进行论文聚类分析...")
        await state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING, state="thinking", data="正在进行论文聚类分析\n"))
        clusters = _cluster_papers(papers_dicts)
        print(f"📊 形成 {len(clusters)} 个聚类")

        # 为每个聚类生成主题
        for cluster in clusters:
            theme, keywords = await _generate_cluster_theme(cluster)
            cluster.theme = theme
            cluster.keywords = keywords
            print(f"  聚类 {cluster.cluster_id}: {theme} ({len(cluster.papers)}篇)")

        await state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING, state="thinking", data=f"聚类完成，共 {len(clusters)} 个聚类\n"))

        # Step 2: 并行深度分析
        print("🔍 正在进行深度分析...")
        await state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING, state="thinking", data="正在进行深度分析\n"))
        deep_results = await asyncio.gather(*[_deep_analyse_cluster(c) for c in clusters])
        print("✅ 深度分析完成")
        await state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING, state="thinking", data="深度分析完成\n"))

        # Step 3: 全局分析
        print("🌐 正在进行全局分析...")
        await state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING, state="thinking", data="正在进行全局分析\n"))
        global_result = await _global_analyse(deep_results)
        print("✅ 全局分析完成")

        current_state.analyse_results = json.dumps(global_result, ensure_ascii=False, indent=2)
        await state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING, state="completed", data=current_state.analyse_results))
        return {"value": current_state}

    except Exception as e:
        err_msg = f"Analyse failed: {e}"
        logger.error(err_msg)
        current_state.error.analyse_node_error = err_msg
        await state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING, state="error", data=err_msg))
        return {"value": current_state}
