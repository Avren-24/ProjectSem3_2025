@echo off
chcp 65001 >nul
echo ============================================================
echo Installing Python Dependencies
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo [System] Python found
python --version

echo.
echo [System] Checking pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [Error] pip is not installed
    echo Please install pip or reinstall Python with pip included
    echo.
    pause
    exit /b 1
)

echo.
echo [System] Upgrading pip to latest version...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo [Warning] Failed to upgrade pip, continuing with current version...
)

echo.
echo [System] Checking requirements.txt...
if not exist requirements.txt (
    echo [Warning] requirements.txt not found.
    echo [System] Installing required package: paramiko
    python -m pip install paramiko>=2.12.0
    if errorlevel 1 (
        echo [Error] Failed to install paramiko
        pause
        exit /b 1
    )
    echo.
    echo ============================================================
    echo Installation completed successfully!
    echo ============================================================
    echo.
    echo Next steps:
    echo 1. Configure raspberry_pi_config.txt with your Raspberry Pi connection details
    echo 2. Run humidity_monitor.py in PyCharm
    echo.
    pause
    exit /b 0
)

echo [System] Installing required packages from requirements.txt...
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [Error] Failed to install dependencies
    echo Please check the error messages above
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Installation completed successfully!
echo ============================================================
echo.
echo Next steps:
echo 1. Configure raspberry_pi_config.txt with your Raspberry Pi connection details
echo 2. Run humidity_monitor.py in PyCharm
echo 3. The script will connect to Raspberry Pi and read real sensor data
echo 4. Email alerts will be sent automatically when humidity drops below 30%%
echo.
pause

