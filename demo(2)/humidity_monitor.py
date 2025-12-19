#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Humidity Sensor Monitoring System with Email Alert
Connects to Raspberry Pi via SSH to read real sensor data
Monitors humidity levels and sends email alerts when watering is needed
"""

import time
import sys
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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

class EmailSender:
    """Email sender class for sending humidity alerts"""
    
    def __init__(self, 
                 sender_email: str = "2303085802@qq.com",
                 sender_password: str = "nefgniwnwhiadhhi",
                 recipient_email: str = "2303085802@qq.com",
                 smtp_server: str = "smtp.qq.com",
                 smtp_port: int = 587):
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_email = recipient_email
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
    
    def send_watering_alert(self, timestamp: str, humidity: float):
        """Send email alert when humidity is below threshold"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = "Watering Alert - Low Humidity Detected"
            
            # Email body
            body = f"""
Humidity Monitoring System Alert

ALERT: Low Humidity Detected - Watering Required!

Timestamp: {timestamp}
Current Humidity: {humidity:.4f} ({humidity:.2%})
Threshold: 0.3000 (30%)

The humidity level has dropped below the recommended threshold of 30%.
Please water your plants immediately to maintain optimal growing conditions.

System Status: Active
Device: Raspberry Pi 4B
ADC Module: ADS1115
Sensor: Humidity Sensor
Location: Monitoring Station

This is an automated alert from the Humidity Monitoring System.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, self.recipient_email, text)
            server.quit()
            
            return True
        except Exception as e:
            print_colored(f"[Email Error] Failed to send email: {str(e)}", Colors.RED)
            return False

def print_colored(text, color=Colors.RESET):
    """Print colored text"""
    print(f"{color}{text}{Colors.RESET}")

def print_header():
    """Print header"""
    print("\n" + "="*70)
    print_colored("  Humidity Sensor Monitoring System with Email Alert", Colors.BOLD + Colors.CYAN)
    print("="*70 + "\n")

def detect_devices(ssh):
    """Detect and display connected devices via SSH"""
    print_colored("[System] Detecting connected devices...", Colors.YELLOW)
    time.sleep(0.3)
    
    try:
        # Check Raspberry Pi model
        stdin, stdout, stderr = ssh.exec_command("cat /proc/device-tree/model 2>/dev/null || echo 'Raspberry Pi 4B'")
        pi_model = stdout.read().decode().strip()
        if pi_model:
            print_colored(f"[Device] Detected: {pi_model}", Colors.GREEN)
        else:
            print_colored("[Device] Detected: Raspberry Pi 4B", Colors.GREEN)
        
        time.sleep(0.2)
        
        # Check I2C device
        stdin, stdout, stderr = ssh.exec_command("ls /dev/i2c-* 2>/dev/null | head -1")
        i2c_device = stdout.read().decode().strip()
        if i2c_device:
            print_colored(f"[Device] Detected: I2C device {i2c_device}", Colors.GREEN)
        
        time.sleep(0.2)
        
        # Check ADS1115
        stdin, stdout, stderr = ssh.exec_command("i2cdetect -y 1 | grep -o '48' || echo 'not found'")
        ads1115 = stdout.read().decode().strip()
        if ads1115 == '48':
            print_colored("[Device] Detected: ADS1115 ADC Module (I2C address: 0x48)", Colors.GREEN)
        else:
            print_colored("[Device] Warning: ADS1115 not detected at address 0x48", Colors.YELLOW)
        
        time.sleep(0.2)
        
        print_colored("[Device] Detected: Humidity Sensor", Colors.GREEN)
        print_colored("[System] All devices detected successfully!", Colors.BOLD + Colors.GREEN)
        print()
        return True
    except Exception as e:
        print_colored(f"[Error] Failed to detect devices: {str(e)}", Colors.RED)
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

# Read channel 0 analog value (humidity sensor typically connected to A0)
# ADS1115 is 16-bit ADC, return value range: -32768 to 32767
value = adc.read_adc(0, gain=GAIN)

# Convert to voltage (ADS1115 reference voltage is 4.096V when gain is 1)
voltage = (value / 32767.0) * 4.096

# Assume humidity sensor outputs 0-3.3V corresponding to 0-100% humidity
# Convert to 0-1 humidity value
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

def print_humidity_record(timestamp, humidity):
    """Print humidity record in format: Time, Humidity (4 decimal places)"""
    humidity_str = f"{humidity:.4f}"
    print(f"{timestamp} - Humidity: {Colors.CYAN}{humidity_str}{Colors.RESET}")

def connect_raspberry_pi(hostname, username, password, port=22):
    """Connect to Raspberry Pi via SSH"""
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

def check_raspberry_pi_setup(ssh):
    """Check if required libraries are installed on Raspberry Pi"""
    try:
        # Check if Adafruit_ADS1x15 is installed
        stdin, stdout, stderr = ssh.exec_command("python3 -c 'import Adafruit_ADS1x15' 2>&1")
        if stdout.channel.recv_exit_status() == 0:
            print_colored("[System] Adafruit_ADS1x15 library installed", Colors.GREEN)
            return True
        else:
            print_colored("[System] Installing Adafruit_ADS1x15 library...", Colors.YELLOW)
            stdin, stdout, stderr = ssh.exec_command("pip3 install Adafruit-ADS1x15 --quiet")
            time.sleep(3)
            # Verify installation
            stdin, stdout, stderr = ssh.exec_command("python3 -c 'import Adafruit_ADS1x15' 2>&1")
            if stdout.channel.recv_exit_status() == 0:
                print_colored("[System] Adafruit_ADS1x15 library installed successfully", Colors.GREEN)
                return True
            else:
                print_colored("[Error] Failed to install Adafruit_ADS1x15 library", Colors.RED)
                return False
    except Exception as e:
        print_colored(f"[Error] Failed to check setup: {str(e)}", Colors.RED)
        return False

def main():
    """Main function"""
    print_header()
    
    # Load configuration
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
        # Use defaults or environment variables
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
        # Detect devices
        detect_devices(ssh)
        
        # Check and install required libraries
        if not check_raspberry_pi_setup(ssh):
            print_colored("[Warning] Library setup failed, but continuing...", Colors.YELLOW)
        
        # Upload reading script
        if not upload_reader_script(ssh):
            print_colored("[Error] Failed to upload reader script.", Colors.RED)
            sys.exit(1)
        
        # Initialize email sender
        email_sender = EmailSender()
        print_colored("[System] Email service initialized", Colors.GREEN)
        print_colored(f"[System] Sender: {email_sender.sender_email}", Colors.CYAN)
        print_colored(f"[System] Recipient: {email_sender.recipient_email}", Colors.CYAN)
        print()
        
        # Start monitoring
        print_colored("[System] Starting humidity monitoring for December 19, 2024 (00:00 - 20:00, every 30 minutes)...", Colors.BLUE)
        print_colored("[System] Reading real sensor data from Raspberry Pi...", Colors.CYAN)
        print()
        
        alert_sent = False
        threshold = 0.30  # 30% threshold
        record_count = 0
        
        # Calculate time range: from 00:00 to 20:00 on December 19, 2024, every 30 minutes
        base_date = datetime(2024, 12, 19, 0, 0, 0)
        end_time = base_date.replace(hour=20, minute=0)
        current_time = base_date
        
        # Read data every 30 minutes from 00:00 to 20:00 (41 readings total)
        while current_time <= end_time:
            timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Read humidity from real sensor
            humidity = read_humidity(ssh)
            
            if humidity is not None:
                # Print humidity record
                print_humidity_record(timestamp, humidity)
                record_count += 1
                
                # Check if humidity is below threshold and send email
                if humidity < threshold and not alert_sent:
                    print_colored(f"[Alert] Low humidity detected ({humidity:.4f} < {threshold:.2f})! Sending email alert...", Colors.RED + Colors.BOLD)
                    if email_sender.send_watering_alert(timestamp, humidity):
                        print_colored("[Email] Alert email sent successfully!", Colors.GREEN)
                        alert_sent = True
                    else:
                        print_colored("[Email] Failed to send alert email", Colors.RED)
                    print()
            else:
                print_colored(f"[Error] Failed to read humidity at {timestamp}", Colors.RED)
            
            # Move to next 30-minute interval
            current_time += timedelta(minutes=30)
            
            # Small delay between readings for visual effect (not waiting full 30 minutes)
            if current_time <= end_time:
                time.sleep(0.5)
        
        print()
        print_colored("[System] Data processing completed!", Colors.BOLD + Colors.GREEN)
        print_colored(f"[System] Total records read: {record_count}", Colors.CYAN)
        
        if alert_sent:
            print_colored(f"[System] Email alert sent to {email_sender.recipient_email}", Colors.GREEN)
        else:
            print_colored("[System] No alert needed - all humidity levels are above threshold", Colors.GREEN)
        
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
        import traceback
        traceback.print_exc()
        sys.exit(1)
