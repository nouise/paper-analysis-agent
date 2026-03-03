# 微信公众号集成配置指南

本文档介绍如何配置 Paper Agent 的微信公众号发布功能。

## 功能概述

Paper Agent 现已集成微信公众号发布功能，支持：

- ✅ **Markdown 转微信 HTML**：将报告转换为适合微信公众号的美化 HTML
- ✅ **三种主题风格**：科技风、简约风、商务风
- ✅ **前端预览**：在浏览器中预览转换效果
- ✅ **一键发布**：直接发布到微信公众号草稿箱

---

## 一、安装依赖

### 1. 安装 Python 依赖

```bash
# 进入 wechat-article-formatter 目录
cd wechat_article_skills/wechat-article-formatter

# 安装依赖
pip install -r requirements.txt
```

依赖包括：
- `markdown` - Markdown 解析
- `beautifulsoup4` - HTML 处理
- `cssutils` - CSS 解析
- `lxml` - XML/HTML 解析
- `watchdog` - 文件监听
- `Pygments` - 代码高亮

### 2. 安装微信发布工具依赖

```bash
# 返回项目根目录
cd ../..

# 安装 requests（如果未安装）
pip install requests
```

---

## 二、配置微信公众号凭证

### 1. 获取 AppID 和 AppSecret

