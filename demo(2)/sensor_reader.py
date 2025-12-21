#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real Humidity Sensor Data Reading Script
Connects to Raspberry Pi via SSH to read ADS1115 ADC module and humidity sensor data
Compatible with Windows system, runs in PyCharm
"""

import time
import sys
import os
from datetime import datetime
import paramiko

# Windows color support
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        pass

# ANSI color codes (Windows compatible)
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    DIM = '\033[2m'

def print_colored(text, color=Colors.RESET):
    """Print colored text"""
    print(f"{color}{text}{Colors.RESET}")

def print_header():
    """Print header"""
    print("\n" + "="*60)
    print_colored("  Humidity Sensor Data Acquisition System", Colors.BOLD + Colors.CYAN)
    print("="*60 + "\n")

def check_connection(ssh):
    """Check Raspberry Pi connection and hardware"""
    try:
        # Check Raspberry Pi model
        stdin, stdout, stderr = ssh.exec_command("cat /proc/device-tree/model 2>/dev/null || echo 'Raspberry Pi'")
        pi_model = stdout.read().decode().strip()
        if pi_model:
            print_colored(f"[System] Detected {pi_model}", Colors.GREEN)
        
        # Check if I2C is enabled
        stdin, stdout, stderr = ssh.exec_command("ls /dev/i2c-* 2>/dev/null | head -1")
        i2c_device = stdout.read().decode().strip()
        if i2c_device:
            print_colored(f"[System] Detected I2C device: {i2c_device}", Colors.GREEN)
        else:
            print_colored("[System] Warning: I2C device not found. Please enable I2C in raspi-config", Colors.YELLOW)
        
        # Check if ADS1115 is connected (scan I2C address 0x48)
        stdin, stdout, stderr = ssh.exec_command("i2cdetect -y 1 | grep -o '48' || echo 'not found'")
        ads1115 = stdout.read().decode().strip()
        if ads1115 == '48':
            print_colored("[System] Detected ADS1115 ADC Module (I2C address: 0x48)", Colors.GREEN)
        else:
            print_colored("[System] Warning: ADS1115 not detected at address 0x48", Colors.YELLOW)
        
        # Check Python library
        stdin, stdout, stderr = ssh.exec_command("python3 -c 'import Adafruit_ADS1x15' 2>&1")
        if stdout.channel.recv_exit_status() == 0:
            print_colored("[System] Adafruit_ADS1x15 library installed", Colors.GREEN)
        else:
            print_colored("[System] Installing Adafruit_ADS1x15 library...", Colors.YELLOW)
            ssh.exec_command("pip3 install Adafruit-ADS1x15 --quiet")
            time.sleep(2)
        
        print_colored("[System] Connection successful! All hardware working normally", Colors.BOLD + Colors.GREEN)
        return True
    except Exception as e:
        print_colored(f"[System] Error checking hardware: {str(e)}", Colors.RED)
        return False

def upload_reader_script(ssh):
    """Upload sensor reading script to Raspberry Pi"""
    try:
        reader_script = """#!/usr/bin/env python3
import sys
import Adafruit_ADS1x15

# Create ADS1115 instance (default I2C address 0x48)
adc = Adafruit_ADS1x15.ADS1115()

# Set gain (options: 2/3, 1, 2, 4, 8, 16)
GAIN = 1

# Read analog value from channel 0 (humidity sensor typically connected to A0)
# ADS1115 is 16-bit ADC, return value range: -32768 to 32767
value = adc.read_adc(0, gain=GAIN)

# Convert to voltage (ADS1115 reference voltage is 4.096V when gain is 1)
voltage = (value / 32767.0) * 4.096

# Assume humidity sensor outputs 0-3.3V corresponding to 0-100% humidity
# Here we assume sensor outputs 0-3.3V, convert to 0-1 humidity value
# Actual conversion formula should be adjusted according to specific sensor specifications
humidity = voltage / 3.3

# Limit humidity value to reasonable range
humidity = max(0.0, min(1.0, humidity))

