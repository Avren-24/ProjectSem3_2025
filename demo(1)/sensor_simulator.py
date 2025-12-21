#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Humidity Sensor Simulator Script
Simulates data reading from Raspberry Pi Model 4B + ADS1115 + Humidity Sensor
"""

import time
import random
import sys

# ANSI color codes
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

def simulate_connection():
    """Simulate connection process"""
    print_colored("[System] Initializing connection...", Colors.YELLOW)
    time.sleep(0.5)
    
    print_colored("[System] Detected Raspberry Pi Model 4B", Colors.GREEN)
    time.sleep(0.3)
    
    print_colored("[System] Detected ADS1115 ADC Module", Colors.GREEN)
    time.sleep(0.3)
    
    print_colored("[System] Detected Humidity Sensor", Colors.GREEN)
    time.sleep(0.3)
    
    print_colored("[System] Connection successful! All hardware working normally", Colors.BOLD + Colors.GREEN)
    time.sleep(0.5)
    print()

def print_data_header():
    """Print data table header"""
    print("-" * 60)
    print(f"{'No.':<8} {'Time':<20} {'Humidity':<15} {'Status':<10}")
    print("-" * 60)

def print_data_row(index, timestamp, humidity, status="OK"):
    """Print data row"""
    status_color = Colors.GREEN if status == "OK" else Colors.RED
    print(f"{index:<8} {timestamp:<20} {Colors.CYAN}{humidity:<15}{Colors.RESET} {status_color}{status:<10}{Colors.RESET}")

def main():
    """Main function"""
    print_header()
    simulate_connection()
    
    print_colored("[System] Starting to read sensor data...", Colors.BLUE)
    print()
    
    print_data_header()
    
    # Generate 10 data sets
    for i in range(1, 11):
        # Generate random humidity value between 0.28-0.30
        humidity = round(random.uniform(0.28, 0.30), 4)
        
        # Get current timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        # Print data
        print_data_row(i, timestamp, f"{humidity:.4f}", "OK")
        
        # If not the last set, wait 1 second
        if i < 10:
            time.sleep(1)
    
    print("-" * 60)
    print()
    print_colored("[System] Data acquisition completed! Total 10 data sets read", Colors.BOLD + Colors.GREEN)
    print_colored("[System] All data read successfully", Colors.GREEN)
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        print_colored("[System] User interrupted, program exiting", Colors.YELLOW)
        sys.exit(0)

