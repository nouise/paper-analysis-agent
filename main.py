"""
Paper-Agent FastAPI 后端

提供以下功能:
- SSE 流式研究接口
- 人工审核输入
- 报告管理
- 知识库管理
- 微信公众号集成
- 健康检查
"""

import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from src.agents.userproxy_agent import (
    create_user_proxy_agent,
    get_user_proxy_agent,
    set_user_input_for_request,
)
from src.core.state_models import BackToFrontData
from src.knowledge.knowledge_router import knowledge
from src.services.report_service import list_reports, get_report, update_report, delete_report
from src.services.wechat_service import WeChatService
from src.utils.log_utils import setup_logger
from src.utils.core_utils import get_metrics, get_cache

# 设置日志
logger = setup_logger(name='main', log_file='project.log')

# 全局状态
active_orchestrators: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 - Graceful Shutdown"""
    # 启动
    logger.info("=" * 60)
    logger.info("Paper-Agent 启动中...")
    logger.info("=" * 60)

    # 清理旧缓存
    await get_cache().clean_expired()

    yield

    # 关闭
    logger.info("=" * 60)
    logger.info("Paper-Agent 关闭中，清理资源...")
    logger.info("=" * 60)

    # 取消所有正在运行的工作流
    for request_id, orchestrator in active_orchestrators.items():
        logger.info(f"取消工作流: {request_id}")
        if hasattr(orchestrator, 'cancel'):
            await orchestrator.cancel()

    # 清理缓存
    await get_cache().clear()

    logger.info("资源清理完成")


app = FastAPI(
    title="Paper-Agent API",
    description="AI 驱动的学术调研报告生成系统",
    version="0.1.0",
    lifespan=lifespan
)

# 包含知识库路由
app.include_router(knowledge)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境使用，生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Pydantic 模型 - 请求验证
# ============================================================

class UserInputRequest(BaseModel):
    """用户输入请求"""
    input: str = Field(..., min_length=1, description="用户输入内容")
    request_id: Optional[str] = Field(None, description="请求ID（用于并发场景）")


class WeChatConvertRequest(BaseModel):
    """微信转换请求"""
    markdown_content: str = Field(..., min_length=1, description="Markdown 内容")
    theme: str = Field(default="tech", description="主题风格: tech/minimal/business")
    output_filename: Optional[str] = Field(None, description="输出文件名")


class WeChatPublishRequest(BaseModel):
    """微信发布请求"""
    title: str = Field(..., min_length=1, max_length=64, description="文章标题")
    html_content: str = Field(..., min_length=1, description="HTML 内容")
    author: str = Field(default="Paper Agent", max_length=10, description="作者")
    cover_image_path: Optional[str] = Field(None, description="封面图片路径")
    digest: Optional[str] = Field(None, max_length=120, description="摘要")


class WeChatConvertAndPublishRequest(BaseModel):
    """微信转换并发布请求"""
    markdown_content: str = Field(..., min_length=1, description="Markdown 内容")
    title: str = Field(..., min_length=1, max_length=64, description="文章标题")
    theme: str = Field(default="tech", description="主题风格")
    author: str = Field(default="Paper Agent", description="作者")
    cover_image_path: Optional[str] = Field(None, description="封面图片路径")


class WeChatConvertReportRequest(BaseModel):
    """微信转换报告请求"""
    filename: str = Field(..., min_length=1, description="报告文件名")
    theme: str = Field(default="tech", description="主题风格")


# ============================================================
# 健康检查
# ============================================================

@app.get("/health")
async def health_check():
    """健康检查端点"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "checks": {
            "knowledge_base": await _check_kb_connection(),
            "cache": await _check_cache(),
        },
        "metrics": get_metrics().get_summary()
    }

    # 如果有任何检查失败，返回 503
    if not all(health_status["checks"].values()):
        raise HTTPException(status_code=503, detail=health_status)

    return health_status


