#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paper Agent - 微信功能演示脚本
展示如何使用微信公众号功能
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


def demo_convert():
    """演示：转换 Markdown 为 HTML"""
    print("\n" + "=" * 70)
    print("演示 1: 转换 Markdown 为微信公众号 HTML")
    print("=" * 70)

    from src.services.wechat_service import WeChatService

    # 示例 Markdown 内容
    markdown_content = """
# 人工智能研究前沿

## 引言

人工智能（Artificial Intelligence, AI）正在改变我们的世界。

## 核心技术

### 1. 机器学习

机器学习是 AI 的核心技术，主要包括：

- **监督学习**：从标注数据中学习
- **无监督学习**：发现数据中的模式
- **强化学习**：通过试错学习最优策略

### 2. 深度学习

深度学习使用多层神经网络进行特征学习。

```python
import torch
import torch.nn as nn

class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(784, 128),
            nn.ReLU(),
            nn.Linear(128, 10)
        )

    def forward(self, x):
        return self.layers(x)
```

## 应用领域

| 领域 | 应用 | 进展 |
|------|------|------|
| 计算机视觉 | 图像识别、目标检测 | 成熟 |
| 自然语言处理 | 机器翻译、文本生成 | 快速发展 |
| 语音识别 | 语音助手、实时翻译 | 商业化 |

## 未来展望

> AI 技术将继续快速发展，为人类社会带来更多价值。

**关键趋势**：
1. 多模态学习
2. 可解释 AI
3. 边缘计算

## 结论

人工智能正处于快速发展阶段，未来充满机遇与挑战。
"""

    try:
        service = WeChatService()

        print("\n📝 正在转换 Markdown...")
        print(f"   内容长度: {len(markdown_content)} 字符")

        # 转换为三种主题
        themes = {
            'tech': '科技风（蓝紫渐变）',
            'minimal': '简约风（黑白灰）',
            'business': '商务风（深蓝金色）'
        }

        for theme, desc in themes.items():
            html_content, html_path = service.convert_markdown_to_html(
                markdown_content=markdown_content,
                theme=theme,
                output_filename=f"demo_{theme}.html"
            )

            print(f"\n✅ {desc}")
            print(f"   📄 文件: {html_path}")
            print(f"   📏 大小: {len(html_content)} 字符")

        print("\n💡 提示:")
        print("   在浏览器中打开 HTML 文件查看效果")
        print(f"   文件位置: {Path('output/wechat').absolute()}")

        return True

    except Exception as e:
        print(f"\n❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_api_usage():
    """演示：API 使用方法"""
    print("\n" + "=" * 70)
    print("演示 2: API 使用方法")
    print("=" * 70)

    print("\n📌 方法一：转换 Markdown 为 HTML")
    print("-" * 70)
    print("""
curl -X POST http://localhost:8000/api/wechat/convert \\
  -H "Content-Type: application/json" \\
  -d '{
    "markdown_content": "# 标题\\n\\n内容...",
    "theme": "tech",
    "output_filename": "my_article.html"
  }'
""")

    print("\n📌 方法二：转换历史报告")
    print("-" * 70)
    print("""
curl -X POST http://localhost:8000/api/wechat/convert-report \\
  -H "Content-Type: application/json" \\
  -d '{
    "filename": "report_20260224_123456_AI研究.md",
    "theme": "tech"
  }'
""")

    print("\n📌 方法三：一键转换并发布")
    print("-" * 70)
    print("""
curl -X POST http://localhost:8000/api/wechat/convert-and-publish \\
  -H "Content-Type: application/json" \\
  -d '{
    "markdown_content": "# 标题\\n\\n内容...",
    "title": "文章标题",
    "theme": "tech",
    "author": "Paper Agent"
  }'
""")


def demo_frontend_usage():
    """演示：前端使用方法"""
    print("\n" + "=" * 70)
    print("演示 3: 前端界面使用")
    print("=" * 70)

    print("\n📱 使用步骤:")
    print("-" * 70)
    print("""
1. 启动服务
   Windows: start.bat
   Linux/Mac: ./start.sh

2. 打开浏览器访问
   http://localhost:5173

3. 进入"历史报告"页面

4. 点击任意报告的"查看详情"

5. 点击右上角"📱 微信公众号"按钮

6. 在弹窗中：
   - 选择主题风格（科技风/简约风/商务风）
   - 点击"🔄 转换为 HTML"预览效果
   - 点击"🚀 一键发布到微信"发布到草稿箱

7. 在预览弹窗中：
   - 点击"📋 复制 HTML"复制内容
   - 点击"🌐 在浏览器中打开"查看完整效果
""")


def demo_theme_comparison():
    """演示：主题对比"""
    print("\n" + "=" * 70)
    print("演示 4: 三种主题风格对比")
    print("=" * 70)

    themes = [
        {
            'name': '科技风 (tech)',
            'color': '蓝紫渐变',
            'suitable': '技术文章、AI 研究、开发教程',
            'features': [
                '现代科技感',
                'Atom One Dark 代码高亮',
                '渐变色标题',
                '圆角卡片设计'
            ]
        },
        {
            'name': '简约风 (minimal)',
            'color': '黑白灰',
            'suitable': '学术论文、通用文章、简洁风格',
            'features': [
                '极简设计',
                'GitHub 风格代码块',
                '清晰的层次结构',
                '专注内容本身'
            ]
        },
        {
            'name': '商务风 (business)',
            'color': '深蓝金色',
            'suitable': '商业报告、行业分析、专业内容',
            'features': [
                '专业稳重',
                'Monokai 代码高亮',
                '金色点缀',
                '商务气质'
            ]
        }
    ]

    for i, theme in enumerate(themes, 1):
        print(f"\n{i}. {theme['name']}")
        print(f"   配色: {theme['color']}")
        print(f"   适合: {theme['suitable']}")
        print(f"   特点:")
        for feature in theme['features']:
            print(f"      - {feature}")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("  Paper Agent - 微信公众号功能演示")
    print("=" * 70)

    # 演示 1: 转换功能
    success = demo_convert()

    # 演示 2: API 使用
    demo_api_usage()

    # 演示 3: 前端使用
    demo_frontend_usage()

    # 演示 4: 主题对比
    demo_theme_comparison()

    # 总结
    print("\n" + "=" * 70)
    print("演示完成")
    print("=" * 70)

    if success:
        print("\n✅ 功能正常，已生成演示文件")
        print("\n📂 生成的文件:")
        print("   output/wechat/demo_tech.html      - 科技风")
        print("   output/wechat/demo_minimal.html   - 简约风")
        print("   output/wechat/demo_business.html  - 商务风")

        print("\n💡 下一步:")
        print("   1. 在浏览器中打开 HTML 文件查看效果")
        print("   2. 运行 start.bat 启动完整服务")
        print("   3. 在前端界面体验完整功能")
        print("   4. 查看 WECHAT_SETUP.md 了解详细配置")
    else:
        print("\n⚠️  演示过程中出现错误")
        print("   请检查依赖是否已安装:")
        print("   pip install -r wechat_article_skills/wechat-article-formatter/requirements.txt")

    print("\n📚 相关文档:")
    print("   - WECHAT_SETUP.md - 详细配置指南")
    print("   - WECHAT_UPDATE.md - 功能更新说明")
    print("   - WECHAT_INTEGRATION_SUMMARY.md - 集成总结")
    print()


if __name__ == "__main__":
    main()
