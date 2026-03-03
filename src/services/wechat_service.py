"""
微信公众号服务: 提供 Markdown 转 HTML 和发布到微信的功能
"""

import os
import sys
from pathlib import Path
from typing import Optional, Tuple

# 添加 wechat_article_skills 到 Python 路径
WECHAT_SKILLS_DIR = Path(__file__).parent.parent.parent / "wechat_article_skills"
sys.path.insert(0, str(WECHAT_SKILLS_DIR / "wechat-article-formatter" / "scripts"))
sys.path.insert(0, str(WECHAT_SKILLS_DIR / "wechat-draft-publisher"))

from markdown_to_html import WeChatHTMLConverter
from publisher import WeChatPublisher

from src.utils.log_utils import setup_logger

logger = setup_logger(__name__)


class WeChatService:
    """微信公众号服务"""

    def __init__(self):
        self.output_dir = Path("output/wechat")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _create_default_cover(self, cover_path: str):
        """
        创建默认封面图片

        Args:
            cover_path: 封面保存路径
        """
        try:
            from PIL import Image, ImageDraw, ImageFont

            # 创建 900x500 的蓝色背景图片
            img = Image.new('RGB', (900, 500), color='#4A90E2')
            draw = ImageDraw.Draw(img)

            # 添加文字
            try:
                font = ImageFont.truetype('arial.ttf', 60)
            except:
                font = ImageFont.load_default()

            text = 'Paper Agent'
            # 获取文字边界框
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # 居中绘制文字
            x = (900 - text_width) // 2
            y = (500 - text_height) // 2
            draw.text((x, y), text, fill='white', font=font)

            # 保存
            img.save(cover_path)
            logger.info(f"默认封面已创建: {cover_path}")

        except Exception as e:
            logger.error(f"创建默认封面失败: {e}")
            raise

    def convert_markdown_to_html(
        self,
        markdown_content: str,
        theme: str = "tech",
        output_filename: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        将 Markdown 转换为微信公众号 HTML

        Args:
            markdown_content: Markdown 内容
            theme: 主题 (tech/minimal/business)
            output_filename: 输出文件名（可选）

        Returns:
            (html_content, html_file_path)
        """
        try:
            converter = WeChatHTMLConverter(theme=theme)
            html_content = converter.convert(markdown_content)

            # 保存 HTML 文件
            if output_filename is None:
                output_filename = "wechat_article.html"

            html_path = self.output_dir / output_filename
            html_path.write_text(html_content, encoding='utf-8')

            logger.info(f"Markdown 转换成功: {html_path}")
            return html_content, str(html_path)

        except Exception as e:
            logger.error(f"Markdown 转换失败: {e}")
            raise

    def publish_to_wechat(
        self,
        title: str,
        html_content: str,
        author: str = "Paper Agent",
        cover_image_path: Optional[str] = None,
        digest: Optional[str] = None
    ) -> dict:
        """
        发布文章到微信公众号草稿箱

        Args:
            title: 文章标题
            html_content: HTML 内容
            author: 作者
            cover_image_path: 封面图片路径（可选，如果不提供则使用默认封面）
            digest: 摘要（可选）

        Returns:
            发布结果
        """
        try:
            publisher = WeChatPublisher()

            # 上传封面图片（微信 API 要求必须提供 thumb_media_id）
            thumb_media_id = None
            show_cover_pic = 1  # 默认显示封面

            if cover_image_path and os.path.exists(cover_image_path):
                # 用户提供了封面图片
                thumb_media_id = publisher.upload_image(cover_image_path)
            else:
                # 没有提供封面，使用默认封面（微信 API 要求必须有 thumb_media_id）
                default_cover = self.output_dir.parent / "default_cover.png"
                if not default_cover.exists():
                    # 创建默认封面
                    self._create_default_cover(str(default_cover))

                thumb_media_id = publisher.upload_image(str(default_cover))
                show_cover_pic = 0  # 不显示默认封面

            # 创建草稿
            result = publisher.create_draft(
                title=title,
                content=html_content,
                author=author,
                thumb_media_id=thumb_media_id,
                digest=digest or title[:54],
                show_cover_pic=show_cover_pic,
                content_base_dir=str(self.output_dir)
            )

            logger.info(f"文章发布成功: {title}")
            return result

        except Exception as e:
            logger.error(f"发布到微信失败: {e}")
            raise

    def convert_and_publish(
        self,
        markdown_content: str,
        title: str,
        theme: str = "tech",
        author: str = "Paper Agent",
        cover_image_path: Optional[str] = None
    ) -> dict:
        """
        一键转换并发布到微信

        Args:
            markdown_content: Markdown 内容
            title: 文章标题
            theme: 主题
            author: 作者
            cover_image_path: 封面图片路径

        Returns:
            发布结果
        """
        # 1. 转换为 HTML
        html_content, html_path = self.convert_markdown_to_html(
            markdown_content,
            theme=theme,
            output_filename=f"{title}.html"
        )

        # 2. 发布到微信
        result = self.publish_to_wechat(
            title=title,
            html_content=html_content,
            author=author,
            cover_image_path=cover_image_path
        )

        result['html_path'] = html_path
        return result
