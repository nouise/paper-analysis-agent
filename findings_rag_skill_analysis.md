# RAG Skill 分析与优化建议

> 参考: ConardLi/rag-skill (本地知识库检索助手)
> 分析日期: 2026-03-13

---

## 一、rag-skill 核心特点分析

### 1.1 架构定位

这是一个**面向本地文件的知识库检索助手**，与向量数据库方案不同，它采用：

- **分层索引 + 文件检索** 而非 向量化 + 语义检索
- **渐进式局部读取** 而非 整文件加载
- **多轮迭代检索** 机制

### 1.2 核心机制

```
┌─────────────────────────────────────────────────────────────┐
│                    分层索引机制                              │
├─────────────────────────────────────────────────────────────┤
│  knowledge/                                                 │
│  ├── data_structure.md  ← 根索引（领域目录说明）              │
│  ├── domain_a/                                              │
│  │   ├── data_structure.md  ← 子索引                        │
│  │   └── files...                                           │
│  └── domain_b/                                              │
│      └── ...                                                │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 关键设计

| 设计 | 说明 | 优势 |
|------|------|------|
| **分层索引** | 多级 `data_structure.md` 描述目录结构 | 快速定位，避免全局扫描 |
| **渐进式检索** | grep定位→局部读取→分析→再检索 | 避免整文件加载，节省token |
| **多轮迭代** | 最多5次迭代，逐步细化 | 提高检索精度 |
| **文件特化处理** | PDF/Excel/文本各自有最佳实践 | 提高处理效率和准确性 |
| **先学习后处理** | 处理前先读取参考文档 | 避免盲目尝试 |

---

## 二、与你当前项目的对比

### 2.1 当前项目特点 (Paper Analysis Agent)

```
用户查询 → Embedding → ChromaDB向量检索 → Top-K返回
                ↓
        临时知识库(tmp_db) ← arXiv论文
        用户知识库(user_db) ← 上传文档
```

**核心特点**:
- 基于 **向量语义相似度** 检索
- 使用 **ChromaDB** 存储向量
- **Embedding模型** 生成向量
- 支持 **双知识库** 检索

### 2.2 两种方案的对比

| 维度 | 你的项目 (向量RAG) | rag-skill (文件RAG) |
|------|-------------------|-------------------|
| **核心机制** | 向量相似度 | 分层索引+关键词 |
| **存储** | ChromaDB向量库 | 本地文件系统 |
| **检索方式** | 语义相似度 | grep关键词匹配 |
| **优势** | 语义理解，模糊匹配 | 精确检索，可溯源 |
| **劣势** | 需要Embedding，有幻觉风险 | 依赖关键词质量 |
| **适用场景** | 大规模文档，语义问答 | 结构化知识库，精确检索 |

---

## 三、可借鉴的优化点

### 3.1 分层索引机制 (可借鉴)

**当前问题**: 你的项目直接对PDF进行向量化，缺乏文件级别的索引

**优化建议**: 添加知识库索引层

```python
# 新增: src/knowledge/knowledge_index.py

class KnowledgeIndex:
    """
    知识库索引管理
    维护文件级别的元数据索引，不依赖向量
    """

    def __init__(self, db_id: str):
        self.db_id = db_id
        self.index_file = f"data/knowledge_index/{db_id}_index.json"

    def build_index(self, file_path: str):
        """
        为文件构建索引项
        """
        index_item = {
            "file_id": generate_file_id(),
            "filename": Path(file_path).name,
            "file_type": Path(file_path).suffix.lower(),
            "path": file_path,
            "content_hash": calculate_hash(file_path),
            "keywords": extract_keywords(file_path),  # 提取关键词
            "summary": generate_summary(file_path),   # 生成摘要
            "chunk_count": count_chunks(file_path),   # chunk数量
            "created_at": utc_isoformat(),
            "metadata": extract_metadata(file_path),  # 文件元数据
        }
        return index_item

    def search_by_keywords(self, keywords: List[str]) -> List[dict]:
        """
        关键词搜索文件（向量检索前的预筛选）
        """
        results = []
        for item in self.index.values():
            score = sum(1 for kw in keywords if kw in item["keywords"])
            if score > 0:
                results.append({"item": item, "score": score})
        return sorted(results, key=lambda x: x["score"], reverse=True)
