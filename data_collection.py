"""
Soil Moisture Data Collection Module
Raspberry Pi + FC-28 Soil Moisture Sensor
"""

import RPi.GPIO as GPIO
import time
import csv
from datetime import datetime
import os

class MoistureSensor:
    def __init__(self, sensor_pin=17):
        """
        Initialize moisture sensor
        :param sensor_pin: GPIO pin connected to sensor DO pin
        """
        self.sensor_pin = sensor_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.sensor_pin, GPIO.IN)
        
    def read_moisture(self):
        """
        Read digital moisture value
        Returns: 0 (dry) or 1 (wet)
        """
        try:
            return GPIO.input(self.sensor_pin)
        except Exception as e:
            print(f"Error reading sensor: {e}")
            return None
    
    def read_analog_moisture(self, adc_pin=0):
        """
        For sensors with analog output using MCP3008 ADC
        Returns: Moisture percentage (0-100%)
        """
        # If using MCP3008 ADC
        import spidev
        
        spi = spidev.SpiDev()
        spi.open(0, 0)
        spi.max_speed_hz = 1350000
        
        # Read ADC value
        adc = spi.xfer2([1, (8 + adc_pin) << 4, 0])
        data = ((adc[1] & 3) << 8) + adc[2]
        spi.close()
        
        # Convert to percentage (calibrate based on your sensor)
        moisture_percent = 100 - (data / 1023.0 * 100)
        return max(0, min(100, moisture_percent))

def collect_data(duration_hours=48, interval_minutes=30):
    """
    Collect moisture data for specified duration
    """
    sensor = MoistureSensor()
    
    # Create data directory
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # CSV file setup
    filename = f"data/moisture_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['timestamp', 'moisture_digital', 'temperature', 'humidity'])
        
        print(f"Starting data collection for {duration_hours} hours...")
        print(f"Data will be saved to: {filename}")
        
        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        
        while time.time() < end_time:
            try:
                # Read sensor data
                moisture = sensor.read_moisture()
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # For demo, simulate temperature and humidity
                # Replace with actual sensor readings if available
                import random
                temperature = round(20 + random.uniform(-2, 2), 2)
                humidity = round(50 + random.uniform(-10, 10), 2)
                
                # Write to CSV
                writer.writerow([timestamp, moisture, temperature, humidity])
                file.flush()
                
                print(f"[{timestamp}] Moisture: {moisture}, Temp: {temperature}°C, Humidity: {humidity}%")
                
                # Wait for next reading
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\nData collection stopped by user")
                break
            except Exception as e:
                print(f"Error during data collection: {e}")
                time.sleep(60)  # Wait before retry
    
    print(f"Data collection complete. File saved: {filename}")
    return filename

def simulate_data():
    """
    Generate simulated sensor data if hardware is not available
    """
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    print("Generating simulated sensor data...")
    
    # Create time range: 48 hours, every 30 minutes
    start_time = datetime.now() - timedelta(days=2)
    timestamps = [start_time + timedelta(minutes=30*i) for i in range(96)]
    
    # Generate realistic moisture data (decreasing trend with noise)
    base_moisture = np.linspace(80, 20, 96)  # Gradually drying out
    noise = np.random.normal(0, 5, 96)  # Add some noise
    moisture_values = np.clip(base_moisture + noise, 0, 100)
    
    # Generate temperature and humidity data
    temperature = 20 + 3 * np.sin(np.linspace(0, 4*np.pi, 96)) + np.random.normal(0, 1, 96)
    humidity = 50 + 10 * np.sin(np.linspace(0, 2*np.pi, 96)) + np.random.normal(0, 3, 96)
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': [ts.strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps],
        'moisture': moisture_values.round(2),
        'temperature': temperature.round(2),
        'humidity': humidity.round(2)
    })
    
    # Save to CSV
    if not os.path.exists('data'):
        os.makedirs('data')
    
    filename = f"data/simulated_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    
    print(f"Simulated data saved to: {filename}")
    return filename, df

if __name__ == "__main__":
    print("Soil Moisture Data Collection System")
    print("=" * 40)
    
    # Uncomment based on your setup:
    
    # Option 1: Real sensor data collection
    # collect_data(duration_hours=48, interval_minutes=30)
    
    # Option 2: Simulated data (if no hardware available)
    simulate_data()
