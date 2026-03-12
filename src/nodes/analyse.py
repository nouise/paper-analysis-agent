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
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
from autogen_agentchat.agents import AssistantAgent

from src.core.model_client import (
    create_subanalyse_cluster_model_client,
    create_subanalyse_deep_analyse_model_client,
    create_subanalyse_global_analyse_model_client,
    create_cluster_embedding_client,
)
from src.core.prompts import (
    clustering_agent_prompt,
    deep_analyse_agent_prompt,
    global_analyse_agent_prompt,
)
from src.core.state_models import (
    State, ExecutionState, BackToFrontData,
    ExtractedPapersData,
)
from src.utils.log_utils import setup_logger
from src.utils.core_utils import get_metrics, retry_with_backoff, RetryConfig

logger = setup_logger(__name__)
metrics = get_metrics()


# ============================================================
# 常量配置
# ============================================================

class AnalyseConfig:
    """分析节点配置常量"""
    # 聚类配置
    MAX_CLUSTERS = 5
    MIN_CLUSTERS = 1
    EMBEDDING_DIMENSION = 1024
    KMEANS_RANDOM_STATE = 42
    KMEANS_N_INIT = 10

    # 并发配置
    MAX_CONCURRENT_DEEP_ANALYSIS = 3

    # 重试配置
    MAX_RETRIES = 2
    RETRY_DELAY = 2.0


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
    """
    调用 embedding API 获取向量

    Args:
        texts: 文本列表

    Returns:
        嵌入向量矩阵

    Raises:
        Exception: API 调用失败
    """
    client = create_cluster_embedding_client()

    try:
        response = client.embeddings.create(
            model=client.default_headers["X-Model"],
            input=texts,
            dimensions=AnalyseConfig.EMBEDDING_DIMENSION,
        )
        return np.array([item.embedding for item in response.data])
    except Exception as e:
        logger.error(f"[Analyse] Embedding API 调用失败: {e}")
        metrics.increment("embedding_errors")
        raise


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
    """
    对论文进行 KMeans 聚类

    Args:
        papers: 论文数据列表

    Returns:
        聚类结果列表
    """
    if len(papers) <= 2:
        return [PaperCluster(cluster_id=0, papers=papers)]

    try:
        texts = [_prepare_text(p) for p in papers]
        embeddings = _get_embedding(texts)

        # 确定聚类数
        from sklearn.cluster import KMeans
        max_k = min(AnalyseConfig.MAX_CLUSTERS, len(papers) - 1)

        if max_k <= 1:
            return [PaperCluster(cluster_id=0, papers=papers)]

        # 简单肘部法则
        inertias = []
        for k in range(1, max_k + 1):
            km = KMeans(
                n_clusters=k,
                random_state=AnalyseConfig.KMEANS_RANDOM_STATE,
                n_init=AnalyseConfig.KMEANS_N_INIT
            )
            km.fit(embeddings)
            inertias.append(km.inertia_)

        if len(inertias) >= 3:
            diffs = [inertias[i - 1] - inertias[i] for i in range(1, len(inertias))]
            n_clusters = diffs.index(max(diffs)) + 2
            n_clusters = min(n_clusters, max_k)
        else:
            n_clusters = min(2, max_k)

        # 最终聚类
        km = KMeans(
            n_clusters=n_clusters,
            random_state=AnalyseConfig.KMEANS_RANDOM_STATE,
            n_init=AnalyseConfig.KMEANS_N_INIT
        )
        labels = km.fit_predict(embeddings)

        # 构建聚类结果
        clusters = []
        for cid in range(n_clusters):
            c_papers = [papers[i] for i, l in enumerate(labels) if l == cid]
            if c_papers:
                clusters.append(PaperCluster(cluster_id=cid, papers=c_papers))

        logger.info(f"[Analyse] 聚类完成: {len(clusters)} 个聚类")
        metrics.increment("clustering_success")

        return clusters

    except Exception as e:
        logger.error(f"[Analyse] 聚类失败: {e}")
        metrics.increment("clustering_errors")
        # 失败时返回单聚类
        return [PaperCluster(cluster_id=0, papers=papers)]