```

**好处**:
- 快速定位可能相关的文件，减少向量检索范围
- 可追溯文件来源
- 支持文件级别的关键词搜索

### 3.2 渐进式检索策略 (部分可借鉴)

**当前问题**: 直接对整个知识库做向量检索

**优化建议**: 分层检索策略

```python
async def hierarchical_retrieval(query: str, db_id: str, **kwargs) -> List[dict]:
    """
    分层检索策略
    """
    # 第1层: 索引层 - 快速筛选候选文件
    candidate_files = await index_layer.search(query)
    if not candidate_files:
        return []

    # 第2层: 向量层 - 在候选文件内做向量检索
    results = []
    for file in candidate_files[:5]:  # 只取Top5候选文件
        file_results = await vector_search_in_file(query, file["file_id"], top_k=3)
        results.extend(file_results)

    # 第3层: 重排序层 - 对结果进行精确排序
    if len(results) > 10:
        results = await rerank_results(query, results)

    return results[:kwargs.get("top_k", 5)]
```

### 3.3 PDF处理优化 (强烈推荐)

**rag-skill的PDF处理最佳实践**:

| 场景 | 推荐工具 | 优势 |
|------|----------|------|
| 纯文本提取 | `pdftotext` | 最快最简单 |
| 保留布局 | `pdftotext -layout` | 保持原始排版 |
| 提取表格 | `pdfplumber` | 表格识别能力强 |
| 元数据 | `pypdf` | 轻量级 |

**你当前代码的优化空间**:

```python
# 当前代码: src/parsers/pdf_parser.py
# 使用 PyMuPDF (fitz) - 也不错，但可以更灵活

# 优化建议: 多策略PDF解析
class OptimizedPDFParser:
    """
    多策略PDF解析器
    """

    def __init__(self):
        self.strategies = {
            "fast": self._parse_with_pdftotext,      # 最快
            "layout": self._parse_with_pdfplumber,   # 保留布局
            "table": self._parse_tables_with_pdfplumber,  # 提取表格
            "ocr": self._parse_with_ocr,             # OCR兜底
        }

    async def parse(self, file_path: str, strategy: str = "auto") -> dict:
        """
        智能选择解析策略
        """
        if strategy == "auto":
            # 自动选择策略
            if self._has_tables(file_path):
                strategy = "table"
            elif self._is_scanned(file_path):
                strategy = "ocr"
            else:
                strategy = "fast"

        parser = self.strategies.get(strategy, self._parse_with_pdftotext)
        return await parser(file_path)

    async def _parse_with_pdftotext(self, file_path: str) -> str:
        """
        使用 pdftotext 快速提取文本（rag-skill推荐）
        """
        import subprocess
        output_file = f"/tmp/{uuid.uuid4()}.txt"

        # pdftotext 比 PyMuPDF 更快
        subprocess.run(
            ["pdftotext", "-layout", file_path, output_file],
            check=True
        )

        with open(output_file, 'r', encoding='utf-8') as f:
            text = f.read()

        os.remove(output_file)
        return text

    async def _parse_tables_with_pdfplumber(self, file_path: str) -> dict:
        """
        使用 pdfplumber 提取表格（rag-skill推荐）
        """
        import pdfplumber

        result = {
            "text": "",
            "tables": []
        }

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # 提取文本
                text = page.extract_text()
                if text:
                    result["text"] += f"\n[Page {page.page_number}]\n{text}"

                # 提取表格
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        result["tables"].append({
                            "page": page.page_number,
                            "data": table
                        })

        return result
```

### 3.4 多轮迭代检索 (可借鉴)

```python
async def iterative_retrieval(query: str, db_id: str, max_iterations: int = 5) -> List[dict]:
    """
    多轮迭代检索 (参考rag-skill)
    """
    all_results = []
    keywords = extract_keywords(query)

    for iteration in range(max_iterations):
        # 每轮迭代扩展关键词
        if iteration > 0:
            keywords = expand_keywords(keywords, all_results)

        # 检索
        results = await knowledge_base.aquery(
            keywords,
            db_id=db_id,
            top_k=5
        )

        # 分析结果，判断是否足够
        if is_sufficient(results, query):
            break

        all_results.extend(results)

    return deduplicate(all_results)
```

### 3.5 Excel处理优化 (可借鉴)

rag-skill中Excel处理的最佳实践：

```python
# 当前你的代码可能一次性读取整个Excel

# 优化: 按需读取，减少内存占用
import pandas as pd

async def optimized_excel_processing(file_path: str, params: dict) -> str:
    """
    优化的Excel处理
    """
    # 1. 先读取前几行了解结构
    preview = pd.read_excel(file_path, nrows=5)
    columns = preview.columns.tolist()

    # 2. 只读取需要的列
    usecols = params.get("usecols", columns)

    # 3. 按条件过滤读取
    df = pd.read_excel(file_path, usecols=usecols)

    # 4. 如果需要聚合，先做聚合
    if params.get("aggregate"):
        df = df.groupby(params["groupby"]).agg(params["aggregate"])

    return df.to_markdown()
