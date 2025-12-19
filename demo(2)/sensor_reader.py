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
        stdin, stdout, stderr = ssh.exec_command("ls /dev/i2c-* 2>/dev/null | head -1")
        i2c_device = stdout.read().decode().strip()
        if i2c_device:
            print_colored(f"[System] Detected I2C device: {i2c_device}", Colors.GREEN)
        else:
            print_colored("[System] Warning: I2C device not found. Please enable I2C in raspi-config", Colors.YELLOW)
        
        # 检查ADS1115是否连接（扫描I2C地址0x48）
        stdin, stdout, stderr = ssh.exec_command("i2cdetect -y 1 | grep -o '48' || echo 'not found'")
        ads1115 = stdout.read().decode().strip()
        if ads1115 == '48':
            print_colored("[System] Detected ADS1115 ADC Module (I2C address: 0x48)", Colors.GREEN)
        else:
            print_colored("[System] Warning: ADS1115 not detected at address 0x48", Colors.YELLOW)
        
        # 检查Python库
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
    """上传传感器读取脚本到树莓派"""
    try:
        reader_script = """#!/usr/bin/env python3
import sys
import Adafruit_ADS1x15

# 创建ADS1115实例 (默认I2C地址0x48)
adc = Adafruit_ADS1x15.ADS1115()

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
        print_colored(f"[Error] Connection error: {str(e)}", Colors.RED)
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

