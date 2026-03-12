# Linux 部署指南

本文档介绍如何在 Linux 服务器上部署 Paper Analysis Agent 项目。

---

## 系统要求

- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- **Python**: 3.10 或更高版本
- **Node.js**: 18.x 或更高版本
- **内存**: 建议 4GB+
- **磁盘**: 建议 10GB+ 可用空间

---

## 端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端 API | 8002 | FastAPI 服务端口 |
| 前端开发服务器 | 5173 | Vite 开发服务器（仅开发环境）|
| 前端生产环境 | 80/443 | Nginx 反向代理（生产环境）|

---

## 部署步骤

### 1. 安装系统依赖

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-pip python3.10-venv nodejs npm git

# CentOS/RHEL
sudo yum install -y python3.10 python3.10-pip nodejs npm git
```

### 2. 安装 Poetry

```bash
# 安装 Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 添加到 PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 验证安装
poetry --version
```

### 3. 克隆项目

```bash
# 克隆仓库
git clone <your-repo-url> paper-analysis-agent
cd paper-analysis-agent
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp example.env .env

# 编辑 .env 文件，设置必要的 API 密钥
vi .env
```

**必须配置的变量：**

```env
# API Keys (至少配置一个)
DASHSCOPE_API_KEY=your_dashscope_key_here
# 或
SILICONFLOW_API_KEY=your_siliconflow_key_here

# 其他可选配置
DEFAULT_MODEL_PROVIDER=dashscope
DEFAULT_MODEL=Qwen/Qwen3-32B
```

### 5. 安装 Python 依赖

```bash
# 使用 Poetry 安装依赖
poetry install --no-root

# 验证安装
poetry run python -c "import src; print('OK')"
```

### 6. 安装前端依赖

```bash
cd web

# 使用 npm 安装依赖
npm install

# 或如果使用 pnpm
pnpm install

cd ..
```

---

## 运行方式

### 开发环境运行

#### 方式一：同时运行前后端（推荐开发使用）

```bash
# 在项目根目录运行
poetry run python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload &
cd web && npm run dev &
```

访问地址：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8002

#### 方式二：分别运行（推荐）

**终端 1 - 运行后端：**
```bash
cd /path/to/paper-analysis-agent
poetry run python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

**终端 2 - 运行前端：**
```bash
cd /path/to/paper-analysis-agent/web
npm run dev -- --host 0.0.0.0
```

---

### 生产环境运行

#### 1. 构建前端

```bash
cd web
npm run build
cd ..
```

构建后的文件位于 `web/dist/` 目录。

#### 2. 使用 Gunicorn 运行后端

```bash
# 安装 gunicorn
poetry add gunicorn

# 使用 gunicorn 运行（推荐）
poetry run gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8002 \
  --daemon \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --pid gunicorn.pid
```

#### 3. 使用 Nginx 反向代理

安装 Nginx：
```bash
# Ubuntu/Debian
sudo apt-get install -y nginx

# CentOS/RHEL
sudo yum install -y nginx
```

创建 Nginx 配置文件：
```bash
sudo vi /etc/nginx/sites-available/paper-agent
```

配置内容：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/paper-analysis-agent/web/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://localhost:8002/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # 知识库 API 代理
    location /knowledge/ {
        proxy_pass http://localhost:8002/knowledge/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # SSE 支持
    location /api/research {
        proxy_pass http://localhost:8002/api/research;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/paper-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 使用 Systemd 管理服务

### 创建后端服务

```bash
sudo vi /etc/systemd/system/paper-agent-backend.service
```

内容：
```ini
[Unit]
Description=Paper Analysis Agent Backend
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/paper-analysis-agent
Environment=PATH=/path/to/.local/bin:/usr/local/bin:/usr/bin
ExecStart=/path/to/.local/bin/poetry run python -m uvicorn main:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 管理服务

```bash
# 启动服务
sudo systemctl start paper-agent-backend

# 停止服务
sudo systemctl stop paper-agent-backend

# 重启服务
sudo systemctl restart paper-agent-backend

# 查看状态
sudo systemctl status paper-agent-backend

# 开机自启
sudo systemctl enable paper-agent-backend

# 查看日志
sudo journalctl -u paper-agent-backend -f
```

---

## 使用 Docker 部署（可选）

### 创建 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装 Poetry
RUN pip install poetry

# 复制项目文件
COPY pyproject.toml poetry.lock ./
COPY src ./src
COPY main.py ./
COPY .env ./

# 安装依赖
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-dev

# 暴露端口
EXPOSE 8002

# 启动命令
CMD ["poetry", "run", "python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
```

### 构建和运行

```bash
# 构建镜像
docker build -t paper-agent:latest .

# 运行容器
docker run -d \
  --name paper-agent \
  -p 8002:8002 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  paper-agent:latest

# 查看日志
docker logs -f paper-agent
```

---

## 常用命令

### Poetry 命令

```bash
# 激活虚拟环境
poetry shell

# 运行 Python 脚本
poetry run python script.py

# 添加依赖
poetry add package-name

# 更新依赖
poetry update

# 查看依赖树
poetry show --tree
```

### 日志查看

```bash
# 后端日志（Systemd）
sudo journalctl -u paper-agent-backend -f

# Nginx 访问日志
sudo tail -f /var/log/nginx/access.log

# Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# 应用日志
tail -f logs/project.log
```

---

## 防火墙配置

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8002/tcp
sudo ufw enable

# CentOS/RHEL (Firewalld)
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=8002/tcp
sudo firewall-cmd --reload
```

---

## 故障排查

### 1. 端口被占用

```bash
# 检查端口占用
sudo lsof -i :8002

# 结束进程
sudo kill -9 <PID>
```

### 2. 权限问题

```bash
# 修复文件权限
sudo chown -R $USER:$USER /path/to/paper-analysis-agent

# 确保 Poetry 可执行
chmod +x $HOME/.local/bin/poetry
```

### 3. 依赖安装失败

```bash
# 清除缓存重新安装
poetry cache clear --all
poetry install --no-root

# 如果仍失败，尝试使用 pip
poetry export -f requirements.txt --output requirements.txt
pip install -r requirements.txt
```

### 4. Nginx 502 错误

```bash
# 检查后端是否运行
curl http://localhost:8002/health

# 检查 Nginx 配置
sudo nginx -t

# 重启服务
sudo systemctl restart paper-agent-backend
sudo systemctl restart nginx
```

---

## 更新部署

```bash
cd /path/to/paper-analysis-agent

# 拉取最新代码
git pull origin main

# 更新后端依赖
poetry install --no-root

# 更新前端依赖
cd web && npm install && cd ..

# 重启服务
sudo systemctl restart paper-agent-backend

# 重新构建前端（生产环境）
cd web && npm run build && cd ..
```

---

## 安全建议

1. **使用 HTTPS**: 生产环境配置 SSL 证书
2. **限制端口访问**: 8002 端口只对本地开放，通过 Nginx 反向代理
3. **环境变量保护**: `.env` 文件设置 600 权限
4. **定期备份**: 备份 `data/` 目录和 `.env` 文件
5. **日志监控**: 配置日志轮转防止磁盘占满

---

## 参考链接

- [Poetry 文档](https://python-poetry.org/docs/)
- [FastAPI 部署](https://fastapi.tiangolo.com/deployment/)
- [Nginx 配置](https://nginx.org/en/docs/)
