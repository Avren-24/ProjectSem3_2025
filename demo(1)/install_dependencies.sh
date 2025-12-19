#!/bin/bash
# Linux/Mac安装脚本（备用）

echo "============================================================"
echo "Installing Python Dependencies"
echo "============================================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "[Error] Python 3 is not installed"
    exit 1
fi

echo "[System] Python found"
python3 --version

echo ""
echo "[System] Upgrading pip..."
python3 -m pip install --upgrade pip --quiet

echo ""
echo "[System] Installing required packages..."
python3 -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "[Error] Failed to install dependencies"
    exit 1
fi

echo ""
echo "============================================================"
echo "Installation completed successfully!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Edit raspberry_pi_config.txt with your Raspberry Pi connection details"
echo "2. Run sensor_reader.py"
echo ""

