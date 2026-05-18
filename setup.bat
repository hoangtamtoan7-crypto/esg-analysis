@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
title ESG分析系统 - 环境安装

echo ================================================
echo    ESG数据智能提取与分析系统 - 环境安装
echo ================================================
echo.

:: 检查Python
echo [1/3] 检查Python环境...
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

:: 安装依赖
echo [2/3] 安装Python依赖包...
pip install -r requirements.txt -q
if !errorlevel! neq 0 (
    echo [错误] 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)
echo 依赖安装完成！
echo.

:: 配置API Key
echo [3/3] 配置DeepSeek API Key...
if exist .env (
    findstr /C:"your_deepseek_api_key_here" .env >nul 2>&1
    if !errorlevel! equ 0 (
        set /p APIKEY="请输入DeepSeek API Key (从 https://platform.deepseek.com/ 获取): "
        echo DEEPSEEK_API_KEY=!APIKEY! > .env
        echo API Key 已保存！
    ) else (
        echo .env 已配置，跳过
    )
) else (
    set /p APIKEY="请输入DeepSeek API Key (从 https://platform.deepseek.com/ 获取): "
    echo DEEPSEEK_API_KEY=!APIKEY! > .env
    echo API Key 已保存！
)

echo.
echo ================================================
echo 安装完成！双击 start.bat 启动系统
echo ================================================
pause
