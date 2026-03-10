#!/bin/bash

echo "=========================================="
echo "  Paper Analysis Agent 部署脚本"
echo "=========================================="
echo ""

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "[错误] 未找到 .env 文件，请从 example.env 复制并配置 API Key"
    echo ""
    echo "请执行: cp example.env .env"
    echo "然后编辑 .env 文件填入你的 API Key"
    exit 1
fi

# 创建输出目录
mkdir -p output/reports
mkdir -p output/log

echo "[1/2] 启动后端服务 (端口 8000)..."
echo ""
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

echo "[2/2] 启动前端服务 (端口 5173)..."
echo ""
cd web
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "  服务启动成功！"
echo "=========================================="
echo ""
echo "后端 API: http://localhost:8000"
echo "前端页面: http://localhost:5173"
echo ""
echo "按 Ctrl+C 关闭所有服务..."

# 捕获退出信号
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

# 等待进程
wait
