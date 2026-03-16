# RAG 模块深度分析

> 聚焦问题: 1) PDF如何实现embedding  2) 如何查找top-k  3) 效果不好怎么办
> 日期: 2026-03-13

---

## 一、PDF 如何实现 Embedding

### 整体流程

```
PDF文件 → 解析文本 → 文本分割(Chunk) → Embedding计算 → 向量存储
```

### 1.1 PDF 解析

**文件**: `src/parsers/pdf_parser.py`

```python
class PDFParser(DocumentParser):
    async def parse(self, file_path: str) -> str:
        doc = fitz.open(file_path)  # PyMuPDF
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_parts.append(f"[Page {page_num + 1}]\n{text}")
        return "\n\n".join(text_parts)
```

**关键设计**:
- 使用 **PyMuPDF (fitz)** 解析 PDF
- 保留页码信息 `[Page X]`
- 跳过空白页

### 1.2 文本分割 (Text Splitting)

**文件**: `src/knowledge/knowledge/utils/kb_utils.py`

```python
def split_text_into_chunks(text: str, file_id: str, filename: str, params: dict = {}) -> list[dict]:
    chunk_size = params.get("chunk_size", 1000)
    chunk_overlap = params.get("chunk_overlap", 200)

    # 使用 MarkdownTextSplitter 智能分割
    text_splitter = MarkdownTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    text_chunks = text_splitter.split_text(text)

    # 转换为标准格式
    for chunk_index, chunk_content in enumerate(text_chunks):
        chunks.append({
            "id": f"{file_id}_chunk_{chunk_index}",
            "content": chunk_content.strip(),
            "file_id": file_id,
            "filename": filename,
            "chunk_index": chunk_index,
            "source": filename,
            "chunk_id": f"{file_id}_chunk_{chunk_index}",
        })
```

**分割策略对比**:

| 分割器 | 特点 | 适用场景 |
|--------|------|----------|
| MarkdownTextSplitter | 沿 Markdown 标题分割 | Markdown/结构文档 |
| RecursiveCharacterTextSplitter | 递归分割，支持多分隔符 | 通用文本 |
| CharacterTextSplitter | 按字符简单分割 | QA 格式数据 |

**关键参数**:
- `chunk_size`: 块大小 (默认 1000 字符)
- `chunk_overlap`: 重叠大小 (默认 200 字符)

**为什么需要 overlap?**
```
文本: "这是一个很长的句子，需要被分割成多个块..."

块1 (0-1000):  "这是一个很长的句子，需要被分割..."
块2 (800-1800): "被分割成多个块，每个块之间有..."
                  ↑↑↑ overlap 区域
```
- 保持上下文连续性
- 避免关键信息被截断在边界

### 1.3 Embedding 计算

**文件**: `src/knowledge/knowledge/implementations/chroma.py`

```python
class DashScopeEmbeddingFunction:
    """自定义 Embedding Function，支持手动批次控制"""

    def __init__(self, api_key: str, api_base: str, model_name: str):
        self.client = OpenAI(api_key=api_key, base_url=api_base)

    def __call__(self, texts: List[str]) -> List[List[float]]:
        """分批计算 embedding，每批最多 10 个（DashScope 限制）"""
        batch_size = 10
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self.client.embeddings.create(
                model=self.model_name,
                input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return all_embeddings
```

**关键设计**:
- **手动批次控制**: DashScope API 限制每批最多 10 个
- **预计算策略**: 在插入 ChromaDB 前先计算好 embedding
- **异步分批**: 避免一次性请求过多导致 API 限流

### 1.4 向量存储

**文件**: `src/knowledge/knowledge/implementations/chroma.py`

```python
async def add_content(self, db_id: str, items: list[str], params: dict | None) -> list[dict]:
    # 1. PDF → Markdown
    markdown_content = await process_file_to_markdown(item, params=params)

    # 2. 文本分割
    chunks = self._split_text_into_chunks(markdown_content, file_id, filename, params)

    # 3. 预计算 Embeddings
    embed_func = self._get_embedding_function(...)
    embeddings = embed_func(documents)  # 手动计算

    # 4. 插入 ChromaDB (使用预计算的 embeddings)
    batch_size = 1  # 极端分批，避免任何问题
    for i in range(0, len(chunks), batch_size):
        await asyncio.to_thread(
            collection.add,
            embeddings=batch_embeddings,  # 预计算的 embedding
            documents=batch_documents,
            metadatas=batch_metadatas,
            ids=batch_ids,
        )
```

