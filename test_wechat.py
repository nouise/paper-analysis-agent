#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号功能测试脚本
"""

import sys
import io
from pathlib import Path

# 设置标准输出编码为 UTF-8（Windows 兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.wechat_service import WeChatService
from src.services.report_service import list_reports, get_report


def test_convert():
    """测试 Markdown 转 HTML"""
    print("=" * 60)
    print("测试 1: Markdown 转 HTML")
    print("=" * 60)

    # 测试 Markdown 内容
    test_markdown = """
# AI 研究综述

## 引言

人工智能（AI）是计算机科学的一个重要分支。

## 主要技术

### 机器学习

机器学习是 AI 的核心技术之一。

```python
import numpy as np

def train_model(X, y):
    # 训练模型
    model = LinearRegression()
    model.fit(X, y)
    return model
```

### 深度学习

深度学习使用神经网络进行学习。

## 结论

AI 技术正在快速发展。
"""

    try:
        service = WeChatService()
        html_content, html_path = service.convert_markdown_to_html(
            markdown_content=test_markdown,
            theme="tech",
            output_filename="test_article.html"
        )

        print(f"[成功] 转换成功！")
        print(f"[文件] HTML 文件: {html_path}")
        print(f"[大小] HTML 大小: {len(html_content)} 字符")
        print(f"\n💡 请在浏览器中打开查看效果:")
        print(f"   file://{Path(html_path).absolute()}")

        return True

    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_convert_report():
    """测试转换历史报告"""
    print("\n" + "=" * 60)
    print("测试 2: 转换历史报告")
    print("=" * 60)

    # 获取最新的报告
    reports = list_reports()

    if not reports:
        print("⚠️  没有找到历史报告，跳过此测试")
        return True

    latest_report = reports[0]
    print(f"📄 选择报告: {latest_report.title}")
    print(f"📅 创建时间: {latest_report.created_at}")

    try:
        # 获取报告详情
        report = get_report(latest_report.filename)

        # 转换为 HTML
        service = WeChatService()
        html_content, html_path = service.convert_markdown_to_html(
            markdown_content=report.content,
            theme="tech",
            output_filename=f"{report.title}.html"
        )

        print(f"[成功] 转换成功！")
        print(f"[文件] HTML 文件: {html_path}")
        print(f"[大小] HTML 大小: {len(html_content)} 字符")

        return True

    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wechat_config():
    """测试微信配置"""
    print("\n" + "=" * 60)
    print("测试 3: 检查微信配置")
    print("=" * 60)

    import os
    config_file = os.path.expanduser("~/.wechat-publisher/config.json")

    if os.path.exists(config_file):
        print(f"✅ 配置文件存在: {config_file}")

        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            appid = config.get('appid', '')
            appsecret = config.get('appsecret', '')

            if appid and appsecret:
                print(f"✅ AppID: {appid[:6]}***")
                print(f"✅ AppSecret: {'*' * 10}")
                print(f"\n💡 配置正确，可以使用发布功能")
                return True
            else:
                print(f"⚠️  配置文件存在但内容不完整")
                print(f"   请检查 appid 和 appsecret 字段")
                return False

        except Exception as e:
            print(f"❌ 读取配置文件失败: {e}")
            return False
    else:
        print(f"⚠️  配置文件不存在: {config_file}")
        print(f"\n💡 首次使用发布功能时会自动引导配置")
        print(f"   或手动创建配置文件:")
        print(f"   {config_file}")
        print(f"\n   内容格式:")
        print(f'   {{"appid": "wx...", "appsecret": "..."}}')
        return False


def main():
    """主函数"""
    print("\n🚀 Paper Agent - 微信公众号功能测试\n")

    results = []

    # 测试 1: Markdown 转 HTML
    results.append(("Markdown 转 HTML", test_convert()))

    # 测试 2: 转换历史报告
    results.append(("转换历史报告", test_convert_report()))

    # 测试 3: 检查微信配置
    results.append(("微信配置检查", test_wechat_config()))

    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n🎉 所有测试通过！")
        print("\n📖 使用说明:")
        print("   1. 启动后端: python main.py")
        print("   2. 启动前端: cd web && npm run dev")
        print("   3. 打开浏览器访问前端")
        print("   4. 在历史报告页面点击'微信公众号'按钮")
        print("\n📚 详细文档: WECHAT_SETUP.md")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息")
        print("\n📚 故障排除: 查看 WECHAT_SETUP.md")


if __name__ == "__main__":
    main()
