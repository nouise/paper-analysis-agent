#!/usr/bin/env python3
"""测试微信公众号发布功能"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("[测试] 开始测试微信公众号发布...")

try:
    from src.services.wechat_service import WeChatService
    print("[测试] WeChatService 导入成功")

    service = WeChatService()
    print("[测试] WeChatService 初始化成功")

    # 测试转换
    md_content = """# 测试文章

这是一篇测试文章，用于测试微信公众号发布功能。

## 测试章节

测试内容。"""

    print("[测试] 开始转换 Markdown...")
    html_content, html_path = service.convert_markdown_to_html(
        markdown_content=md_content,
        theme='tech',
        output_filename='test_article.html'
    )
    print(f"[转换成功] HTML路径: {html_path}")
    print(f"[转换成功] HTML长度: {len(html_content)} 字符")

    # 测试发布
    print("[测试] 开始发布到微信公众号...")
    result = service.publish_to_wechat(
        title='测试文章',
        html_content=html_content,
        author='Paper Agent'
    )
    print(f"[发布成功] 结果: {result}")

except Exception as e:
    print(f"[错误] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
