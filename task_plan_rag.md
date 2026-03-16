# RAG 模块面试准备计划

> 目标: 深入理解 RAG 实现，能够回答面试官关于 PDF Embedding、Top-K 检索、效果优化的问题

---

## 当前状态

✅ 已完成代码分析
✅ 已创建详细技术文档 `findings_rag_deep_dive.md`
⬜ 创建演示代码
⬜ 验证关键流程

---

## Phase 1: 理解 PDF Embedding 流程

**学习目标**: 能够清晰描述从 PDF 到向量的完整流程

### 1.1 流程梳理

```
PDF文件 → 解析(PyMuPDF) → 分割(MarkdownTextSplitter) → Embedding(DashScope) → 存储(ChromaDB)
```

### 1.2 关键参数

| 参数 | 当前值 | 说明 |
|------|--------|------|
| chunk_size | 1000 | 每块字符数 |
| chunk_overlap | 200 | 块间重叠字符数 |
| batch_size | 10 | Embedding API 批次大小 |
| embedding_dim | 1024 | 向量维度 |

### 1.3 面试要点

- 为什么要 overlap? → 保持上下文连续性
- 为什么分批? → DashScope API 限制每批最多 10 个
- 为什么预计算 embedding? → 手动控制批次，避免 ChromaDB 内部处理不当

**验收标准**: 能够在不看代码的情况下描述完整流程

---

## Phase 2: 理解 Top-K 检索

**学习目标**: 能够解释向量检索原理和实现

### 2.1 检索流程

```
查询文本 → Embedding → 向量相似度计算 → 阈值过滤 → 去重 → Top-K返回
```

### 2.2 关键概念

- **Cosine Similarity**: 余弦相似度，范围 [-1, 1]
- **Distance**: ChromaDB 返回的是距离，需要 `similarity = 1 - distance`
- **相似度阈值**: 过滤低质量结果，默认 0.5

### 2.3 双知识库检索

```python
# 临时知识库 (arXiv 论文)
tmp_results = await knowledge_base.aquery(querys, db_id=tmp_db_id, ...)

# 用户知识库 (私有文档)
user_results = await knowledge_base.aquery(querys, db_id=current_db_id, ...)
```

**验收标准**: 能够解释相似度计算和阈值过滤的逻辑

---

## Phase 3: 掌握效果优化方案

**学习目标**: 能够针对"效果不好"提出 3-5 个优化方案

### 3.1 优化方案清单

| 方案 | 难度 | 效果 | 优先级 |
|------|------|------|--------|
| 调整 Chunk 参数 | 低 | 中 | P0 |
| 更换 Embedding 模型 | 低 | 高 | P0 |
| 添加重排序(Rerank) | 中 | 高 | P1 |
| 查询扩展 | 中 | 中 | P1 |
| 混合检索 | 高 | 高 | P2 |

### 3.2 面试重点

**重排序 (Rerank) 原理**:
```
1. 先用 Embedding 快速召回 Top-K*10
2. 再用精确模型 (如 bge-reranker) 计算查询与文档的相关性
3. 重新排序，返回 Top-K

优势: Embedding 速度快但精度有限，Rerank 模型精度高但慢
      两者结合兼顾效率和效果
```

**混合检索原理**:
```
向量检索: 擅长语义匹配，但可能漏掉关键词
关键词检索(BM25): 擅长精确匹配，但不懂语义
融合(RRF): 综合两者优势
```

**验收标准**: 能够详细解释至少 3 种优化方案的原理

---

## Phase 4: 实战演练

### 4.1 可能的面试问题

**Q1**: 你们的 RAG 系统是如何处理 PDF 的?

**回答要点**:
```
1. 使用 PyMuPDF 解析 PDF，提取文本并保留页码
2. 使用 MarkdownTextSplitter 分割文本，chunk_size=1000, overlap=200
3. 使用 DashScope Embedding API 计算向量，分批处理(每批10个)
4. 存储到 ChromaDB，包括文本、向量、元数据
5. 关键点: overlap 保持上下文，预计算 embedding 控制批次
```

**Q2**: 如何检索相关文档?

**回答要点**:
```
1. 将查询文本用相同的 Embedding 模型向量化
2. 调用 ChromaDB query，使用 Cosine Similarity 计算相似度
3. ChromaDB 返回距离，我们转换为相似度: similarity = 1 - distance
4. 根据配置的 similarity_threshold 过滤低质量结果
5. 对 chunk_id 去重，返回 Top-K
6. 同时检索临时知识库(arXiv)和用户知识库(私有文档)
```

**Q3**: 如果检索效果不好，你会怎么优化?

**回答要点**:
```
首先分析问题: 是召回率低? 精确率低? 还是排序差?

优化方案:
1. 调整 Chunk 参数: 根据文档类型调整 chunk_size 和 overlap
2. 更换 Embedding 模型: 使用更强的模型如 bge-m3
3. 添加重排序: 先用 Embedding 召回 Top-K*10，再用 bge-reranker 精确排序
4. 查询扩展: 用 LLM 将查询扩展为多个语义相似查询
5. 混合检索: 结合向量检索和 BM25 关键词检索

评估: 使用 Recall、Precision、F1 指标定量评估效果
```

### 4.2 代码走查

**关键文件**:
- `src/knowledge/knowledge/implementations/chroma.py` (Embedding + 检索)
- `src/knowledge/knowledge/utils/kb_utils.py` (文本分割)
- `src/parsers/pdf_parser.py` (PDF 解析)
- `src/services/retrieval_tool.py` (双知识库检索)

---

## 参考文档

- `findings_rag_deep_dive.md` - 详细技术分析
- `demos/demo_module_02_data.py` - 数据层演示

---

## 下一步行动

1. 阅读 `findings_rag_deep_dive.md` 完整文档
2. 准备面试回答要点
3. 练习不看代码描述完整流程