1. 登录 [微信公众平台](https://mp.weixin.qq.com)
2. 进入 **设置与开发 → 基本配置**
3. 复制 **AppID** 和 **AppSecret**

### 2. 配置凭证

**方式一：自动配置（推荐）**

首次使用发布功能时，系统会自动引导你配置：

```bash
# 运行后端服务
python main.py

# 在前端点击"一键发布到微信"，系统会提示配置
```

**方式二：手动配置**

创建配置文件 `~/.wechat-publisher/config.json`：

```json
{
  "appid": "wx1234567890abcdef",
  "appsecret": "your_appsecret_here"
}
```

**Windows 路径**：`C:\Users\你的用户名\.wechat-publisher\config.json`

**Linux/Mac 路径**：`~/.wechat-publisher/config.json`

### 3. 配置 IP 白名单

1. 登录微信公众平台
2. 进入 **设置与开发 → 基本配置 → IP 白名单**
3. 添加你的服务器 IP 地址

**获取本机 IP**：
```bash
# Windows
ipconfig

# Linux/Mac
ifconfig
```

---

## 三、使用方法

### 1. 启动后端服务

```bash
python main.py
```

后端将在 `http://localhost:8000` 运行。

### 2. 启动前端服务

```bash
cd web
npm install  # 首次运行
npm run dev
```

前端将在 `http://localhost:5173` 运行。

### 3. 转换和发布

#### 方法一：通过前端界面

1. 打开 **历史报告** 页面
2. 点击任意报告的 **查看详情**
3. 点击右上角 **📱 微信公众号** 按钮
4. 选择主题风格（科技风/简约风/商务风）
5. 点击 **🔄 转换为 HTML** 预览效果
6. 点击 **🚀 一键发布到微信** 发布到草稿箱

#### 方法二：通过 API

**转换为 HTML**：
```bash
curl -X POST http://localhost:8000/api/wechat/convert-report \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "report_20260224_123456_AI研究.md",
    "theme": "tech"
  }'
```

**发布到微信**：
```bash
curl -X POST http://localhost:8000/api/wechat/convert-and-publish \
  -H "Content-Type: application/json" \
  -d '{
    "markdown_content": "# 标题\n\n内容...",
    "title": "文章标题",
    "theme": "tech",
    "author": "Paper Agent"
  }'
```

---

## 四、主题风格说明

### 1. 科技风 (tech)
- **配色**：蓝紫渐变
- **适用**：技术文章、AI 研究、开发教程
- **特点**：现代科技感，Atom One Dark 代码高亮

### 2. 简约风 (minimal)
- **配色**：黑白灰
- **适用**：通用文章、学术论文、简洁风格
- **特点**：极简设计，GitHub 风格代码块

### 3. 商务风 (business)
- **配色**：深蓝金色
- **适用**：商业分析、行业报告、专业内容
- **特点**：专业稳重，Monokai 代码高亮

---

## 五、输出文件位置

转换后的文件保存在：

```
output/
├── reports/          # 原始 Markdown 报告
└── wechat/          # 转换后的 HTML 文件
    ├── 文章标题.html
    └── ...
```

---

## 六、发布流程

### 自动发布流程

1. **转换 Markdown → HTML**
   - 移除 H1 标题（微信有独立标题输入框）
   - 应用主题样式
   - 内联所有 CSS

2. **上传图片**
   - 自动上传封面图片（如果提供）
   - 上传内容中的本地图片
   - 替换为微信 CDN 链接

3. **创建草稿**
   - 调用微信 API 创建草稿
   - 返回 media_id

4. **完成**
   - 前往微信公众号后台查看草稿
   - 可在编辑器中进一步调整

### 手动发布流程

如果不使用自动发布，可以手动操作：

1. 点击 **🔄 转换为 HTML**
2. 点击 **📋 复制 HTML**
3. 在浏览器中打开 HTML 文件预览
4. 按 `Ctrl+A` 全选，`Ctrl+C` 复制
5. 粘贴到微信公众号编辑器
6. 重新上传图片（本地图片无法显示）
7. 调整格式后发布

---

## 七、常见问题

### 1. 转换失败

**错误**：`ModuleNotFoundError: No module named 'markdown'`

**解决**：
```bash
pip install -r wechat_article_skills/wechat-article-formatter/requirements.txt
```

### 2. 发布失败：AppSecret 错误

**错误**：`AppSecret错误或者AppSecret不属于这个AppID`

**解决**：
1. 检查配置文件中的 AppID 和 AppSecret 是否正确
2. 确认 AppID 以 `wx` 开头，长度为 18 位
3. 重新从微信公众平台复制凭证

### 3. 发布失败：IP 不在白名单

**错误**：`调用接口的IP地址不在白名单中`

**解决**：
1. 登录微信公众平台
2. 设置与开发 → 基本配置 → IP 白名单
3. 添加你的服务器 IP

### 4. 图片无法显示

**原因**：本地图片路径在微信编辑器中无法访问

**解决**：
- 使用自动发布功能（会自动上传图片）
- 或手动在微信编辑器中重新上传图片

### 5. 样式丢失

**原因**：微信编辑器会重置部分样式

**解决**：
- 本工具已针对微信编辑器优化
- 所有样式使用 `!important` 强制应用
- 背景色区块转换为 `<table>` 结构

---

## 八、API 接口文档

### 1. 转换报告为 HTML

**接口**：`POST /api/wechat/convert-report`

**请求体**：
```json
{
  "filename": "report_20260224_123456_AI研究.md",
  "theme": "tech"
}
```

**响应**：
```json
{
  "status": 200,
  "msg": "转换成功",
  "html_content": "<html>...",
  "html_path": "output/wechat/AI研究.html",
  "title": "AI研究综述"
}
```

### 2. 发布到微信

**接口**：`POST /api/wechat/publish`

**请求体**：
```json
{
  "title": "文章标题",
  "html_content": "<html>...",
  "author": "Paper Agent",
  "cover_image_path": "/path/to/cover.png",
  "digest": "文章摘要"
}
```

**响应**：
```json
{
  "status": 200,
  "msg": "发布成功",
  "result": {
    "media_id": "xxx"
  }
}
```

### 3. 一键转换并发布

**接口**：`POST /api/wechat/convert-and-publish`

**请求体**：
```json
{
  "markdown_content": "# 标题\n\n内容...",
  "title": "文章标题",
  "theme": "tech",
  "author": "Paper Agent"
}
```

---

## 九、注意事项

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

---

## 十、技术架构

```
Paper Agent
├── src/services/wechat_service.py    # 微信服务封装
├── main.py                            # FastAPI 后端（新增 API）
├── web/src/views/History.vue          # 前端界面（新增按钮）
└── wechat_article_skills/             # 微信工具集
    ├── wechat-article-formatter/      # Markdown → HTML 转换
    │   ├── scripts/markdown_to_html.py
    │   └── templates/*.css            # 主题样式
    └── wechat-draft-publisher/        # 微信发布工具
        └── publisher.py
```

---

## 十一、更新日志

### v1.0.0 (2026-02-24)
- ✅ 集成 Markdown 转 HTML 功能
- ✅ 支持三种主题风格
- ✅ 前端添加微信公众号按钮
- ✅ 实现一键发布到草稿箱
- ✅ 自动上传图片到微信 CDN
- ✅ 优化微信编辑器兼容性

---

## 十二、参考资源

- [微信公众平台开发文档](https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Overview.html)
- [微信公众号 API 文档](https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Add_draft.html)
- [wechat-article-formatter 文档](wechat_article_skills/wechat-article-formatter/README.md)

---

**祝你使用愉快！** 🎉

如有问题，请查看日志文件 `project.log` 或提交 Issue。
