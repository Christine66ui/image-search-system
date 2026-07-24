@echo off
chcp 65001 >nul
echo ========================================
echo    产品图片检索系统 - 启动脚本
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [2/4] 检查依赖包...
python -c "import torch, flask, sklearn" >nul 2>&1
if errorlevel 1 (
    echo 依赖包未安装，正在安装...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo 安装失败，请手动运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo [3/4] 运行配置检查...
python test.py
if errorlevel 1 (
    echo 配置检查发现问题，请修复后再启动
    pause
    exit /b 1
)

echo [4/4] 启动服务...
echo.
echo ========================================
echo   服务启动中，请稍候...
echo   首次启动需要建立索引，可能需要几分钟
echo ========================================
echo.

python app.py

pause
