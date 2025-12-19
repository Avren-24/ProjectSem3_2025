#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
湿度传感器真实数据读取脚本
通过SSH连接树莓派，读取ADS1115 ADC模块和湿度传感器数据
适配Windows系统，在PyCharm中运行
"""

import time
import sys
import os
from datetime import datetime
import paramiko

# Windows颜色支持
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        pass

# ANSI颜色代码（Windows兼容）
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
    """打印彩色文本"""
    print(f"{color}{text}{Colors.RESET}")

def print_header():
    """打印标题"""
    print("\n" + "="*60)
    print_colored("  Humidity Sensor Data Acquisition System", Colors.BOLD + Colors.CYAN)
    print("="*60 + "\n")

def check_connection(ssh):
    """检查树莓派连接和硬件"""
    try:
        # 检查树莓派型号
        stdin, stdout, stderr = ssh.exec_command("cat /proc/device-tree/model 2>/dev/null || echo 'Raspberry Pi'")
        pi_model = stdout.read().decode().strip()
        if pi_model:
            print_colored(f"[System] Detected {pi_model}", Colors.GREEN)
        
        # 检查I2C是否启用
        stdin, stdout, stderr = ssh.exec_command("ls /dev/i2c-* 2>/dev/null")
        i2c_devices = stdout.read().decode().strip().split('\n')
        i2c_devices = [d for d in i2c_devices if d]
        if i2c_devices:
            print_colored(f"[System] Detected I2C devices: {', '.join(i2c_devices)}", Colors.GREEN)
        else:
            print_colored("[System] Warning: I2C device not found. Please enable I2C in raspi-config", Colors.YELLOW)
            return False
        
        # 检查I2C权限
        stdin, stdout, stderr = ssh.exec_command("groups $USER 2>/dev/null | grep -q i2c && echo 'yes' || echo 'no'")
        has_i2c_permission = stdout.read().decode().strip() == 'yes'
        if not has_i2c_permission:
            print_colored("[System] Warning: User may not have I2C permissions", Colors.YELLOW)
            print_colored("[System] Tip: Run 'sudo usermod -aG i2c $USER' and logout/login", Colors.CYAN)
        
        # 检查i2c-tools是否安装
        stdin, stdout, stderr = ssh.exec_command("which i2cdetect 2>/dev/null")
        has_i2cdetect = bool(stdout.read().decode().strip())
        if not has_i2cdetect:
            print_colored("[System] Warning: i2c-tools not installed (i2cdetect command not found)", Colors.YELLOW)
            print_colored("[System] Tip: Install with 'sudo apt-get install -y i2c-tools'", Colors.CYAN)
            print_colored("[System] Continuing without i2cdetect...", Colors.CYAN)
        
        # 扫描I2C总线查找ADS1115（可能的地址：0x48, 0x49, 0x4a, 0x4b）
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
                        # 检查所有可能的ADS1115地址
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
        
        # 检查Python库
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
    """上传传感器读取脚本到树莓派"""
    try:
        reader_script = """#!/usr/bin/env python3
import sys
import os
import subprocess
import Adafruit_ADS1x15

# 检测可用的I2C总线
available_buses = []
if os.path.exists('/dev/i2c-1'):
    available_buses.append(1)
if os.path.exists('/dev/i2c-0'):
    available_buses.append(0)
if not available_buses:
    # 尝试自动检测
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

# ADS1115可能的I2C地址
possible_addresses = [0x48, 0x49, 0x4a, 0x4b]

# 检查i2cdetect是否可用
has_i2cdetect = False
try:
    result = subprocess.run(['which', 'i2cdetect'], 
                          capture_output=True, text=True, timeout=1)
    has_i2cdetect = result.returncode == 0
except:
    has_i2cdetect = False

# 如果i2cdetect可用，尝试扫描I2C设备
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

# 如果扫描到设备，使用扫描到的地址和总线
# 否则尝试所有可能的组合
if detected_addresses:
    busnum = list(detected_addresses.keys())[0]
    i2c_address = detected_addresses[busnum]
else:
    # 使用默认值（最常见的情况）
    busnum = available_buses[0]
    i2c_address = 0x48

# 尝试连接ADS1115
success = False
last_error = None

