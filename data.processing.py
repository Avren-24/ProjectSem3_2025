"""
Data Preprocessing Module
Denoising, Normalization, and Feature Engineering
"""

import pandas as pd
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

class DataPreprocessor:
    def __init__(self, data_path):
        """
        Initialize preprocessor with data
        """
        self.data = pd.read_csv(data_path)
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        self.data.set_index('timestamp', inplace=True)
        
    def apply_moving_average(self, column='moisture', window_size=5):
        """
        Apply moving average denoising
        """
        self.data[f'{column}_smooth'] = self.data[column].rolling(
            window=window_size, center=True, min_periods=1
        ).mean()
        return self.data[f'{column}_smooth']
    
    def apply_median_filter(self, column='moisture', kernel_size=5):
        """
        Apply median filter denoising
        """
        self.data[f'{column}_median'] = self.data[column].rolling(
            window=kernel_size, center=True, min_periods=1
        ).median()
        return self.data[f'{column}_median']
    
    def apply_savitzky_golay(self, column='moisture', window=11, order=2):
        """
        Apply Savitzky-Golay filter for smoothing
        """
        try:
            self.data[f'{column}_sg'] = signal.savgol_filter(
                self.data[column], window_length=window, polyorder=order
            )
            return self.data[f'{column}_sg']
        except:
            print("Savitzky-Golay filter failed, using moving average instead")
            return self.apply_moving_average(column, window)
    
    def normalize_data(self, columns=None):
        """
        Normalize data to [0, 1] range
        """
        if columns is None:
            columns = ['moisture', 'temperature', 'humidity']
        
        self.scalers = {}
        
        for col in columns:
            if col in self.data.columns:
                scaler = MinMaxScaler()
                self.data[f'{col}_normalized'] = scaler.fit_transform(
                    self.data[[col]]
                )
                self.scalers[col] = scaler
        
        return self.data[[f'{col}_normalized' for col in columns if f'{col}_normalized' in self.data.columns]]
    
    def create_features(self):
        """
        Create additional time-series features
        """
        # Time-based features
        self.data['hour'] = self.data.index.hour
        self.data['day_of_week'] = self.data.index.dayofweek
        self.data['is_daytime'] = ((self.data['hour'] >= 6) & (self.data['hour'] <= 18)).astype(int)
        
        # Rolling statistics
        self.data['moisture_6h_mean'] = self.data['moisture'].rolling(window=12, min_periods=1).mean()
        self.data['moisture_12h_mean'] = self.data['moisture'].rolling(window=24, min_periods=1).mean()
        
        # Rate of change
        self.data['moisture_change'] = self.data['moisture'].diff()
        self.data['moisture_change_pct'] = self.data['moisture'].pct_change() * 100
        
        # Fill NaN values
        self.data.fillna(method='bfill', inplace=True)
        self.data.fillna(method='ffill', inplace=True)
        
        return self.data
    
    def plot_comparison(self, original_col='moisture', smooth_col='moisture_smooth'):
        """
        Plot original vs smoothed data
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Original vs Smoothed
        axes[0, 0].plot(self.data.index, self.data[original_col], 
                       alpha=0.5, label='Original', linewidth=1)
        axes[0, 0].plot(self.data.index, self.data[smooth_col], 
                       label='Smoothed', linewidth=2)
        axes[0, 0].set_title('Original vs Smoothed Data')
        axes[0, 0].set_xlabel('Time')
        axes[0, 0].set_ylabel('Moisture')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Distribution comparison
        axes[0, 1].hist(self.data[original_col], bins=30, alpha=0.5, 
                       label='Original', density=True)
        axes[0, 1].hist(self.data[smooth_col], bins=30, alpha=0.5, 
                       label='Smoothed', density=True)
        axes[0, 1].set_title('Distribution Comparison')
        axes[0, 1].set_xlabel('Moisture Value')
        axes[0, 1].set_ylabel('Density')
        axes[0, 1].legend()
        
        # Normalized data
        if 'moisture_normalized' in self.data.columns:
            axes[1, 0].plot(self.data.index, self.data['moisture_normalized'])
            axes[1, 0].set_title('Normalized Moisture Data')
            axes[1, 0].set_xlabel('Time')
            axes[1, 0].set_ylabel('Normalized Moisture')
            axes[1, 0].grid(True, alpha=0.3)
        
        # Rate of change
        if 'moisture_change' in self.data.columns:
            axes[1, 1].plot(self.data.index, self.data['moisture_change'])
            axes[1, 1].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[1, 1].set_title('Moisture Change Rate')
            axes[1, 1].set_xlabel('Time')
            axes[1, 1].set_ylabel('Change Rate')
            axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('data/preprocessing_comparison.png', dpi=150, bbox_inches='tight')
        plt.show()
        
        return fig
    
    def save_processed_data(self, output_path='data/processed_data.csv'):
        """
        Save processed data to CSV
        """
        self.data.to_csv(output_path)
        print(f"Processed data saved to: {output_path}")
        return output_path

# Main execution
if __name__ == "__main__":
    # Example usage
    preprocessor = DataPreprocessor('data/raw_moisture_data.csv')
    
    # Apply denoising
    preprocessor.apply_moving_average('moisture', window_size=5)
    preprocessor.apply_savitzky_golay('moisture', window=11, order=2)
    
    # Normalize data
    preprocessor.normalize_data(['moisture', 'temperature', 'humidity'])
    
    # Create features
    preprocessor.create_features()
    
    # Plot results
    preprocessor.plot_comparison('moisture', 'moisture_smooth')
    
    # Save processed data
    preprocessor.save_processed_data()
