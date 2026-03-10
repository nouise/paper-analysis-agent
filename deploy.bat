@echo off
chcp 65001 >nul
echo ==========================================
echo   Paper Analysis Agent 部署脚本
echo ==========================================
echo.

:: 检查 .env 文件
if not exist .env (
    echo [错误] 未找到 .env 文件，请从 example.env 复制并配置 API Key
    echo.
    echo 请执行: copy example.env .env
    echo 然后编辑 .env 文件填入你的 API Key
    exit /b 1
)

:: 创建输出目录
if not exist output\reports mkdir output\reports
if not exist output\log mkdir output\log

echo [1/2] 启动后端服务 (端口 8000)...
echo.
start "Paper Agent Backend" cmd /c "poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: 等待后端启动
timeout /t 3 /nobreak >nul

echo [2/2] 启动前端服务 (端口 5173)...
echo.
cd web
start "Paper Agent Frontend" cmd /c "npm run dev"

echo.
echo ==========================================
echo   服务启动成功！
echo ==========================================
echo.
echo 后端 API: http://localhost:8000
echo 前端页面: http://localhost:5173
echo.
echo 按任意键关闭所有服务...
pause >nul

:: 关闭进程
taskkill /FI "WindowTitle eq Paper Agent Backend*" /F 2>nul
taskkill /FI "WindowTitle eq Paper Agent Frontend*" /F 2>nul
taskkill /IM python.exe /F 2>nul

echo 服务已关闭
