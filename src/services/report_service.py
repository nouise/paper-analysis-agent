"""
报告服务: 提供报告的增删改查功能
读取 output/reports/ 目录下的 .md 文件
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from src.utils.log_utils import setup_logger

logger = setup_logger(__name__)

REPORTS_DIR = Path("output/reports")


class ReportMeta(BaseModel):
    """报告元数据"""
    filename: str
    title: str
    query: str
    created_at: str
    size: int  # 字节数


class ReportDetail(BaseModel):
    """报告详细内容"""
    filename: str
    title: str
    query: str
    created_at: str
    content: str


def _parse_filename(filename: str) -> dict:
    """从文件名解析元数据
    格式: report_YYYYMMDD_HHMMSS_查询关键词.md
    """
    stem = Path(filename).stem  # 去掉 .md
    # 匹配 report_日期_时间_查询内容
    match = re.match(r'^report_(\d{8})_(\d{6})_(.+)$', stem)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        query = match.group(3).replace('_', ' ')
        try:
            dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
            created_at = dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            created_at = ""
    else:
        query = stem
        created_at = ""
    
    return {"query": query, "created_at": created_at}


def _extract_title(content: str, fallback: str = "未命名报告") -> str:
    """从报告内容中提取标题（第一个 # 开头的行）"""
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('# ') and not line.startswith('## '):
            return line[2:].strip()
    return fallback


def list_reports() -> List[ReportMeta]:
    """列出所有报告"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    reports = []
    
    for f in sorted(REPORTS_DIR.glob("*.md"), key=os.path.getmtime, reverse=True):
        meta = _parse_filename(f.name)
        
        # 读取文件提取标题
        try:
            content = f.read_text(encoding='utf-8')
            title = _extract_title(content, meta["query"])
        except Exception:
            title = meta["query"]
            content = ""
        
        reports.append(ReportMeta(
            filename=f.name,
            title=title,
            query=meta["query"],
            created_at=meta["created_at"],
            size=f.stat().st_size,
        ))
    
    return reports


def get_report(filename: str) -> Optional[ReportDetail]:
    """获取单个报告详情"""
    filepath = REPORTS_DIR / filename
    if not filepath.exists() or not filepath.suffix == '.md':
        return None
    
    content = filepath.read_text(encoding='utf-8')
    meta = _parse_filename(filename)
    title = _extract_title(content, meta["query"])
    
    return ReportDetail(
        filename=filename,
        title=title,
        query=meta["query"],
        created_at=meta["created_at"],
        content=content,
    )


def update_report(filename: str, content: str) -> bool:
    """更新报告内容"""
    filepath = REPORTS_DIR / filename
    if not filepath.exists() or not filepath.suffix == '.md':
        return False
    
    filepath.write_text(content, encoding='utf-8')
    logger.info(f"报告已更新: {filepath}")
    return True


def delete_report(filename: str) -> bool:
    """删除报告"""
    filepath = REPORTS_DIR / filename
    if not filepath.exists() or not filepath.suffix == '.md':
        return False
    
    filepath.unlink()
    logger.info(f"报告已删除: {filepath}")
    return True
