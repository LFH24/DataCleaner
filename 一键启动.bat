@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ============================================
echo   自动化数据预处理工具
echo ============================================
echo.
echo 正在启动 GUI 界面...
echo.
if exist "dist\DataCleaner.exe" (
    start "" "dist\DataCleaner.exe"
    echo 已启动!
) else if exist "main.py" (
    echo 首次运行，正在安装依赖...
    pip install -r requirements.txt -q
    echo.
    python main.py
) else (
    echo [错误] 找不到可执行文件，请检查文件完整性。
    pause
)
