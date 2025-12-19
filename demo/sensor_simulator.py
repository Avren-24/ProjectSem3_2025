#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
湿度传感器模拟脚本
模拟树莓派Model4B + ADS1115 + 湿度传感器的数据读取
"""

import time
import random
import sys

# ANSI颜色代码
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
    print_colored("  湿度传感器数据采集系统", Colors.BOLD + Colors.CYAN)
    print("="*60 + "\n")

def simulate_connection():
    """模拟连接过程"""
    print_colored("[系统] 正在初始化连接...", Colors.YELLOW)
    time.sleep(0.5)
    
    print_colored("[系统] 检测到树莓派 Model 4B", Colors.GREEN)
    time.sleep(0.3)
    
    print_colored("[系统] 检测到 ADS1115 ADC模块", Colors.GREEN)
    time.sleep(0.3)
    
    print_colored("[系统] 检测到湿度传感器", Colors.GREEN)
    time.sleep(0.3)
    
    print_colored("[系统] 连接成功！所有硬件工作正常", Colors.BOLD + Colors.GREEN)
    time.sleep(0.5)
    print()

def print_data_header():
    """打印数据表头"""
    print("-" * 60)
    print(f"{'序号':<8} {'时间':<20} {'湿度值':<15} {'状态':<10}")
    print("-" * 60)

def print_data_row(index, timestamp, humidity, status="正常"):
    """打印数据行"""
    status_color = Colors.GREEN if status == "正常" else Colors.RED
    print(f"{index:<8} {timestamp:<20} {Colors.CYAN}{humidity:<15}{Colors.RESET} {status_color}{status:<10}{Colors.RESET}")

def main():
    """主函数"""
    print_header()
    simulate_connection()
    
    print_colored("[系统] 开始读取传感器数据...", Colors.BLUE)
    print()
    
    print_data_header()
    
    # 生成10组数据
    for i in range(1, 11):
        # 生成0.28-0.30之间的随机湿度值
        humidity = round(random.uniform(0.28, 0.30), 4)
        
        # 获取当前时间戳
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        # 打印数据
        print_data_row(i, timestamp, f"{humidity:.4f}", "正常")
        
        # 如果不是最后一组，等待1秒
        if i < 10:
            time.sleep(1)
    
    print("-" * 60)
    print()
    print_colored("[系统] 数据采集完成！共读取 10 组数据", Colors.BOLD + Colors.GREEN)
    print_colored("[系统] 所有数据读取成功", Colors.GREEN)
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        print_colored("[系统] 用户中断，程序退出", Colors.YELLOW)
        sys.exit(0)

