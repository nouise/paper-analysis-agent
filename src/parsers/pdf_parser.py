"""
PDF 文档解析器

使用 PyMuPDF (fitz) 解析 PDF 文件
"""

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False
    fitz = None

from . import DocumentParser, ParseError


class PDFParser(DocumentParser):
    """PDF 文档解析器"""

    def supports(self, mime_type: str, file_extension: str) -> bool:
        return file_extension.lower() == '.pdf' or mime_type == 'application/pdf'

    async def parse(self, file_path: str) -> str:
        """解析 PDF 文档"""
        if not HAS_FITZ:
            raise ParseError("PDF 解析需要安装 PyMuPDF: poetry install")

        try:
            text_parts = []
            doc = fitz.open(file_path)
            self._pages = len(doc)  # 保存页数用于元数据

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_parts.append(f"[Page {page_num + 1}]\n{text}")

            doc.close()
            return "\n\n".join(text_parts)
        except Exception as e:
            raise ParseError(f"PDF 解析失败: {e}")
