"""
Markdown 文档解析器

将 Markdown 转换为纯文本
"""

try:
    import markdown
    from bs4 import BeautifulSoup
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False
    markdown = None
    BeautifulSoup = None

from . import DocumentParser, ParseError


class MarkdownParser(DocumentParser):
    """Markdown 文档解析器"""

    def supports(self, mime_type: str, file_extension: str) -> bool:
        return file_extension.lower() in ['.md', '.markdown']

    async def parse(self, file_path: str) -> str:
        """解析 Markdown 文档"""
        if not HAS_MARKDOWN:
            # 如果未安装 markdown 库，直接读取文件
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                raise ParseError(f"Markdown 读取失败: {e}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            # 转换为 HTML
            html = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

            # 使用 BeautifulSoup 提取纯文本
            soup = BeautifulSoup(html, 'html.parser')

            # 移除 script 和 style 元素
            for script in soup(['script', 'style']):
                script.decompose()

            # 获取文本
            text = soup.get_text(separator='\n')

            # 清理空行
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)
        except Exception as e:
            raise ParseError(f"Markdown 解析失败: {e}")
