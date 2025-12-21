# Humidity Sensor Data Acquisition System

Connect to Raspberry Pi via SSH to read real data from ADS1115 ADC module and humidity sensor.

## System Requirements

- Windows 10/11
- Python 3.7+
- PyCharm (recommended)
- Raspberry Pi (SSH enabled)
- ADS1115 ADC Module
- Humidity Sensor

## Hardware Connections

1. **ADS1115 to Raspberry Pi**:
   - VDD → 3.3V
   - GND → GND
   - SCL → GPIO 3 (SCL)
   - SDA → GPIO 2 (SDA)

2. **Humidity Sensor to ADS1115**:
   - Sensor output → ADS1115 A0 channel
   - Sensor power → 3.3V or 5V (according to sensor specifications)
   - Sensor ground → GND

3. **Raspberry Pi Configuration**:
   ```bash
   # Enable I2C
   sudo raspi-config
   # Select Interfacing Options → I2C → Enable
   
   # Install I2C tools
   sudo apt-get update
   sudo apt-get install -y i2c-tools
   
   # Check if ADS1115 is connected (should see 0x48)
   i2cdetect -y 1
   ```

## Installation Steps

### Method 1: One-Click Installation (Recommended)

1. Double-click to run `install_dependencies.bat`
2. Wait for installation to complete

### Method 2: Manual Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. Edit the `raspberry_pi_config.txt` file and fill in your Raspberry Pi connection information:
   ```
   HOSTNAME=192.168.1.100  # Your Raspberry Pi IP address
   USERNAME=pi             # SSH username
   PASSWORD=your_password  # SSH password
   PORT=22                 # SSH port
   ```

2. Or set environment variables:
   - `PI_HOSTNAME`: Raspberry Pi IP or hostname
   - `PI_USERNAME`: SSH username
   - `PI_PASSWORD`: SSH password
   - `PI_PORT`: SSH port

## Usage

1. Open the project in PyCharm
2. Run `sensor_reader.py`
3. The program will automatically:
   - Connect to Raspberry Pi
   - Check hardware connections
   - Upload reading script
   - Read humidity data once per second, 10 times total

## Output Description

The program will output:
- System connection status
- Hardware detection results
- 10 sets of humidity data (one set per second)
- Data acquisition completion status

## Troubleshooting

1. **Connection Failed**:
   - Check if SSH is enabled on Raspberry Pi
   - Check if IP address and port are correct
   - Check firewall settings

2. **Hardware Not Detected**:
   - Run `i2cdetect -y 1` to check if ADS1115 is connected
   - Check if I2C is enabled in raspi-config
   - Check if wiring is correct

3. **Reading Failed**:
   - Check if sensor is correctly connected to ADS1115 A0 channel
   - Check sensor power connection
   - Adjust conversion formula according to actual sensor specifications

## Notes

- Ensure Raspberry Pi and Windows computer are on the same network
- First connection may require SSH host key confirmation
- Humidity conversion formula needs to be adjusted according to actual sensor specifications
- Recommend using Raspberry Pi with fixed IP address