```

---

## 四、具体优化建议清单

### 高优先级 (立即实施)

1. **PDF解析多策略支持**
   - 添加 `pdftotext` 作为快速解析选项
   - 添加 `pdfplumber` 表格提取能力
   - 根据PDF类型自动选择策略

2. **添加知识库索引层**
   - 为每个文件维护关键词索引
   - 向量检索前先做关键词预筛选

3. **渐进式文本分割**
   - 大文件先分段，按需处理
   - 避免一次性加载大文件到内存

### 中优先级 (后续实施)

4. **多轮迭代检索**
   - 实现关键词扩展机制
   - 检索结果不足时自动扩展查询

5. **检索结果溯源**
   - 记录每个结果的来源文件、页码
   - 提供引用信息

### 低优先级 (可选)

6. **混合检索**
   - 结合向量检索 + 关键词检索
   - RRF融合算法

---

## 五、代码实现示例

### 5.1 优化的PDF解析器

```python
# src/parsers/pdf_parser_optimized.py

import subprocess
import os
import tempfile
from pathlib import Path
from typing import Literal

class OptimizedPDFParser:
    """
    多策略PDF解析器（参考rag-skill优化）
    """

    async def parse(
        self,
        file_path: str,
        strategy: Literal["auto", "fast", "layout", "table", "ocr"] = "auto"
    ) -> dict:
        """
        解析PDF

        Args:
            file_path: PDF文件路径
            strategy: 解析策略
                - auto: 自动选择
                - fast: 最快，使用pdftotext
                - layout: 保留布局
                - table: 提取表格
                - ocr: OCR识别
        """
        if strategy == "auto":
            strategy = self._detect_strategy(file_path)

        if strategy == "fast":
            return {"text": await self._parse_fast(file_path)}
        elif strategy == "table":
            return await self._parse_with_tables(file_path)
        elif strategy == "ocr":
            return {"text": await self._parse_ocr(file_path)}
        else:
            return {"text": await self._parse_layout(file_path)}

    async def _parse_fast(self, file_path: str) -> str:
        """使用pdftotext快速解析（rag-skill推荐）"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            subprocess.run(
                ["pdftotext", "-layout", file_path, tmp_path],
                check=True,
                capture_output=True
            )

            with open(tmp_path, 'r', encoding='utf-8') as f:
                text = f.read()

            return text
        finally:
            os.unlink(tmp_path)

    async def _parse_with_tables(self, file_path: str) -> dict:
        """使用pdfplumber提取表格"""
        import pdfplumber

        result = {"text": "", "tables": []}

        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    result["text"] += f"\n[Page {i}]\n{text}"

                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) > 1:
                        result["tables"].append({
                            "page": i,
                            "headers": table[0],
                            "rows": table[1:]
                        })

        return result

    def _detect_strategy(self, file_path: str) -> str:
        """自动检测最佳解析策略"""
        # TODO: 实现策略检测逻辑
        return "fast"
```

### 5.2 分层检索实现

```python
# src/knowledge/hierarchical_retrieval.py

class HierarchicalRetriever:
    """
    分层检索器
    """

    async def retrieve(
        self,
        query: str,
        db_id: str,
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """
        分层检索流程
        """
        # 第1层: 索引层筛选
        candidates = await self._index_layer.search(query, limit=10)

        if not candidates:
            return []

        # 第2层: 向量层精确检索
        results = []
        for candidate in candidates:
            file_results = await self._vector_layer.search_in_file(
                query,
                file_id=candidate.file_id,
                top_k=3
            )
            results.extend(file_results)

        # 第3层: 重排序
        if len(results) > top_k * 2:
            results = await self._rerank_layer.rerank(query, results)

        return results[:top_k]
```

---

## 六、总结

### 你的项目 vs rag-skill

| 维度 | 你的项目 | rag-skill | 结合建议 |
|------|---------|-----------|----------|
| **存储** | ChromaDB向量 | 本地文件 | 保持向量，添加索引层 |
| **检索** | 向量相似度 | 关键词+分层 | 向量为主，关键词预筛选 |
| **PDF处理** | PyMuPDF | pdftotext/pdfplumber | 多策略支持 |
| **检索策略** | 单次检索 | 多轮迭代 | 添加迭代机制 |

### 推荐优化顺序

1. **立即**: 优化PDF解析器，支持多策略
2. **短期**: 添加知识库索引层
3. **中期**: 实现分层检索
4. **长期**: 多轮迭代检索

### 面试亮点

可以这样说：
"我参考了rag-skill的分层索引思想，在我们的向量RAG基础上增加了索引层，实现关键词预筛选+向量精确检索的两阶段检索，既保留了语义检索的优势，又提高了检索效率和可溯源性。"
