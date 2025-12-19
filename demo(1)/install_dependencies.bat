@echo off
chcp 65001 >nul
echo ============================================================
echo Installing Python Dependencies
echo ============================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://www.python.org/
    pause
    exit /b 1
)

echo [System] Python found
python --version

echo.
echo [System] Upgrading pip...
python -m pip install --upgrade pip --quiet

echo.
echo [System] Installing required packages...
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [Error] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Installation completed successfully!
echo ============================================================
echo.
echo Next steps:
echo 1. Edit raspberry_pi_config.txt with your Raspberry Pi connection details
echo 2. Run sensor_reader.py in PyCharm
echo.
pause

