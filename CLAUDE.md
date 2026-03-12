# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Paper Analysis Agent is a multi-agent academic paper research system that automates the workflow: **Paper Search → Reading → Cluster Analysis → Chapter Writing → Report Generation**. It uses LangGraph for workflow orchestration, AutoGen for multi-agent collaboration, FastAPI for the backend, and Vue 3 for the frontend.

## Common Commands

### Backend (Python/FastAPI)

```bash
# Install dependencies
poetry install --no-root

# Run development server (port 8002)
poetry run python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload

# Run tests
poetry run pytest

# Add new dependency
poetry add <package-name>
```

### Frontend (Vue 3)

```bash
cd web

# Install dependencies
npm install

# Run development server (port 5173)
npm run dev

# Build for production
npm run build
```

### Environment Setup

```bash
# Copy environment template
cp example.env .env

# Required: Edit .env and set DASHSCOPE_API_KEY at minimum
```

## High-Level Architecture

### Workflow Orchestration (LangGraph)

The core workflow is defined in `src/agents/orchestrator.py` using LangGraph StateGraph:

```
search_node → reading_node → analyse_node → writing_node → report_node
     ↑
userProxyAgent (human review via Future mechanism)
```

**Key architectural pattern**: Each node receives a `State` TypedDict containing:
- `state_queue`: `asyncio.Queue` for SSE progress推送
- `value`: `PaperAgentState` - the actual workflow state

**Human-in-the-loop**: The `WebUserProxyAgent` (`src/agents/userproxy_agent.py`) creates an `asyncio.Future` and awaits user input via POST `/send_input`. This pauses the workflow at the search stage for keyword review.

### State Management

**Backend**: `src/core/state_models.py` defines the single source of truth:
- `PaperAgentState`: Main workflow state containing user_request, search_results, extracted_data, analyse_results, writted_sections, report_markdown
- `ExecutionState`: Enum of workflow stages (SEARCHING, READING, ANALYZING, WRITING, REPORTING, etc.)
- `BackToFrontData`: SSE communication format

**Frontend**: Uses Vue 3 reactive state. Key components:
- `App.vue`: Main workflow display with SSE connection
- `views/History.vue`: Report management
- `views/KnowledgeBase.vue`: Knowledge base management

### Multi-Agent System

Agents are organized hierarchically:

```
src/agents/
├── orchestrator.py          # LangGraph workflow builder
├── userproxy_agent.py       # Human review handler
├── sub_analyse_agent/       # Analysis sub-agents
│   ├── cluster_agent.py     # KMeans + LLM topic clustering
│   ├── deep_analyse_agent.py # Per-cluster deep analysis
│   └── global_analyse_agent.py # Cross-cluster synthesis
└── sub_writing_agent/       # Writing sub-agents
    ├── director.py          # Outline generation
    ├── writer.py            # Chapter writing
    ├── retrieval_agent.py   # RAG from ChromaDB
    └── review_agent.py      # Quality review
```

### SSE Real-time Communication

The backend uses `sse-starlette` to stream progress. Events follow this format:

```json
{
  "step": "searching|reading|analysing|writing|reporting",
  "state": "initializing|thinking|generating|user_review|completed|error|finished",
  "data": "..."
}
```

Key SSE endpoint: `GET /api/research?query=...` - initiates workflow and returns event stream.

### Knowledge Base System

Located in `src/knowledge/`:
- `knowledge_router.py`: FastAPI routes for CRUD operations
- `knowledge/`: ChromaDB abstraction layer
  - `manager.py`: Business logic for document indexing/querying
  - `implementations/chroma.py`: ChromaDB-specific implementation

Document parsing (planned): `src/parsers/` with factory pattern for PDF, DOCX, MD, TXT.

### Report Management

`src/services/report_service.py`: File-based CRUD for generated reports stored in `output/reports/`. Reports are Markdown files with metadata headers.

### Configuration System

- `src/core/models.yaml`: Model selection per node (provider: dashscope/siliconflow/openai/ark)
- `src/core/system_params.yaml`: System-wide parameters
- `.env`: API keys and secrets (never commit this)

### WeChat Integration

`src/services/wechat_service.py` and `wechat_article_skills/`: Converts Markdown reports to WeChat HTML with three theme styles (tech/minimal/business).

## Key Development Patterns

### Adding a New Node

1. Create node function in `src/nodes/{name}.py`
2. Accept `state: State` parameter, return `State`
3. Use `await state["state_queue"].put(BackToFrontData(...))` for progress updates
4. Register in `src/agents/orchestrator.py:_build_graph()`

### Adding a New Agent

1. Create agent class inheriting from AutoGen's `ConversableAgent` or `AssistantAgent`
2. Place in appropriate `sub_*_agent/` directory
3. Use `src/core/model_client.py` for LLM client configuration

### State Updates Between Nodes

Nodes communicate via `PaperAgentState` fields. Common pattern:
```python
current_state = state["value"]
current_state.search_results = {...}  # Set data for next node
current_state.current_step = ExecutionState.READING  # Update step
return {"state_queue": state["state_queue"], "value": current_state}
```

### Error Handling

Each node should catch exceptions and set:
```python
current_state.error = NodeError(message=str(e), details=...)
current_state.current_step = ExecutionState.FAILED
```

The orchestrator's `condition_handler` routes to `handle_error_node` when error is set.

## File Organization Conventions

- `src/nodes/`: LangGraph node implementations (workflow steps)
- `src/agents/`: Agent definitions (LLM actors)
- `src/core/`: Configuration and shared models
- `src/services/`: Business services (not agent-related)
- `src/tasks/`: Background task implementations
- `src/utils/`: Utility functions
- `web/src/views/`: Page-level Vue components
- `web/src/components/`: Reusable Vue components

## Important Notes

- **Port configuration**: Backend runs on 8002, frontend on 5173. Frontend proxy is configured in `web/vite.config.js`.
- **Request isolation**: Each `/api/research` request creates a new `PaperAgentOrchestrator` instance stored in `active_orchestrators` dict.
- **Graceful shutdown**: The FastAPI lifespan handler cancels all running workflows on shutdown.
- **Parallel processing**: Reading and writing use `asyncio.gather()` for concurrent execution.
- **RAG integration**: Writing agents use `retrieval_agent` to query ChromaDB which contains both arXiv papers and user knowledge base documents.

## Documentation References

- `RPD.md`: Requirements & Product Document (EARS format requirements)
- `IMPLEMENTATION_STATUS.md`: Implementation status and technical proposals
- `design.md`: Detailed design documentation
- `WECHAT_SETUP.md`: WeChat integration setup guide
