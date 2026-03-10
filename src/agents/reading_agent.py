from autogen_agentchat.agents import AssistantAgent
from pydantic import BaseModel, Field
from typing import List, Optional,Dict,Any
from src.utils.log_utils import setup_logger
from src.core.prompts import reading_agent_prompt
from src.core.model_client import create_default_client, create_reading_model_client
from src.core.state_models import BackToFrontData
from src.core.state_models import State,ExecutionState
from src.services.chroma_client import ChromaClient
from src.knowledge.knowledge import knowledge_base
from src.core.config import config

import asyncio
import json

logger = setup_logger(__name__)

class KeyMethodology(BaseModel):
    name: Optional[str] = Field(default=None, description="方法名称（如“Transformer-based Sentiment Classifier”）")
    principle: Optional[str] = Field(default=None, description="核心原理")
    novelty: Optional[str] = Field(default=None, description="创新点（如“首次引入领域自适应预训练”）")


class ExtractedPaperData(BaseModel):
    # paper_id: str = Field(default=None, description="论文ID")
    core_problem: str = Field(default=None, description="核心问题")
    key_methodology: KeyMethodology = Field(default=None, description="关键方法")
    datasets_used: List[str] = Field(default=[], description="使用的数据集")
    evaluation_metrics: List[str] = Field(default=[], description="评估指标")
    main_results: str = Field(default="", description="主要结果")
    limitations: str = Field(default="", description="局限性")
    contributions: List[str] = Field(default=[], description="贡献")
    # author_institutions: Optional[str]  # 如“Stanford University, Department of CS”

# 创建一个新的Pydantic模型来包装列表
class ExtractedPapersData(BaseModel):
    papers: List[ExtractedPaperData] = Field(default=[], description="提取的论文数据列表")

model_client = create_reading_model_client()

read_agent = AssistantAgent(
    name="read_agent",
    model_client=model_client,
    system_message=reading_agent_prompt,
    output_content_type=ExtractedPaperData,
    model_client_stream=True
)


async def add_papers_to_kb(papers:Optional[List[Dict[str, Any]]], extracted_papers: ExtractedPapersData):
    """将提取的论文数据添加到知识库"""
    embedding_dic = config.get("embedding-model")
    embedding_provider = embedding_dic.get("model-provider")
    provider_dic = config.get(embedding_provider)
    
    embed_info = {
        "name": embedding_dic.get("model"),
        "dimension": embedding_dic.get("dimension"),
        "base_url": provider_dic.get("base_url"),
        "api_key": provider_dic.get("api_key"),
    }
    kb_type = config.get("KB_TYPE")
    database_info = await knowledge_base.create_database(
        "临时知识库", "用于存储临时提取的论文数据，仅用于本次报告的生成，用完即删", kb_type=kb_type, embed_info=embed_info, llm_info=None,
    )
    db_id = database_info["db_id"]
    config.set("tmp_db_id", db_id) # 记录临时知识库的db_id，后面retrieval_agent中使用
    
    # 准备数据（注意：不要在列表末尾加逗号，否则会变成元组）
    documents = [json.dumps(paper.model_dump(), ensure_ascii=False) for paper in extracted_papers.papers]
    
    # 规范化 metadatas：只保留 ChromaDB 支持的基本类型字段
    metadatas = []
    for paper in papers:
        metadata = {
            "paper_id": str(paper.get("paper_id", "")),
            "title": str(paper.get("title", "")),
            "published_date": str(paper.get("published_date", "")),
            "url": str(paper.get("url", "")),
            "primary_category": str(paper.get("primary_category", "")),
        }
        metadatas.append(metadata)
    
    # ChromaDB 要求 ids 是字符串
    ids = [f"paper_{i}" for i in range(len(papers))]
    
    data = {
        "documents": documents,
        "metadatas": metadatas,
        "ids": ids,
    }

    await knowledge_base.add_processed_content(db_id, data)


async def process_papers_with_semaphore(papers: List[Dict], max_concurrent: int = 2) -> List[Any]:
    """使用信号量限制并发数量，避免API过载"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_one_paper(paper: Dict, index: int) -> Any:
        async with semaphore:
            print(f"[阅读] [{index+1}/{len(papers)}] 正在阅读论文: {paper.get('title', 'Unknown')[:60]}...")
            
            # 简化传递给 LLM 的内容，减少token消耗
            simplified_paper = {
                'paper_id': paper.get('paper_id'),
                'title': paper.get('title'),
                'authors': paper.get('authors', [])[:5],  # 只取前5个作者
                'summary': paper.get('summary', '')[:1500],  # 限制摘要长度
                'published_date': paper.get('published_date'),
                'url': paper.get('url'),
                'primary_category': paper.get('primary_category')
            }
            
            # 添加重试机制
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    result = await read_agent.run(task=str(simplified_paper))
                    print("result:", result)
                    print(f"[完成] [{index+1}/{len(papers)}] 论文阅读完成")
                    return result
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"[警告] [{index+1}/{len(papers)}] 第 {attempt+1} 次尝试失败: {str(e)[:100]}, 重试中...")
                        await asyncio.sleep(2 ** attempt)  # 指数退避
                    else:
                        print(f"[错误] [{index+1}/{len(papers)}] 所有尝试均失败: {str(e)[:100]}")
                        raise
    
    tasks = [process_one_paper(paper, i) for i, paper in enumerate(papers)]
    return await asyncio.gather(*tasks, return_exceptions=True)


async def reading_node(state: State) -> State:
    """阅读论文节点 - 使用受控并发避免API超时"""
    state_queue = state["state_queue"]
    current_state = state["value"]
    current_state.current_step = ExecutionState.READING
    await state_queue.put(BackToFrontData(step=ExecutionState.READING,state="initializing",data=None))

    papers = current_state.search_results
    
    print(f"\n[书籍] 开始阅读 {len(papers)} 篇论文...")
    print(f"[设置] 并发控制: 最多同时处理 2 篇论文（避免API过载）\n")

    # 使用受控并发处理论文（限制同时处理2篇，避免API超时）
    results = await process_papers_with_semaphore(papers, max_concurrent=2)

    # 合并结果，过滤掉失败的任务
    extracted_papers = ExtractedPapersData()
    failed_count = 0
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # 任务失败
            failed_count += 1
            logger.error(f"论文 {i+1} 处理失败: {result}")
            continue
        
        try:
            parsed_paper = result.messages[-1].content
            extracted_papers.papers.append(parsed_paper)
        except Exception as e:
            failed_count += 1
            logger.error(f"解析论文 {i+1} 结果失败: {e}")
    
    success_count = len(extracted_papers.papers)
    print(f"\n[统计] 阅读统计: 成功 {success_count} 篇, 失败 {failed_count} 篇")     

     # 还得存入向量数据库中
    await add_papers_to_kb(papers,extracted_papers)
        
    current_state.extracted_data = extracted_papers
    await state_queue.put(BackToFrontData(step=ExecutionState.READING,state="completed",data=f"论文阅读完成，共阅读 {len(extracted_papers.papers)} 篇论文"))
    return {"value": current_state}


if __name__ == "__main__":
    paper = {
        'core_problem': 'Despite the rapid introduction of autonomous vehicles, public misunderstanding and mistrust are prominent issues hindering their acceptance.'
    }
    chroma_client = ChromaClient()
    chroma_client.add_documents(
        documents=[paper],
        metadatas=[paper],
    )   