# 如果扫描失败，尝试所有可能的地址和总线组合
for test_bus in available_buses:
    for test_addr in possible_addresses:
        try:
            adc = Adafruit_ADS1x15.ADS1115(address=test_addr, busnum=test_bus)
            # 尝试读取一个值来验证连接
            test_value = adc.read_adc(0, gain=1)
            # 如果成功，使用这个配置
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
    # 显示详细的错误信息
    print(f"ERROR: Cannot communicate with ADS1115", file=sys.stderr)
    print(f"Tried buses: {available_buses}", file=sys.stderr)
    print(f"Tried addresses: {[hex(a) for a in possible_addresses]}", file=sys.stderr)
    print("", file=sys.stderr)
    
    # 如果i2cdetect可用，尝试扫描并显示结果
    if has_i2cdetect:
        print("I2C scan results:", file=sys.stderr)
        for busnum in available_buses:
            try:
                result = subprocess.run(['i2cdetect', '-y', str(busnum)], 
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    print(f"Bus {busnum}:", file=sys.stderr)
                    # 只显示检测到的设备行
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
    # 创建ADS1115实例（使用找到的配置）
    adc = Adafruit_ADS1x15.ADS1115(address=i2c_address, busnum=busnum)
    
    # 设置增益 (可选: 2/3, 1, 2, 4, 8, 16)
    GAIN = 1
    
    # 读取通道0的模拟值 (湿度传感器通常连接到A0)
    # ADS1115是16位ADC，返回值范围: -32768到32767
    value = adc.read_adc(0, gain=GAIN)
    
    # 转换为电压 (ADS1115参考电压为4.096V，增益为1时)
    voltage = (value / 32767.0) * 4.096
    
    # 假设湿度传感器输出0-3.3V对应0-100%湿度
    # 这里假设传感器输出0-3.3V，我们转换为0-1的湿度值
    # 实际转换公式需要根据具体传感器规格调整
    humidity = voltage / 3.3
    
    # 限制湿度值在合理范围内
    humidity = max(0.0, min(1.0, humidity))
    
    print(f"{humidity:.4f}")
    
except Exception as e:
    print(f"ERROR: Failed to read sensor: {str(e)}", file=sys.stderr)
    sys.exit(1)
"""
        
        # 写入临时文件
        sftp = ssh.open_sftp()
        remote_file = sftp.file('/tmp/read_humidity.py', 'w')
        remote_file.write(reader_script)
        remote_file.close()
        sftp.close()
        
        # 设置执行权限
        ssh.exec_command("chmod +x /tmp/read_humidity.py")
        return True
    except Exception as e:
        print_colored(f"[System] Error uploading script: {str(e)}", Colors.RED)
        return False

def read_humidity(ssh):
    """从树莓派读取湿度值"""
    try:
        stdin, stdout, stderr = ssh.exec_command("python3 /tmp/read_humidity.py")
        # 等待命令完成
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        # 如果命令失败或stderr有输出，显示错误
        if exit_status != 0 or error:
            if error:
                # 提取关键错误信息
                error_lines = error.split('\n')
                for line in error_lines:
                    if 'ERROR:' in line or 'Error' in line or 'error' in line:
                        print_colored(f"[Error] {line}", Colors.RED)
                    elif line.strip() and not line.startswith('Traceback'):
                        print_colored(f"[Error] {line}", Colors.RED)
            else:
                print_colored(f"[Error] Command failed with exit status {exit_status}", Colors.RED)
            return None
        
        # 尝试解析输出
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
    """打印数据表头"""
    print("-" * 60)
    print(f"{'No.':<8} {'Time':<20} {'Humidity':<15} {'Status':<10}")
    print("-" * 60)

def print_data_row(index, timestamp, humidity, status="OK"):
    """打印数据行"""
    status_color = Colors.GREEN if status == "OK" else Colors.RED
    humidity_str = f"{humidity:.4f}" if humidity is not None else "N/A"
    print(f"{index:<8} {timestamp:<20} {Colors.CYAN}{humidity_str:<15}{Colors.RESET} {status_color}{status:<10}{Colors.RESET}")

def connect_raspberry_pi(hostname, username, password, port=22):
    """连接到树莓派"""
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
        # 检查是否是DNS解析错误（Windows错误代码11001）
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
    """主函数"""
    print_header()
    
    # 从配置文件或环境变量读取连接信息
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
        # 使用默认值或提示用户输入
        print_colored("[Config] Configuration file not found. Using defaults or environment variables.", Colors.YELLOW)
        hostname = os.getenv('PI_HOSTNAME', 'raspberrypi.local')
        username = os.getenv('PI_USERNAME', 'pi')
        password = os.getenv('PI_PASSWORD', 'raspberry')
        port = int(os.getenv('PI_PORT', '22'))
        
        print_colored(f"[Config] Hostname: {hostname}", Colors.CYAN)
        print_colored(f"[Config] Username: {username}", Colors.CYAN)
        print()
    
    # 连接树莓派
    ssh = connect_raspberry_pi(hostname, username, password, port)
    if not ssh:
        print_colored("[Error] Failed to connect to Raspberry Pi. Please check your configuration.", Colors.RED)
        sys.exit(1)
    
    try:
        # 检查硬件连接
        if not check_connection(ssh):
            print_colored("[Warning] Hardware check failed, but continuing...", Colors.YELLOW)
        
        # 上传读取脚本
        if not upload_reader_script(ssh):
            print_colored("[Error] Failed to upload reader script.", Colors.RED)
            sys.exit(1)
        
        print()
        print_colored("[System] Starting to read sensor data...", Colors.BLUE)
        print()
        
        print_data_header()
        
        # 读取10组数据，每秒一次
        success_count = 0
        for i in range(1, 11):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            humidity = read_humidity(ssh)
            
            if humidity is not None:
                print_data_row(i, timestamp, humidity, "OK")
                success_count += 1
            else:
                print_data_row(i, timestamp, None, "ERROR")
            
            # 如果不是最后一组，等待1秒
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

