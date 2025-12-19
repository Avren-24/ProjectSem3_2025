#!/bin/bash
# Mac/Linux Installation Script

echo "============================================================"
echo "Installing Python Dependencies"
echo "============================================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "[Error] Python 3 is not installed"
    echo "Please install Python 3.7+ from https://www.python.org/"
    echo ""
    exit 1
fi

echo "[System] Python found"
python3 --version

echo ""
echo "[System] Checking pip..."
if ! python3 -m pip --version &> /dev/null; then
    echo "[Error] pip is not installed"
    echo "Please install pip or reinstall Python with pip included"
    echo ""
    exit 1
fi

echo ""
echo "[System] Upgrading pip to latest version..."
python3 -m pip install --upgrade pip --quiet
if [ $? -ne 0 ]; then
    echo "[Warning] Failed to upgrade pip, continuing with current version..."
fi

echo ""
echo "[System] Checking requirements.txt..."
if [ ! -f requirements.txt ]; then
    echo "[Warning] requirements.txt not found."
    echo "[System] Installing required package: paramiko"
    python3 -m pip install paramiko>=2.12.0
    if [ $? -ne 0 ]; then
        echo "[Error] Failed to install paramiko"
        exit 1
    fi
    echo ""
    echo "============================================================"
    echo "Installation completed successfully!"
    echo "============================================================"
    echo ""
    echo "Next steps:"
    echo "1. Configure raspberry_pi_config.txt with your Raspberry Pi connection details"
    echo "2. Run humidity_monitor.py in PyCharm or terminal"
    echo ""
    exit 0
fi

echo "[System] Installing required packages from requirements.txt..."
python3 -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "[Error] Failed to install dependencies"
    echo "Please check the error messages above"
    echo ""
    exit 1
fi

echo ""
echo "============================================================"
echo "Installation completed successfully!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Configure raspberry_pi_config.txt with your Raspberry Pi connection details"
echo "2. Run humidity_monitor.py in PyCharm or terminal"
echo "3. The script will connect to Raspberry Pi and read real sensor data"
echo "4. Email alerts will be sent automatically when humidity drops below 30%"
echo ""

