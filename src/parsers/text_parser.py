"""
纯文本解析器

直接读取 TXT 文件
"""

from . import DocumentParser, ParseError


class TextParser(DocumentParser):
    """纯文本文档解析器"""

    def supports(self, mime_type: str, file_extension: str) -> bool:
        return file_extension.lower() in ['.txt', '.text'] or mime_type.startswith('text/')

    async def parse(self, file_path: str) -> str:
        """解析纯文本文档"""
        try:
            # 尝试多种编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue

            # 如果所有编码都失败，使用 latin-1（不会抛出异常）
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()

        except Exception as e:
            raise ParseError(f"文本解析失败: {e}")