async def _generate_cluster_theme(cluster: PaperCluster) -> Tuple[str, List[str]]:
    """
    用 LLM 为聚类生成主题和关键词

    Args:
        cluster: 聚类数据

    Returns:
        (主题, 关键词列表)
    """
    try:
        # 准备摘要信息
        summaries = []
        for p in cluster.papers[:3]:  # 使用前3篇作为代表
            summaries.append({
                "problem": p.get("core_problem", ""),
                "method": (p.get("key_methodology") or {}).get("name", ""),
                "results": p.get("main_results", ""),
            })

        model_client = create_subanalyse_cluster_model_client()
        agent = AssistantAgent(
            name=f"cluster_theme_agent_{cluster.cluster_id}",
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

        # 解析响应
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
        logger.error(f"[Analyse] 生成聚类 {cluster.cluster_id} 主题失败: {e}")
        return "未分类研究主题", ["research"]


# ============================================================
# 2. 深度分析
# ============================================================

async def _deep_analyse_cluster(cluster: PaperCluster) -> DeepAnalyseResult:
    """
    对单个聚类进行深度分析

    Args:
        cluster: 聚类数据

    Returns:
        深度分析结果
    """
    try:
        model_client = create_subanalyse_deep_analyse_model_client()
        agent = AssistantAgent(
            name=f"deep_analyse_agent_{cluster.cluster_id}",
            model_client=model_client,
            system_message=deep_analyse_agent_prompt,
        )

        # 限制 JSON 大小，避免超出上下文
        papers_data = json.dumps(cluster.papers, ensure_ascii=False, indent=2)
        if len(papers_data) > 10000:
            # 截断过长的数据
            papers_data = papers_data[:10000] + "... [truncated]"

        prompt = f"""基于以下聚类信息进行深入学术分析：
## 聚类主题：{cluster.theme}
## 关键词：{', '.join(cluster.keywords)}
## 论文数量：{len(cluster.papers)}
## 论文数据：
{papers_data}

请以结构化方式组织分析结果。"""

        response = await agent.run(task=prompt)
        content = response.messages[-1].content

        metrics.increment("deep_analysis_success")

        return DeepAnalyseResult(
            cluster_id=cluster.cluster_id,
            theme=cluster.theme,
            keywords=cluster.keywords,
            paper_count=len(cluster.papers),
            deep_analyse=content,
            papers=cluster.papers,
        )

    except Exception as e:
        logger.error(f"[Analyse] 深度分析聚类 {cluster.cluster_id} 失败: {e}")
        metrics.increment("deep_analysis_errors")

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
    """
    汇总所有聚类分析，生成全局分析报告

    Args:
        results: 各聚类的深度分析结果

    Returns:
        全局分析结果字典
    """
    cluster_summaries = []
    for r in results:
        cluster_summaries.append({
            "cluster_id": r.cluster_id,
            "theme": r.theme,
            "keywords": r.keywords,
            "paper_count": r.paper_count,
            "analyse_summary": r.deep_analyse[:3000],  # 限制长度
        })

    try:
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

        metrics.increment("global_analysis_success")

        return {
            "isSuccess": True,
            "total_clusters": len(results),
            "total_papers": sum(r.paper_count for r in results),
            "cluster_themes": [r.theme for r in results],
            "global_analyse": global_text,
            "cluster_summaries": cluster_summaries,
        }

    except Exception as e:
        logger.error(f"[Analyse] 全局分析失败: {e}")
        metrics.increment("global_analysis_errors")

        return {
            "isSuccess": False,
            "error": str(e),
            "total_clusters": len(results),
            "total_papers": sum(r.paper_count for r in results),
            "cluster_themes": [r.theme for r in results],
            "global_analyse": f"全局分析失败: {e}",
            "cluster_summaries": cluster_summaries,
        }


# ============================================================
# 分析节点入口
# ============================================================

async def analyse_node(state: State) -> State:
    """
    分析节点: 提取数据 → 聚类 → 深度分析 → 全局分析

    Args:
        state: LangGraph 状态

    Returns:
        更新后的状态
    """
    state_queue = state["state_queue"]
    current_state = state["value"]
    current_state.current_step = ExecutionState.ANALYZING

    await state_queue.put(BackToFrontData(
        step=ExecutionState.ANALYZING,
        state="initializing",
        summary="正在初始化分析...",
        detail="准备分析论文数据，正在进行预处理...",
        data="正在初始化分析...",
        progress=0
    ))

    with metrics.timer("analyse_node_total"):
        try:
            extracted = current_state.extracted_data

            if extracted is None or not extracted.papers:
                err_msg = "没有可分析的论文数据"
                logger.warning(f"[Analyse] {err_msg}")
                current_state.error.analyse_node_error = err_msg
                await state_queue.put(BackToFrontData(
                    step=ExecutionState.ANALYZING,
                    state="error",
                    summary="分析失败",
                    detail=f"没有可分析的论文数据: {err_msg}",
                    data=err_msg,
                    progress=100
                ))
                return {"value": current_state}

            papers_dicts = [p.model_dump() for p in extracted.papers]

            # Step 1: 聚类
            print("[聚类] 正在进行论文聚类分析...")
            await state_queue.put(BackToFrontData(
                step=ExecutionState.ANALYZING,
                state="thinking",
                summary="正在分析论文...",
                detail="正在进行论文聚类分析，识别研究主题...",
                data="正在进行论文聚类分析\n",
                progress=30
            ))

            clusters = _cluster_papers(papers_dicts)
            print(f"[统计] 形成 {len(clusters)} 个聚类")

            # 为每个聚类生成主题
            for cluster in clusters:
                theme, keywords = await _generate_cluster_theme(cluster)
                cluster.theme = theme
                cluster.keywords = keywords
                print(f"  聚类 {cluster.cluster_id}: {theme} ({len(cluster.papers)}篇)")

            await state_queue.put(BackToFrontData(
                step=ExecutionState.ANALYZING,
                state="thinking",
                summary="正在分析论文...",
                detail=f"聚类完成，共识别出 {len(clusters)} 个研究主题",
                data=f"聚类完成，共 {len(clusters)} 个聚类\n",
                progress=45
            ))

            # Step 2: 并行深度分析
            print("[分析] 正在进行深度分析...")
            await state_queue.put(BackToFrontData(
                step=ExecutionState.ANALYZING,
                state="thinking",
                summary="正在分析论文...",
                detail=f"正在对 {len(clusters)} 个研究主题进行深度分析...",
                data="正在进行深度分析\n",
                progress=50
            ))

            # 使用信号量控制并发
            semaphore = asyncio.Semaphore(AnalyseConfig.MAX_CONCURRENT_DEEP_ANALYSIS)

            async def _with_semaphore(cluster: PaperCluster) -> DeepAnalyseResult:
                async with semaphore:
                    return await _deep_analyse_cluster(cluster)

            deep_results = await asyncio.gather(*[
                _with_semaphore(c) for c in clusters
            ])

            print("[完成] 深度分析完成")
            await state_queue.put(BackToFrontData(
                step=ExecutionState.ANALYZING,
                state="thinking",
                summary="正在分析论文...",
                detail="深度分析完成，正在进行全局汇总...",
                data="深度分析完成\n",
                progress=70
            ))

            # Step 3: 全局分析
            print("[全局] 正在进行全局分析...")
            await state_queue.put(BackToFrontData(
                step=ExecutionState.ANALYZING,
                state="thinking",
                summary="正在分析论文...",
                detail="正在进行全局分析，生成综合分析报告...",
                data="正在进行全局分析\n",
                progress=85
            ))

            global_result = await _global_analyse(deep_results)
            print("[完成] 全局分析完成")

            current_state.analyse_results = json.dumps(
                global_result,
                ensure_ascii=False,
                indent=2
            )

            await state_queue.put(BackToFrontData(
                step=ExecutionState.ANALYZING,
                state="completed",
                summary="分析完成",
                detail=f"分析完成！共分析了 {len(clusters)} 个研究主题，{sum(r.paper_count for r in deep_results)} 篇论文",
                data=current_state.analyse_results,
                progress=100
            ))

            metrics.increment("analyse_node_success")
            return {"value": current_state}

        except Exception as e:
            err_msg = f"Analyse failed: {e}"
            logger.error(f"[Analyse] {err_msg}", exc_info=True)
            metrics.increment("analyse_node_errors")

            current_state.error.analyse_node_error = err_msg
            await state_queue.put(BackToFrontData(
                step=ExecutionState.ANALYZING,
                state="error",
                summary="分析失败",
                detail=f"分析过程中发生错误: {err_msg}",
                data=err_msg,
                progress=100
            ))
            return {"value": current_state}
