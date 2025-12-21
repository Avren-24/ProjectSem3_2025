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
        stdin, stdout, stderr = ssh.exec_command("ls /dev/i2c-* 2>/dev/null")
        i2c_devices = stdout.read().decode().strip().split('\n')
        i2c_devices = [d for d in i2c_devices if d]
        if i2c_devices:
            print_colored(f"[System] Detected I2C devices: {', '.join(i2c_devices)}", Colors.GREEN)
        else:
            print_colored("[System] Warning: I2C device not found. Please enable I2C in raspi-config", Colors.YELLOW)
            return False
        
        # Check I2C permissions
        stdin, stdout, stderr = ssh.exec_command("groups $USER 2>/dev/null | grep -q i2c && echo 'yes' || echo 'no'")
        has_i2c_permission = stdout.read().decode().strip() == 'yes'
        if not has_i2c_permission:
            print_colored("[System] Warning: User may not have I2C permissions", Colors.YELLOW)
            print_colored("[System] Tip: Run 'sudo usermod -aG i2c $USER' and logout/login", Colors.CYAN)
        
        # Check if i2c-tools is installed
        stdin, stdout, stderr = ssh.exec_command("which i2cdetect 2>/dev/null")
        has_i2cdetect = bool(stdout.read().decode().strip())
        if not has_i2cdetect:
            print_colored("[System] Warning: i2c-tools not installed (i2cdetect command not found)", Colors.YELLOW)
            print_colored("[System] Tip: Install with 'sudo apt-get install -y i2c-tools'", Colors.CYAN)
            print_colored("[System] Continuing without i2cdetect...", Colors.CYAN)
        
        # Scan I2C bus to find ADS1115 (possible addresses: 0x48, 0x49, 0x4a, 0x4b)
        ads1115_found = False
        ads1115_address = None
        ads1115_bus = None
        
        if has_i2cdetect:
            for bus in [1, 0]:
                try:
                    stdin, stdout, stderr = ssh.exec_command(f"i2cdetect -y {bus} 2>/dev/null")
                    exit_status = stdout.channel.recv_exit_status()
                    if exit_status == 0:
                        scan_result = stdout.read().decode()
                        # Check all possible ADS1115 addresses
                        for addr in ['48', '49', '4a', '4A', '4b', '4B']:
                            if addr in scan_result:
                                ads1115_found = True
                                ads1115_address = f"0x{addr.lower()}"
                                ads1115_bus = bus
                                print_colored(f"[System] Detected ADS1115 ADC Module (I2C address: {ads1115_address}, bus: {bus})", Colors.GREEN)
                                break
                        if ads1115_found:
                            break
                except:
                    continue
        
        if not ads1115_found:
            print_colored("[System] Warning: ADS1115 not detected on I2C bus", Colors.YELLOW)
            if not has_i2cdetect:
                print_colored("[System] Note: Cannot scan I2C bus without i2c-tools", Colors.CYAN)
            print_colored("[System] Please check:", Colors.CYAN)
            print_colored("  1. ADS1115 power connections (VDD to 3.3V, GND to GND)", Colors.CYAN)
            print_colored("  2. I2C connections (SDA to GPIO 2, SCL to GPIO 3)", Colors.CYAN)
            print_colored("  3. ADDR pin configuration (default address is 0x48)", Colors.CYAN)
            print_colored("[System] Script will try all possible addresses automatically", Colors.CYAN)
        
        # Check Python library
        stdin, stdout, stderr = ssh.exec_command("python3 -c 'import Adafruit_ADS1x15' 2>&1")
        if stdout.channel.recv_exit_status() == 0:
            print_colored("[System] Adafruit_ADS1x15 library installed", Colors.GREEN)
        else:
            print_colored("[System] Installing Adafruit_ADS1x15 library...", Colors.YELLOW)
            ssh.exec_command("pip3 install Adafruit-ADS1x15 --quiet")
            time.sleep(2)
        
        if ads1115_found:
            print_colored("[System] Hardware check completed successfully", Colors.BOLD + Colors.GREEN)
        else:
            print_colored("[System] Hardware check completed with warnings", Colors.YELLOW)
        
        return True
    except Exception as e:
        print_colored(f"[System] Error checking hardware: {str(e)}", Colors.RED)
        return False

