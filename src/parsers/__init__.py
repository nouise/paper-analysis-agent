"""
文档解析器模块

提供统一的文档解析接口，支持 PDF、Word、Markdown、TXT 等格式。
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional, List


class DocumentParser(ABC):
    """文档解析器基类"""

    @abstractmethod
    async def parse(self, file_path: str) -> str:
        """解析文档返回纯文本内容"""
        pass

    @abstractmethod
    def supports(self, mime_type: str, file_extension: str) -> bool:
        """是否支持该文件类型"""
        pass

    async def parse_with_metadata(self, file_path: str) -> dict:
        """解析并返回带元数据的结果"""
        content = await self.parse(file_path)
        path = Path(file_path)
        return {
            "content": content,
            "file_path": file_path,
            "file_name": path.name,
            "file_size": path.stat().st_size,
            "parser_type": self.__class__.__name__,
            "success": True,
            "pages": getattr(self, '_pages', None)  # PDF 特有
        }


class UnsupportedFormatError(Exception):
    """不支持的文件格式错误"""
    pass


class ParseError(Exception):
    """解析错误"""
    pass
