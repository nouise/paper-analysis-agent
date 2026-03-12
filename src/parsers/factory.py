"""
解析器工厂

根据文件类型自动选择合适的解析器
"""

from pathlib import Path
from typing import List, Optional

from . import DocumentParser, UnsupportedFormatError
from .pdf_parser import PDFParser
from .docx_parser import DocxParser
from .markdown_parser import MarkdownParser
from .text_parser import TextParser


class ParserFactory:
    """解析器工厂"""

    _parsers: List[DocumentParser] = [
        PDFParser(),
        DocxParser(),
        MarkdownParser(),
        TextParser(),
    ]

    @classmethod
    def get_parser(cls, file_path: str) -> DocumentParser:
        """
        根据文件路径获取合适的解析器

        Args:
            file_path: 文件路径

        Returns:
            合适的文档解析器

        Raises:
            UnsupportedFormatError: 如果文件格式不支持
        """
        # 由于 python-magic 在 Windows 上可能有问题，这里主要使用扩展名
        path = Path(file_path)
        file_ext = path.suffix.lower()

        # 根据扩展名选择解析器
        ext_to_parser = {
            '.pdf': PDFParser(),
            '.docx': DocxParser(),
            '.md': MarkdownParser(),
            '.markdown': MarkdownParser(),
            '.txt': TextParser(),
            '.text': TextParser(),
        }

        if file_ext in ext_to_parser:
            return ext_to_parser[file_ext]

        raise UnsupportedFormatError(f"不支持的文件格式: {file_ext}")

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """获取支持的文件扩展名列表"""
        return ['.pdf', '.docx', '.md', '.markdown', '.txt', '.text']

    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """检查文件是否支持"""
        path = Path(file_path)
        return path.suffix.lower() in cls.get_supported_extensions()