def upload_reader_script(ssh):
    """Upload sensor reading script to Raspberry Pi"""
    try:
        reader_script = """#!/usr/bin/env python3
import sys
import os
import subprocess
import Adafruit_ADS1x15

# Detect available I2C buses
available_buses = []
if os.path.exists('/dev/i2c-1'):
    available_buses.append(1)
if os.path.exists('/dev/i2c-0'):
    available_buses.append(0)
if not available_buses:
    # Try auto-detection
    import glob
    i2c_devices = glob.glob('/dev/i2c-*')
    for device in i2c_devices:
        try:
            busnum = int(device.split('-')[1])
            available_buses.append(busnum)
        except:
            pass

if not available_buses:
    print("ERROR: No I2C buses found", file=sys.stderr)
    sys.exit(1)

# Possible I2C addresses for ADS1115
possible_addresses = [0x48, 0x49, 0x4a, 0x4b]

# Check if i2cdetect is available
has_i2cdetect = False
try:
    result = subprocess.run(['which', 'i2cdetect'], 
                          capture_output=True, text=True, timeout=1)
    has_i2cdetect = result.returncode == 0
except:
    has_i2cdetect = False

# If i2cdetect is available, try scanning I2C devices
detected_addresses = {}
if has_i2cdetect:
    for busnum in available_buses:
        try:
            result = subprocess.run(['i2cdetect', '-y', str(busnum)], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                scan_output = result.stdout.lower()
                for addr in possible_addresses:
                    addr_str = f"{addr:02x}"
                    if addr_str in scan_output:
                        detected_addresses[busnum] = addr
                        break
        except:
            continue

# If devices are detected, use detected address and bus
# Otherwise try all possible combinations
if detected_addresses:
    busnum = list(detected_addresses.keys())[0]
    i2c_address = detected_addresses[busnum]
else:
    # Use default values (most common case)
    busnum = available_buses[0]
    i2c_address = 0x48

# Try to connect to ADS1115
success = False
last_error = None

# If scan failed, try all possible address and bus combinations
for test_bus in available_buses:
    for test_addr in possible_addresses:
        try:
            adc = Adafruit_ADS1x15.ADS1115(address=test_addr, busnum=test_bus)
            # Try reading a value to verify connection
            test_value = adc.read_adc(0, gain=1)
            # If successful, use this configuration
            busnum = test_bus
            i2c_address = test_addr
            success = True
            break
        except OSError as e:
            last_error = e
            continue
        except Exception as e:
            last_error = e
            continue
    if success:
        break

if not success:
    # Display detailed error information
    print(f"ERROR: Cannot communicate with ADS1115", file=sys.stderr)
    print(f"Tried buses: {available_buses}", file=sys.stderr)
    print(f"Tried addresses: {[hex(a) for a in possible_addresses]}", file=sys.stderr)
    print("", file=sys.stderr)
    
    # If i2cdetect is available, try scanning and display results
    if has_i2cdetect:
        print("I2C scan results:", file=sys.stderr)
        for busnum in available_buses:
            try:
                result = subprocess.run(['i2cdetect', '-y', str(busnum)], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    print(f"Bus {busnum}:", file=sys.stderr)
                    # Only show detected device lines
                    for line in result.stdout.split('\\n'):
                        if any(f"{addr:02x}" in line.lower() for addr in range(0x08, 0x78)):
                            print(f"  {line}", file=sys.stderr)
            except Exception as e:
                print(f"  Cannot scan bus {busnum}: {str(e)}", file=sys.stderr)
    else:
        print("Note: i2cdetect not available (install with: sudo apt-get install -y i2c-tools)", file=sys.stderr)
        print("Cannot scan I2C bus without i2cdetect", file=sys.stderr)
    
    print("", file=sys.stderr)
    print("Possible causes:", file=sys.stderr)
    print("1. ADS1115 not connected or powered (check VDD to 3.3V, GND to GND)", file=sys.stderr)
    print("2. Wrong I2C connections (SDA to GPIO 2, SCL to GPIO 3)", file=sys.stderr)
    print("3. Loose connections (check all wires)", file=sys.stderr)
    print("4. I2C permissions issue (run: sudo usermod -aG i2c $USER, then logout/login)", file=sys.stderr)
    print("5. ADS1115 module may be faulty", file=sys.stderr)
    if last_error:
        print(f"Last error: {str(last_error)}", file=sys.stderr)
    sys.exit(1)

try:
    # Create ADS1115 instance (using found configuration)
    adc = Adafruit_ADS1x15.ADS1115(address=i2c_address, busnum=busnum)
    
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
    
except Exception as e:
    print(f"ERROR: Failed to read sensor: {str(e)}", file=sys.stderr)
    sys.exit(1)
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
        # Wait for command to complete
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        # If command failed or stderr has output, display error
        if exit_status != 0 or error:
            if error:
                # Extract key error information
                error_lines = error.split('\n')
                for line in error_lines:
                    if 'ERROR:' in line or 'Error' in line or 'error' in line:
                        print_colored(f"[Error] {line}", Colors.RED)
                    elif line.strip() and not line.startswith('Traceback'):
                        print_colored(f"[Error] {line}", Colors.RED)
            else:
                print_colored(f"[Error] Command failed with exit status {exit_status}", Colors.RED)
            return None
        
        # Try to parse output
        if not output:
            print_colored("[Error] No output from sensor reading script", Colors.RED)
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
        error_msg = str(e)
        # Check if it's a DNS resolution error (Windows error code 11001)
        if '11001' in error_msg or 'getaddrinfo failed' in error_msg or 'Name or service not known' in error_msg:
            print_colored("[Error] Cannot resolve hostname. DNS lookup failed.", Colors.RED)
            print()
            print_colored("Possible solutions:", Colors.YELLOW)
            print_colored("1. Use IP address instead of hostname:", Colors.CYAN)
            print_colored("   Edit raspberry_pi_config.txt and change HOSTNAME to your Pi's IP address", Colors.CYAN)
            print_colored("   Example: HOSTNAME=192.168.1.100", Colors.CYAN)
            print()
            print_colored("2. Find your Raspberry Pi's IP address:", Colors.CYAN)
            if sys.platform == 'win32':
                print_colored("   - On Raspberry Pi, run: hostname -I", Colors.CYAN)
                print_colored("   - Or check your router's admin page", Colors.CYAN)
            else:
                print_colored("   - On Raspberry Pi, run: hostname -I", Colors.CYAN)
            print()
            print_colored("3. If using .local hostname on Windows:", Colors.CYAN)
            print_colored("   - Install Bonjour Print Services from Apple", Colors.CYAN)
            print_colored("   - Or use IP address instead (recommended)", Colors.CYAN)
        else:
            print_colored(f"[Error] Connection error: {error_msg}", Colors.RED)
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

