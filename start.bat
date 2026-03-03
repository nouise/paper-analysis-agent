@echo off
chcp 65001 >nul
echo ========================================
echo   Paper Agent - 启动脚本
echo ========================================
echo.

echo [1/3] 检查依赖...
python -c "import markdown, beautifulsoup4, cssutils" 2>nul
if errorlevel 1 (
    echo ⚠️  检测到缺少微信功能依赖
    echo.
    set /p install="是否安装微信功能依赖？(Y/n): "
    if /i "%install%"=="Y" (
        echo 正在安装依赖...
        cd wechat_article_skills\wechat-article-formatter
        pip install -r requirements.txt
        cd ..\..
        echo ✅ 依赖安装完成
    )
)

echo.
echo [2/3] 启动后端服务...
start "Paper Agent Backend" cmd /k "python main.py"
timeout /t 3 >nul

echo.
echo [3/3] 启动前端服务...
cd web
start "Paper Agent Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ========================================
echo   ✅ 服务启动完成！
echo ========================================
echo.
echo 📌 后端地址: http://localhost:8000
echo 📌 前端地址: http://localhost:5173
echo.
echo 💡 提示:
echo    - 在浏览器中打开前端地址开始使用
echo    - 历史报告页面可使用微信公众号功能
echo    - 详细文档: WECHAT_SETUP.md
echo.
echo 按任意键退出...
pause >nul
