# Installation Guide

## Quick Start

### Windows Users

1. Double-click `install_dependencies.bat`
2. Wait for the installation to complete
3. Run `humidity_monitor.py` in PyCharm

### Mac Users

1. Open Terminal
2. Navigate to the project directory:
   ```bash
   cd /path/to/demo
   ```
3. Run the installation script:
   ```bash
   ./install_dependencies.sh
   ```
   Or if you get a permission error:
   ```bash
   chmod +x install_dependencies.sh
   ./install_dependencies.sh
   ```
4. Run `humidity_monitor.py` in PyCharm or terminal

## Manual Installation

If the automated scripts don't work, you can install dependencies manually:

### Windows
```cmd
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Mac/Linux
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## Requirements

- Python 3.7 or higher
- pip (usually included with Python)

## Note

The `humidity_monitor.py` script uses only Python standard library modules:
- `time`
- `sys`
- `random`
- `smtplib`
- `datetime`
- `email`

No additional packages are required unless you have a `requirements.txt` file with other dependencies.

## Troubleshooting

### Python not found
- **Windows**: Install Python from https://www.python.org/ and check "Add Python to PATH" during installation
- **Mac**: Install Python using Homebrew: `brew install python3` or download from python.org

### pip not found
- Reinstall Python with pip included
- Or install pip separately following the official guide

### Permission errors (Mac/Linux)
- Use `sudo` if needed: `sudo python3 -m pip install -r requirements.txt`
- Or use `--user` flag: `python3 -m pip install --user -r requirements.txt`

