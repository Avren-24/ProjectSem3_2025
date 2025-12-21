# Quick Start Guide

## Step 1: Install Dependencies

Double-click to run `install_dependencies.bat` and wait for installation to complete.

## Step 2: Configure Raspberry Pi Connection

Edit the `raspberry_pi_config.txt` file:

```
HOSTNAME=192.168.1.100    # Change to your Raspberry Pi IP address
USERNAME=pi                # Change to your SSH username
PASSWORD=your_password     # Change to your SSH password
PORT=22                    # Usually no need to change
```

## Step 3: Run in PyCharm

1. Open PyCharm
2. Open the project folder
3. Run `sensor_reader.py`
4. The program will automatically connect to Raspberry Pi and read 10 data sets

## Raspberry Pi Setup

Execute the following commands on Raspberry Pi:

```bash
# 1. Enable I2C
sudo raspi-config
# Select: Interfacing Options → I2C → Enable

# 2. Install I2C tools
sudo apt-get update
sudo apt-get install -y i2c-tools python3-pip

# 3. Install ADS1115 library
pip3 install Adafruit-ADS1x15

# 4. Check if ADS1115 is connected (should see 0x48)
i2cdetect -y 1

# 5. Ensure SSH is enabled
sudo systemctl enable ssh
sudo systemctl start ssh
```

## Hardware Connections

- **ADS1115 → Raspberry Pi**:
  - VDD → 3.3V
  - GND → GND  
  - SCL → GPIO 3 (Physical pin 5)
  - SDA → GPIO 2 (Physical pin 3)

- **Humidity Sensor → ADS1115**:
  - Sensor output → A0 channel
  - Sensor power → 3.3V or 5V
  - Sensor ground → GND

## Common Issues

**Q: What to do if connection fails?**
A: Check Raspberry Pi IP address, whether SSH is enabled, and firewall settings

**Q: ADS1115 not detected?**
A: Run `i2cdetect -y 1` to check, confirm I2C is enabled

**Q: Data reading incorrect?**
A: Check sensor connections, may need to adjust conversion formula according to actual sensor
