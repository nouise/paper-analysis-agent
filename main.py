from src.utils.log_utils import setup_logger
from fastapi import FastAPI, HTTPException
from sse_starlette.sse import EventSourceResponse
from src.agents.userproxy_agent import userProxyAgent
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.knowledge.knowledge_router import knowledge
from src.services.report_service import list_reports, get_report, update_report, delete_report
from src.services.wechat_service import WeChatService

import asyncio
from src.core.state_models import BackToFrontData
# 设置日志
logger = setup_logger(name='main', log_file='project.log')

app = FastAPI()
app.include_router(knowledge)
# === CORS 配置（开发时可用 "*"，生产请限定具体域名） ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/send_input")
async def send_input(data: dict):
    """人工审核接口: 前端提交审核结果，唤醒等待中的 userProxyAgent"""
    user_input = data.get("input")
    userProxyAgent.set_user_input(user_input)
    return JSONResponse({"status": 200, "msg": "已收到人工输入"})


@app.get('/api/research')
async def research_stream(query: str):
    from src.agents.orchestrator import PaperAgentOrchestrator

    # 每次请求创建独立的队列，避免多次请求数据串扰
    state_queue = asyncio.Queue()

    async def event_generator():
        while True:
            state = await state_queue.get()
            data_json = state.model_dump_json()
            yield {"data": data_json}
            # 当收到 finished 信号时，终止 SSE 流
            if state.state == "finished":
                logger.info("SSE 流结束")
                break
    
    # 初始化业务流程控制器
    orchestrator = PaperAgentOrchestrator(state_queue=state_queue)
    
    # 启动异步任务（后台运行工作流）
    asyncio.create_task(orchestrator.run(user_request=query))

    # 返回 SSE 事件流
    return EventSourceResponse(event_generator(), media_type="text/event-stream")


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
async def update_report_content(filename: str, data: dict):
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
async def convert_to_wechat_html(data: dict):
    """
    将 Markdown 转换为微信公众号 HTML

    请求体:
    {
        "markdown_content": "...",
        "theme": "tech",  // tech/minimal/business
        "output_filename": "article.html"  // 可选
    }
    """
    markdown_content = data.get("markdown_content")
    theme = data.get("theme", "tech")
    output_filename = data.get("output_filename")

    if not markdown_content:
        raise HTTPException(status_code=400, detail="缺少 markdown_content 字段")

    try:
        html_content, html_path = wechat_service.convert_markdown_to_html(
            markdown_content=markdown_content,
            theme=theme,
            output_filename=output_filename
        )
        return {
            "status": 200,
            "msg": "转换成功",
            "html_content": html_content,
            "html_path": html_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转换失败: {str(e)}")


@app.post('/api/wechat/publish')
async def publish_to_wechat(data: dict):
    """
    发布文章到微信公众号草稿箱

    请求体:
    {
        "title": "文章标题",
        "html_content": "...",
        "author": "作者",  // 可选
        "cover_image_path": "/path/to/cover.png",  // 可选
        "digest": "摘要"  // 可选
    }
    """
    title = data.get("title")
    html_content = data.get("html_content")
    author = data.get("author", "Paper Agent")
    cover_image_path = data.get("cover_image_path")
    digest = data.get("digest")

    if not title or not html_content:
        raise HTTPException(status_code=400, detail="缺少 title 或 html_content 字段")

    try:
        result = wechat_service.publish_to_wechat(
            title=title,
            html_content=html_content,
            author=author,
            cover_image_path=cover_image_path,
            digest=digest
        )
        return {
            "status": 200,
            "msg": "发布成功",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发布失败: {str(e)}")


@app.post('/api/wechat/convert-and-publish')
async def convert_and_publish_to_wechat(data: dict):
    """
    一键转换并发布到微信公众号

    请求体:
    {
        "markdown_content": "...",
        "title": "文章标题",
        "theme": "tech",  // 可选
        "author": "作者",  // 可选
        "cover_image_path": "/path/to/cover.png"  // 可选
    }
    """
    markdown_content = data.get("markdown_content")
    title = data.get("title")
    theme = data.get("theme", "tech")
    author = data.get("author", "Paper Agent")
    cover_image_path = data.get("cover_image_path")

    if not markdown_content or not title:
        raise HTTPException(status_code=400, detail="缺少 markdown_content 或 title 字段")

    try:
        result = wechat_service.convert_and_publish(
            markdown_content=markdown_content,
            title=title,
            theme=theme,
            author=author,
            cover_image_path=cover_image_path
        )
        return {
            "status": 200,
            "msg": "转换并发布成功",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转换并发布失败: {str(e)}")


@app.post('/api/wechat/convert-report')
async def convert_report_to_wechat(data: dict):
    """
    将历史报告转换为微信公众号格式

    请求体:
    {
        "filename": "report_xxx.md",
        "theme": "tech"  // 可选
    }
    """
    filename = data.get("filename")
    theme = data.get("theme", "tech")

    if not filename:
        raise HTTPException(status_code=400, detail="缺少 filename 字段")

    # 获取报告内容
    report = get_report(filename)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    try:
        html_content, html_path = wechat_service.convert_markdown_to_html(
            markdown_content=report.content,
            theme=theme,
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
        raise HTTPException(status_code=500, detail=f"转换失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    