**存储结构**:
```python
{
    "id": "file_xxx_chunk_0",           # 唯一ID
    "document": "文本内容...",           # 原始文本
    "embedding": [0.1, 0.2, ...],        # 向量 (1024维)
    "metadata": {
        "source": "document.pdf",        # 来源文件
        "chunk_id": "file_xxx_chunk_0",  # Chunk ID
        "full_doc_id": "file_xxx",       # 文档ID
        "chunk_type": "normal",          # Chunk 类型
    }
}
```

---

## 二、如何查找 Top-K

### 2.1 查询流程

```
用户查询 → Embedding计算 → 向量相似度搜索 → 相似度过滤 → Top-K返回
```

### 2.2 查询实现

**文件**: `src/knowledge/knowledge/implementations/chroma.py`

```python
async def aquery(self, db_id: str, query_text: Union[str, List[str]] = "", **kwargs) -> list[dict]:
    # 1. 获取参数
    top_k = kwargs.get("top_k", config.get("top_k", 10))
    similarity_threshold = kwargs.get("similarity_threshold", config.get("similarity_threshold", 0.0))

    # 2. 调用 ChromaDB 查询
    text_query_results = collection.query(
        query_texts=query_texts,
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    # 3. 处理结果
    retrieved_chunks = []
    for i, doc in enumerate(documents):
        # 距离转相似度 (ChromaDB 返回的是距离，越小越相似)
        similarity = 1 - distances[i] if i < len(distances) else 1.0

        # 相似度阈值过滤
        if similarity < similarity_threshold:
            continue

        # Chunk 去重
        has_same_chunk_id = False
        for chunk in retrieved_chunks:
            if chunk.get("metadata").get("chunk_id") == metadata.get("chunk_id"):
                has_same_chunk_id = True
                break
        if not has_same_chunk_id:
            retrieved_chunks.append({
                "content": doc,
                "metadata": metadata,
                "score": similarity
            })

    return retrieved_chunks
```

### 2.3 相似度计算

**ChromaDB 默认使用 Cosine Similarity (余弦相似度)**:

```
similarity = cos(θ) = (A · B) / (||A|| × ||B||)

距离(distance) = 1 - similarity
```

**代码中的转换**:
```python
similarity = 1 - distances[i]  # 距离 → 相似度
```

### 2.4 双知识库检索

**文件**: `src/services/retrieval_tool.py`

```python
async def retrieval_tool(querys: List[str]) -> List[List[Dict[str, Any]]]:
    retrieval_results = []

    # 1. 从临时知识库检索 (arXiv 论文)
    tmp_db_id = config.get("tmp_db_id")
    tmpdb_results = await knowledge_base.aquery(
        querys,
        db_id=tmp_db_id,
        top_k=config.get_int("tmpdb_top_k"),
        similarity_threshold=config.get_float("tmpdb_similarity_threshold")
    )

    # 2. 从用户知识库检索 (私有文档)
    db_id = config.get("current_db_id")
    db_results = await knowledge_base.aquery(
        querys,
        db_id=db_id,
        top_k=config.get_int("top_k"),
        similarity_threshold=config.get_float("similarity_threshold")
    )

    # 合并结果
    return retrieval_results
```

### 2.5 检索参数配置

**文件**: `src/core/system_params.yaml` (推测)

```yaml
# Top-K 配置
top_k: 5                    # 默认返回5个结果
tmpdb_top_k: 5              # 临时知识库返回5个

# 相似度阈值配置 (0-1，越大越严格)
similarity_threshold: 0.5   # 默认阈值 0.5
tmpdb_similarity_threshold: 0.5
```

**阈值选择建议**:

| 阈值 | 效果 | 适用场景 |
|------|------|----------|
| 0.3 | 宽松，召回率高 | 需要更多参考资料 |
| 0.5 | 平衡 | 一般场景 |
| 0.7 | 严格，精度高 | 需要高质量匹配 |
| 0.9 | 非常严格 | 精确匹配场景 |

---

## 三、效果不好怎么办

### 3.1 效果不好的表现

1. **召回率低**: 相关文档没有被检索到
2. **精确率低**: 检索到很多不相关的文档
3. **排序差**: 最相关的文档不在前面

### 3.2 优化策略矩阵