async def _check_kb_connection() -> bool:
    """检查知识库连接"""
    try:
        # 简单的健康检查
        from src.knowledge.knowledge import knowledge_base
        # 尝试获取数据库列表
        _ = knowledge_base.get_databases()
        return True
    except Exception as e:
        logger.warning(f"知识库连接检查失败: {e}")
        return False


async def _check_cache() -> bool:
    """检查缓存状态"""
    try:
        cache = get_cache()
        # 简单的存取测试
        test_key = "_health_check_"
        await cache.set(test_key, "ok", ttl=1)
        result = await cache.get(test_key)
        return result == "ok"
    except Exception as e:
        logger.warning(f"缓存检查失败: {e}")
        return False


# ============================================================
# 人工审核接口
# ============================================================

@app.post("/send_input")
async def send_input(data: UserInputRequest):
    """
    人工审核接口

    前端提交审核结果，唤醒等待中的用户代理。
    支持并发场景，通过 request_id 指定具体请求。
    """
    user_input = data.input
    request_id = data.request_id

    # 如果提供了 request_id，使用它；否则尝试使用默认代理
    if request_id:
        success = set_user_input_for_request(request_id, user_input)
    else:
        # 向后兼容：使用默认代理
        from src.agents.userproxy_agent import userProxyAgent
        success = userProxyAgent.set_user_input(user_input)

    if success:
        return JSONResponse({"status": 200, "msg": "已收到人工输入"})
    else:
        raise HTTPException(status_code=400, detail="无法接收输入，可能代理未在等待状态")


# ============================================================
# SSE 研究接口（带心跳机制）
# ============================================================

@app.get('/api/research')
async def research_stream(query: str):
    """
    启动研究流程，返回 SSE 事件流

    事件格式: {"step": "...", "state": "...", "data": "..."}

    心跳: 每 30 秒发送一次 {"type": "heartbeat"}
    """
    from src.agents.orchestrator import PaperAgentOrchestrator

    # 生成唯一请求 ID
    request_id = str(uuid.uuid4())

    # 创建独立的队列和用户代理
    state_queue = asyncio.Queue()
    user_proxy = create_user_proxy_agent(request_id=request_id)

    # 初始化业务流程控制器
    orchestrator = PaperAgentOrchestrator(
        state_queue=state_queue,
        user_proxy=user_proxy,
        request_id=request_id
    )

    # 注册到全局字典
    active_orchestrators[request_id] = orchestrator

    async def event_generator():
        """SSE 事件生成器（带心跳）"""
        heartbeat_interval = 30.0  # 30秒心跳
        last_heartbeat = asyncio.get_event_loop().time()

        # 启动工作流任务
        workflow_task = asyncio.create_task(
            orchestrator.run(user_request=query),
            name=f"workflow_{request_id}"
        )

        try:
            while True:
                try:
                    # 使用 timeout 等待状态更新
                    timeout = heartbeat_interval - (
                        asyncio.get_event_loop().time() - last_heartbeat
                    )
                    timeout = max(timeout, 1.0)  # 至少等待 1 秒

                    state = await asyncio.wait_for(
                        state_queue.get(),
                        timeout=timeout
                    )

                    yield {
                        "event": "message",
                        "data": state.model_dump_json()
                    }

                    # 发送完成信号时结束
                    if state.state == "finished":
                        logger.info(f"[SSE:{request_id}] 流结束")
                        break

                except asyncio.TimeoutError:
                    # 发送心跳
                    heartbeat_data = json.dumps({
                        "type": "heartbeat",
                        "timestamp": datetime.utcnow().isoformat(),
                        "request_id": request_id
                    })
                    yield {"event": "heartbeat", "data": heartbeat_data}
                    last_heartbeat = asyncio.get_event_loop().time()

        except asyncio.CancelledError:
            logger.info(f"[SSE:{request_id}] 客户端断开连接")
            # 取消工作流
            workflow_task.cancel()
            try:
                await workflow_task
            except asyncio.CancelledError:
                pass
            raise

        finally:
            # 清理
            if request_id in active_orchestrators:
                del active_orchestrators[request_id]
            logger.debug(f"[SSE:{request_id}] 清理完成")

    return EventSourceResponse(
        event_generator(),
        media_type="text/event-stream",
        ping=30000,  # 30秒 ping
    )


