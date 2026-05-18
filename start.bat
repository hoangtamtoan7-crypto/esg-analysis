@echo off
chcp 65001 >nul
title ESG分析系统

echo ================================================
echo    ESG数据智能提取与分析系统
echo ================================================
echo.

:: 检查.env
if not exist .env (
    echo [提示] 未找到 .env 文件，请先运行 setup.bat
    pause
    exit /b 1
)

findstr /C:"your_deepseek_api_key_here" .env >nul 2>&1
if %errorlevel% equ 0 (
    echo [提示] .env 中API Key未配置，请先运行 setup.bat
    pause
    exit /b 1
)

echo 正在启动应用...
echo 浏览器将自动打开 http://localhost:8501
echo 按 Ctrl+C 可停止运行
echo.

streamlit run src\app\main.py --server.port 8501

pause