```
                    ┌─────────────────────────────────────┐
                    │         效果不好原因分析             │
                    ├─────────────┬─────────────┬─────────┤
                    │  文本分割问题 │  Embedding  │  检索策略 │
    ┌───────────────┼─────────────┼─────────────┼─────────┤
    │  优化方向      │             │             │         │
    ├───────────────┼─────────────┼─────────────┼─────────┤
    │ Chunk Size    │    ✓        │             │         │
    │ Overlap       │    ✓        │             │         │
    │ 分割策略      │    ✓        │             │         │
    │ Embedding模型 │             │    ✓        │         │
    │ 微调(Fine-tune)│            │    ✓        │         │
    │ 重排序(Rerank)│             │             │    ✓    │
    │ 查询扩展      │             │             │    ✓    │
    │ 混合检索      │             │             │    ✓    │
    └───────────────┴─────────────┴─────────────┴─────────┘
```

### 3.3 具体优化方案

#### 方案 1: 优化文本分割 (Chunking)

**问题**: Chunk 太大或太小都会影响检索效果

**当前实现**:
```python
chunk_size = 1000
chunk_overlap = 200
```

**优化建议**:
```python
# 根据文档类型调整
DOC_TYPE_CONFIG = {
    "technical_paper": {"chunk_size": 500, "overlap": 100},   # 技术论文，短段落
    "legal_document": {"chunk_size": 2000, "overlap": 400},   # 法律文档，长条款
    "qa_document": {"chunk_size": 300, "overlap": 50},       # QA文档，短问答
    "general": {"chunk_size": 1000, "overlap": 200},         # 一般文档
}
```

**面试要点**:
- Chunk 太小 → 上下文丢失，语义不完整
- Chunk 太大 → 噪声多，相似度被稀释
- 需要实验找到最佳值

#### 方案 2: 使用更好的 Embedding 模型

**当前**: 使用 DashScope/Qwen Embedding

**升级选项**:
```python
# 选项 1: 更大的模型 (效果更好但更慢)
"Qwen/Qwen3-Embedding-8B"  # 当前使用
"BAAI/bge-m3"               # 更强的多语言模型
"BAAI/bge-large-zh"         # 中文专用

# 选项 2: 领域专用模型
# 如果是医学领域
"medical-domain-embedding"
# 如果是法律领域
"legal-domain-embedding"
```

**代码修改**:
```python
# models.yaml
embedding-model:
  model-provider: siliconflow
  model: BAAI/bge-m3  # 更换模型
  dimension: 1024
```

#### 方案 3: 添加重排序 (Reranking)

**原理**: 先用 embedding 快速召回 Top-K*10，再用更精确的模型重排序

**代码实现** (项目中已有注释掉的实现):
```python
# src/knowledge/knowledge/manager.py

async def aquery(self, query_text: Union[str, List[str]], db_id: str, **kwargs) -> list[dict]:
    # 1. 基础检索 (召回 Top-K*5)
    results = await kb_instance.aquery(db_id, query_text, top_k=top_k*5, **kwargs)

    # 2. 重排序 (如果启用)
    if config.get("enable_reranker", False) and results:
        reranker = get_reranker(config.reranker)

        # 准备输入
        sentences = [result["content"] for result in results]
        sentence_pairs = (query_text, sentences)

        # 计算重排序分数
        rerank_scores = reranker.compute_score(sentence_pairs, normalize=True)

        # 更新分数
        for i, result in enumerate(results):
            result["rerank_score"] = rerank_scores[i]

        # 按重排序分数重新排序
        results.sort(key=lambda x: x["rerank_score"], reverse=True)

    return results[:top_k]
```

**推荐重排序模型**:
- `BAAI/bge-reranker-large`
- `cohere/rerank-english-v2.0`

#### 方案 4: 查询扩展 (Query Expansion)

**原理**: 将用户查询扩展成多个相关查询，提高召回率

**实现思路**:
```python
async def query_with_expansion(query: str, db_id: str, **kwargs):
    # 1. 使用 LLM 扩展查询
    expansion_prompt = f"""
    将以下查询扩展成 3 个语义相似的查询：
    原始查询: {query}

    要求:
    - 保持语义一致
    - 使用不同的表达方式
    - 每个查询一行
    """

    expanded_queries = await llm.generate(expansion_prompt)
    all_queries = [query] + expanded_queries.split("\n")

    # 2. 并行检索所有查询
    all_results = []
    for q in all_queries:
        results = await knowledge_base.aquery(q, db_id=db_id, **kwargs)
        all_results.extend(results)

    # 3. 去重并重新排序
    unique_results = deduplicate(all_results)
    return unique_results[:top_k]
```

#### 方案 5: 混合检索 (Hybrid Search)

**原理**: 结合向量检索 + 关键词检索 (BM25)

