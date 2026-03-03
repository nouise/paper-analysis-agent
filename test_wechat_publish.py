#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试微信公众号发布功能
"""

import sys
import io
from pathlib import Path

# 设置标准输出编码为 UTF-8（Windows 兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "wechat_article_skills" / "wechat-draft-publisher"))

from publisher import WeChatPublisher

def test_simple_publish():
    """测试最简单的发布（无封面）"""
    print("=" * 70)
    print("测试：发布无封面文章到微信公众号")
    print("=" * 70)

    # 简单的 HTML 内容
    html_content = """
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; background-color: #ffffff;">
        <h1 style="color: #333; font-size: 24px; margin-bottom: 20px;">测试文章标题</h1>
        <p style="color: #666; line-height: 1.8; margin-bottom: 15px;">这是一篇测试文章，用于验证微信公众号发布功能是否正常。</p>
        <h2 style="color: #444; font-size: 20px; margin-top: 30px; margin-bottom: 15px;">第一部分</h2>
        <p style="color: #666; line-height: 1.8; margin-bottom: 15px;">这里是第一部分的内容。</p>
        <h2 style="color: #444; font-size: 20px; margin-top: 30px; margin-bottom: 15px;">第二部分</h2>
        <p style="color: #666; line-height: 1.8; margin-bottom: 15px;">这里是第二部分的内容。</p>
    </div>
    """

    try:
        publisher = WeChatPublisher()

        print("\n→ 测试 1: 不提供 thumb_media_id（传递 None）")
        print(f"  标题: 测试文章 - 无封面")
        print(f"  作者: Test Agent")
        print(f"  封面: 无")
        print()

        # 发布（不提供封面）
        result = publisher.create_draft(
            title="测试文章 - 无封面",
            content=html_content,
            author="Test Agent",
            thumb_media_id=None,  # 明确传递 None
            digest="这是一篇测试文章"
        )

        print("\n" + "=" * 70)
        print("✅ 发布成功！")
        print("=" * 70)
        print(f"media_id: {result.get('media_id')}")
        print("\n请前往微信公众号后台查看草稿")

        return True

    except Exception as e:
        error_msg = str(e)
        print("\n" + "=" * 70)
        print("❌ 测试 1 失败")
        print("=" * 70)
        print(f"错误信息: {error_msg}")

        # 如果是 invalid media_id 错误，说明微信 API 要求必须提供 thumb_media_id
        if "40007" in error_msg or "invalid media_id" in error_msg:
            print("\n💡 分析: 微信 API 要求 thumb_media_id 为必需字段")
            print("   即使不显示封面，也需要上传一个占位图片")
            print("\n→ 测试 2: 使用默认封面图片")

            try:
                # 上传默认封面
                print("\n→ 上传默认封面图片...")
                thumb_media_id = publisher.upload_image("output/default_cover.png")

                print(f"\n→ 使用封面重新发布...")
                result = publisher.create_draft(
                    title="测试文章 - 带默认封面",
                    content=html_content,
                    author="Test Agent",
                    thumb_media_id=thumb_media_id,
                    digest="这是一篇测试文章",
                    show_cover_pic=0  # 不显示封面
                )

                print("\n" + "=" * 70)
                print("✅ 测试 2 成功！")
                print("=" * 70)
                print(f"media_id: {result.get('media_id')}")
                print("\n结论: 微信 API 要求必须提供 thumb_media_id，即使设置不显示封面")
                print("      建议: 始终上传一个默认封面图片")

                return True

            except Exception as e2:
                print(f"\n❌ 测试 2 也失败: {e2}")
                return False

        return False


if __name__ == "__main__":
    success = test_simple_publish()
    sys.exit(0 if success else 1)