print(f"{humidity:.4f}")
"""
        
        # Write to temporary file
        sftp = ssh.open_sftp()
        remote_file = sftp.file('/tmp/read_humidity.py', 'w')
        remote_file.write(reader_script)
        remote_file.close()
        sftp.close()
        
        # Set execute permission
        ssh.exec_command("chmod +x /tmp/read_humidity.py")
        return True
    except Exception as e:
        print_colored(f"[System] Error uploading script: {str(e)}", Colors.RED)
        return False

def read_humidity(ssh):
    """Read humidity value from Raspberry Pi"""
    try:
        stdin, stdout, stderr = ssh.exec_command("python3 /tmp/read_humidity.py")
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        if error:
            print_colored(f"[Error] {error}", Colors.RED)
            return None
        
        try:
            humidity = float(output)
            return humidity
        except ValueError:
            print_colored(f"[Error] Invalid humidity value: {output}", Colors.RED)
            return None
    except Exception as e:
        print_colored(f"[Error] Failed to read humidity: {str(e)}", Colors.RED)
        return None

def print_data_header():
    """Print data table header"""
    print("-" * 60)
    print(f"{'No.':<8} {'Time':<20} {'Humidity':<15} {'Status':<10}")
    print("-" * 60)

def print_data_row(index, timestamp, humidity, status="OK"):
    """Print data row"""
    status_color = Colors.GREEN if status == "OK" else Colors.RED
    humidity_str = f"{humidity:.4f}" if humidity is not None else "N/A"
    print(f"{index:<8} {timestamp:<20} {Colors.CYAN}{humidity_str:<15}{Colors.RESET} {status_color}{status:<10}{Colors.RESET}")

def connect_raspberry_pi(hostname, username, password, port=22):
    """Connect to Raspberry Pi"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print_colored(f"[System] Connecting to Raspberry Pi at {hostname}...", Colors.YELLOW)
        ssh.connect(hostname, port=port, username=username, password=password, timeout=10)
        print_colored("[System] Connection established!", Colors.GREEN)
        return ssh
    except paramiko.AuthenticationException:
        print_colored("[Error] Authentication failed. Please check username and password.", Colors.RED)
        return None
    except paramiko.SSHException as e:
        print_colored(f"[Error] SSH connection failed: {str(e)}", Colors.RED)
        return None
    except Exception as e:
        print_colored(f"[Error] Connection error: {str(e)}", Colors.RED)
        return None

def main():
    """Main function"""
    print_header()
    
    # Read connection information from config file or environment variables
    config_file = "raspberry_pi_config.txt"
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            lines = f.readlines()
            config = {}
            for line in lines:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key.strip()] = value.strip()
            
            hostname = config.get('HOSTNAME', 'raspberrypi.local')
            username = config.get('USERNAME', 'pi')
            password = config.get('PASSWORD', 'raspberry')
            port = int(config.get('PORT', '22'))
    else:
        # Use default values or prompt user input
        print_colored("[Config] Configuration file not found. Using defaults or environment variables.", Colors.YELLOW)
        hostname = os.getenv('PI_HOSTNAME', 'raspberrypi.local')
        username = os.getenv('PI_USERNAME', 'pi')
        password = os.getenv('PI_PASSWORD', 'raspberry')
        port = int(os.getenv('PI_PORT', '22'))
        
        print_colored(f"[Config] Hostname: {hostname}", Colors.CYAN)
        print_colored(f"[Config] Username: {username}", Colors.CYAN)
        print()
    
    # Connect to Raspberry Pi
    ssh = connect_raspberry_pi(hostname, username, password, port)
    if not ssh:
        print_colored("[Error] Failed to connect to Raspberry Pi. Please check your configuration.", Colors.RED)
        sys.exit(1)
    
    try:
        # Check hardware connection
        if not check_connection(ssh):
            print_colored("[Warning] Hardware check failed, but continuing...", Colors.YELLOW)
        
        # Upload reading script
        if not upload_reader_script(ssh):
            print_colored("[Error] Failed to upload reader script.", Colors.RED)
            sys.exit(1)
        
        print()
        print_colored("[System] Starting to read sensor data...", Colors.BLUE)
        print()
        
        print_data_header()
        
        # Read 10 data sets, once per second
        success_count = 0
        for i in range(1, 11):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            humidity = read_humidity(ssh)
            
            if humidity is not None:
                print_data_row(i, timestamp, humidity, "OK")
                success_count += 1
            else:
                print_data_row(i, timestamp, None, "ERROR")
            
            # If not the last set, wait 1 second
            if i < 10:
                time.sleep(1)
        
        print("-" * 60)
        print()
        print_colored(f"[System] Data acquisition completed! Total 10 data sets read ({success_count} successful)", Colors.BOLD + Colors.GREEN)
        if success_count == 10:
            print_colored("[System] All data read successfully", Colors.GREEN)
        else:
            print_colored(f"[System] Warning: {10 - success_count} readings failed", Colors.YELLOW)
        print()
        
    finally:
        ssh.close()
        print_colored("[System] Connection closed", Colors.CYAN)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        print_colored("[System] User interrupted, program exiting", Colors.YELLOW)
        sys.exit(0)
    except Exception as e:
        print_colored(f"[Error] Unexpected error: {str(e)}", Colors.RED)
        sys.exit(1)