**实现思路**:
```python
async def hybrid_search(query: str, db_id: str, **kwargs):
    # 1. 向量检索
    vector_results = await knowledge_base.aquery(query, db_id=db_id, **kwargs)

    # 2. 关键词检索 (需要额外的 BM25 索引)
    keyword_results = await bm25_search(query, db_id=db_id, **kwargs)

    # 3. 融合结果 (RRF - Reciprocal Rank Fusion)
    fused_results = reciprocal_rank_fusion(vector_results, keyword_results)

    return fused_results[:top_k]


def reciprocal_rank_fusion(vector_results, keyword_results, k=60):
    """RRF 融合算法"""
    scores = {}

    # 向量检索分数
    for rank, result in enumerate(vector_results):
        doc_id = result["metadata"]["chunk_id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)

    # 关键词检索分数
    for rank, result in enumerate(keyword_results):
        doc_id = result["metadata"]["chunk_id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)

    # 排序返回
    sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [get_result_by_id(doc_id) for doc_id, _ in sorted_results]
```

### 3.4 效果评估

**关键指标**:

```python
# 1. 召回率 (Recall)
recall = len(relevant_retrieved) / len(all_relevant)

# 2. 精确率 (Precision)
precision = len(relevant_retrieved) / len(all_retrieved)

# 3. F1 分数
f1 = 2 * (precision * recall) / (precision + recall)

# 4. NDCG (归一化折损累计增益)
# 评估排序质量
```

**评估方法**:
```python
def evaluate_retrieval(test_queries: List[Query], top_k: int = 5):
    """评估检索效果"""
    results = []

    for query in test_queries:
        retrieved = await knowledge_base.aquery(query.text, top_k=top_k)
        retrieved_ids = {r["metadata"]["chunk_id"] for r in retrieved}
        relevant_ids = set(query.relevant_chunks)

        # 计算指标
        true_positives = len(retrieved_ids & relevant_ids)
        recall = true_positives / len(relevant_ids) if relevant_ids else 0
        precision = true_positives / len(retrieved_ids) if retrieved_ids else 0

        results.append({
            "query": query.text,
            "recall": recall,
            "precision": precision,
        })

    # 平均指标
    avg_recall = sum(r["recall"] for r in results) / len(results)
    avg_precision = sum(r["precision"] for r in results) / len(results)

    return {
        "avg_recall": avg_recall,
        "avg_precision": avg_precision,
        "f1": 2 * (avg_precision * avg_recall) / (avg_precision + avg_recall),
    }
```

---

## 四、面试要点总结

### Q1: PDF 如何实现 Embedding?

**回答框架**:
```
1. PDF解析: 使用 PyMuPDF 提取文本，保留页码
2. 文本分割: MarkdownTextSplitter，chunk_size=1000, overlap=200
3. Embedding计算: DashScope API，手动分批(每批10个)
4. 向量存储: ChromaDB，预计算 embedding 后插入

关键设计: 预计算策略 + 分批处理避免 API 限流
```

### Q2: 如何查找 Top-K?

**回答框架**:
```
1. 查询向量化: 使用相同的 Embedding 模型
2. 相似度搜索: ChromaDB query，使用 Cosine Similarity
3. 相似度转换: distance → similarity (1 - distance)
4. 阈值过滤: 根据 similarity_threshold 过滤低质量结果
5. 去重返回: 按 chunk_id 去重，返回 Top-K

双知识库: 同时检索 tmp_db (arXiv) 和 user_db (私有文档)
```

### Q3: 效果不好怎么办?

**回答框架**:
```
1. 文本分割优化: 调整 chunk_size/overlap，根据文档类型选择分割策略
2. Embedding模型升级: 使用更强的模型如 BAAI/bge-m3
3. 重排序(Rerank): 先召回 Top-K*10，再用精确模型重排序
4. 查询扩展: LLM 扩展查询为多个语义相似查询
5. 混合检索: 结合向量检索 + BM25 关键词检索

评估: 使用 Recall、Precision、F1 指标定量评估
```

---

## 五、代码路径索引

| 功能 | 文件路径 |
|------|----------|
| PDF 解析 | `src/parsers/pdf_parser.py` |
| 文本分割 | `src/knowledge/knowledge/utils/kb_utils.py` |
| Embedding | `src/knowledge/knowledge/implementations/chroma.py` (DashScopeEmbeddingFunction) |
| 向量存储 | `src/knowledge/knowledge/implementations/chroma.py` (add_content) |
| 向量检索 | `src/knowledge/knowledge/implementations/chroma.py` (aquery) |
| 检索工具 | `src/services/retrieval_tool.py` |
| 知识库管理 | `src/knowledge/knowledge/manager.py` |
