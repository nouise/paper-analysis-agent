# Paper Agent - 微信公众号功能更新说明

## 更新内容

本次更新为 Paper Agent 添加了完整的微信公众号集成功能，支持将生成的研究报告一键转换为微信公众号格式并发布。

## 新增功能

### 1. 后端服务

**新增文件**：
- `src/services/wechat_service.py` - 微信服务封装类
- `test_wechat.py` - 功能测试脚本
- `WECHAT_SETUP.md` - 详细配置文档

**新增 API 接口**（`main.py`）：
- `POST /api/wechat/convert` - 转换 Markdown 为 HTML
- `POST /api/wechat/publish` - 发布到微信草稿箱
- `POST /api/wechat/convert-and-publish` - 一键转换并发布
- `POST /api/wechat/convert-report` - 转换历史报告

### 2. 前端界面

**更新文件**：
- `web/src/views/History.vue` - 历史报告页面

**新增功能**：
- 📱 微信公众号按钮（报告详情页）
- 🎨 主题选择弹窗（科技风/简约风/商务风）
- 🔄 转换为 HTML 功能
- 🚀 一键发布到微信功能
- 👁️ HTML 预览弹窗

### 3. 微信工具集成

**集成目录**：
- `wechat_article_skills/wechat-article-formatter/` - Markdown 转 HTML 工具
- `wechat_article_skills/wechat-draft-publisher/` - 微信发布工具

**支持的主题**：
- **tech**（科技风）：蓝紫渐变，适合技术文章
- **minimal**（简约风）：黑白灰，适合学术论文
- **business**（商务风）：深蓝金色，适合商业报告

## 使用流程

### 方式一：通过前端界面（推荐）

1. 启动后端和前端服务
2. 打开历史报告页面
3. 点击任意报告的"查看详情"
4. 点击右上角"📱 微信公众号"按钮
5. 选择主题风格
6. 点击"🔄 转换为 HTML"预览效果
7. 点击"🚀 一键发布到微信"发布到草稿箱

### 方式二：通过 API

```bash
# 转换报告为 HTML
curl -X POST http://localhost:8000/api/wechat/convert-report \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "report_xxx.md",
    "theme": "tech"
  }'

# 一键发布
curl -X POST http://localhost:8000/api/wechat/convert-and-publish \
  -H "Content-Type: application/json" \
  -d '{
    "markdown_content": "# 标题\n\n内容...",
    "title": "文章标题",
    "theme": "tech"
  }'
```

## 配置要求

### 1. 安装依赖

```bash
# 安装微信转换工具依赖
cd wechat_article_skills/wechat-article-formatter
pip install -r requirements.txt
```

### 2. 配置微信公众号凭证（可选）

如果需要使用一键发布功能，需要配置微信公众号凭证：

1. 登录 [微信公众平台](https://mp.weixin.qq.com)
2. 获取 AppID 和 AppSecret
3. 创建配置文件 `~/.wechat-publisher/config.json`：

```json
{
  "appid": "wx1234567890abcdef",
  "appsecret": "your_appsecret_here"
}
```

4. 配置 IP 白名单（在微信公众平台后台）

**注意**：如果只使用转换功能（不发布），无需配置微信凭证。

## 测试验证

运行测试脚本验证功能：

```bash
python test_wechat.py
```

测试内容：
- ✅ Markdown 转 HTML 功能
- ✅ 转换历史报告功能
- ⚠️ 微信配置检查（需要配置凭证）

## 输出文件

转换后的文件保存在：

```
output/
├── reports/          # 原始 Markdown 报告
└── wechat/          # 转换后的 HTML 文件
    ├── 文章标题.html
    └── test_article.html
```

## 技术实现

### 后端架构

```python
WeChatService
├── convert_markdown_to_html()    # Markdown → HTML 转换
├── publish_to_wechat()            # 发布到微信草稿箱
└── convert_and_publish()          # 一键转换并发布
```

### 前端组件

```vue
History.vue
├── showWechatModal              # 微信转换弹窗
├── convertToWechat()            # 转换功能
├── publishToWechat()            # 发布功能
└── showHtmlPreview              # HTML 预览弹窗
```

### 转换流程

1. **读取 Markdown**：从报告文件或用户输入读取内容
2. **解析转换**：使用 `markdown` 库解析，应用主题 CSS
3. **内联样式**：将所有 CSS 转换为内联样式（微信要求）
4. **优化兼容**：移除不支持的 CSS 属性，优化布局
5. **生成 HTML**：输出完整的 HTML 文件

### 发布流程

1. **转换 HTML**：先将 Markdown 转换为 HTML
2. **上传图片**：自动上传封面和内容图片到微信 CDN
3. **创建草稿**：调用微信 API 创建草稿文章
4. **返回结果**：返回 media_id 供用户在后台查看

## 注意事项

### 微信公众号限制

1. **不支持外部 CSS**：本工具自动转换为内联样式
2. **不支持 JavaScript**：使用纯 CSS 实现效果
3. **图片需重新上传**：本地图片无法直接使用（自动发布会处理）
4. **部分 CSS 属性不支持**：已过滤不支持的属性

### 最佳实践

1. **文章长度**：建议 2000-5000 字
2. **图片数量**：建议 4-8 张
3. **表格列数**：建议 ≤ 4 列（移动端友好）
4. **代码块长度**：建议 < 30 行

## 常见问题

### Q1: 转换失败，提示找不到模块

**A**: 需要安装依赖：
```bash
pip install -r wechat_article_skills/wechat-article-formatter/requirements.txt
```

### Q2: 发布失败，提示 AppSecret 错误

**A**: 检查配置文件 `~/.wechat-publisher/config.json` 中的凭证是否正确。

### Q3: 发布失败，提示 IP 不在白名单

**A**: 需要在微信公众平台后台添加服务器 IP 到白名单。

### Q4: 图片无法显示

**A**:
- 使用自动发布功能（会自动上传图片）
- 或手动在微信编辑器中重新上传图片

### Q5: 样式丢失或错位

**A**: 本工具已针对微信编辑器优化，如仍有问题：
- 尝试切换不同主题
- 在微信编辑器中微调样式

## 详细文档

完整的配置和使用说明请查看：
- [WECHAT_SETUP.md](WECHAT_SETUP.md) - 详细配置指南
- [wechat-article-formatter/README.md](wechat_article_skills/wechat-article-formatter/README.md) - 转换工具文档
- [wechat-draft-publisher/README.md](wechat_article_skills/wechat-draft-publisher/README.md) - 发布工具文档

## 更新日志

### v1.0.0 (2026-02-24)
- ✅ 集成 Markdown 转 HTML 功能
- ✅ 支持三种主题风格
- ✅ 前端添加微信公众号按钮
- ✅ 实现一键发布到草稿箱
- ✅ 自动上传图片到微信 CDN
- ✅ 优化微信编辑器兼容性
- ✅ 添加测试脚本和文档

## 反馈与支持

如有问题或建议，请：
1. 查看日志文件 `project.log`
2. 运行测试脚本 `python test_wechat.py`
3. 查看详细文档 `WECHAT_SETUP.md`
4. 提交 Issue 到项目仓库

---

**祝你使用愉快！** 🎉