# ============================================================
# 报告管理 API
# ============================================================

@app.get('/api/reports')
async def get_reports():
    """获取所有历史报告列表"""
    reports = list_reports()
    return [r.model_dump() for r in reports]


@app.get('/api/reports/{filename}')
async def get_report_detail(filename: str):
    """获取单个报告详情"""
    report = get_report(filename)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return report.model_dump()


@app.put('/api/reports/{filename}')
async def update_report_content(filename: str, data: Dict[str, Any]):
    """更新报告内容"""
    content = data.get("content")
    if content is None:
        raise HTTPException(status_code=400, detail="缺少 content 字段")
    success = update_report(filename, content)
    if not success:
        raise HTTPException(status_code=404, detail="报告不存在")
    return {"status": 200, "msg": "报告已更新"}


@app.delete('/api/reports/{filename}')
async def delete_report_file(filename: str):
    """删除报告"""
    success = delete_report(filename)
    if not success:
        raise HTTPException(status_code=404, detail="报告不存在")
    return {"status": 200, "msg": "报告已删除"}


# ============================================================
# 微信公众号 API
# ============================================================

wechat_service = WeChatService()


@app.post('/api/wechat/convert')
async def convert_to_wechat_html(data: WeChatConvertRequest):
    """将 Markdown 转换为微信公众号 HTML"""
    try:
        html_content, html_path = wechat_service.convert_markdown_to_html(
            markdown_content=data.markdown_content,
            theme=data.theme,
            output_filename=data.output_filename
        )
        return {
            "status": 200,
            "msg": "转换成功",
            "html_content": html_content,
            "html_path": html_path
        }
    except Exception as e:
        logger.error(f"Markdown 转换失败: {e}")
        raise HTTPException(status_code=500, detail=f"转换失败: {str(e)}")


@app.post('/api/wechat/publish')
async def publish_to_wechat(data: WeChatPublishRequest):
    """发布文章到微信公众号草稿箱"""
    try:
        result = wechat_service.publish_to_wechat(
            title=data.title,
            html_content=data.html_content,
            author=data.author,
            cover_image_path=data.cover_image_path,
            digest=data.digest
        )
        return {
            "status": 200,
            "msg": "发布成功",
            "result": result
        }
    except Exception as e:
        logger.error(f"发布到微信失败: {e}")
        raise HTTPException(status_code=500, detail=f"发布失败: {str(e)}")


@app.post('/api/wechat/convert-and-publish')
async def convert_and_publish_to_wechat(data: WeChatConvertAndPublishRequest):
    """一键转换并发布到微信公众号"""
    try:
        result = wechat_service.convert_and_publish(
            markdown_content=data.markdown_content,
            title=data.title,
            theme=data.theme,
            author=data.author,
            cover_image_path=data.cover_image_path
        )
        return {
            "status": 200,
            "msg": "转换并发布成功",
            "result": result
        }
    except Exception as e:
        logger.error(f"转换并发布失败: {e}")
        raise HTTPException(status_code=500, detail=f"转换并发布失败: {str(e)}")


@app.post('/api/wechat/convert-report')
async def convert_report_to_wechat(data: WeChatConvertReportRequest):
    """将历史报告转换为微信公众号格式"""
    # 获取报告内容
    report = get_report(data.filename)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    try:
        html_content, html_path = wechat_service.convert_markdown_to_html(
            markdown_content=report.content,
            theme=data.theme,
            output_filename=f"{report.title}.html"
        )
        return {
            "status": 200,
            "msg": "转换成功",
            "html_content": html_content,
            "html_path": html_path,
            "title": report.title
        }
    except Exception as e:
        logger.error(f"转换报告失败: {e}")
        raise HTTPException(status_code=500, detail=f"转换失败: {str(e)}")


# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    import uvicorn

    # 从环境变量读取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "false").lower() == "true"

    logger.info(f"启动服务器: {host}:{port} (reload={reload})")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
