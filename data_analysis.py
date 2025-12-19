"""
Data Analysis and Visualization Module
Descriptive statistics and time-series visualization
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class DataAnalyzer:
    def __init__(self, data_path):
        """
        Initialize analyzer with data
        """
        self.data = pd.read_csv(data_path, parse_dates=['timestamp'])
        self.data.set_index('timestamp', inplace=True)
        
    def calculate_statistics(self):
        """
        Calculate descriptive statistics
        """
        stats_dict = {}
        
        for column in ['moisture', 'temperature', 'humidity']:
            if column in self.data.columns:
                col_data = self.data[column].dropna()
                
                stats_dict[column] = {
                    'count': len(col_data),
                    'mean': np.mean(col_data),
                    'std': np.std(col_data),
                    'min': np.min(col_data),
                    '25%': np.percentile(col_data, 25),
                    '50%': np.percentile(col_data, 50),
                    '75%': np.percentile(col_data, 75),
                    'max': np.max(col_data),
                    'range': np.max(col_data) - np.min(col_data),
                    'variance': np.var(col_data),
                    'skewness': stats.skew(col_data),
                    'kurtosis': stats.kurtosis(col_data)
                }
        
        # Convert to DataFrame for better display
        stats_df = pd.DataFrame(stats_dict).T
        
        print("=" * 60)
        print("DESCRIPTIVE STATISTICS")
        print("=" * 60)
        print(stats_df.round(3))
        
        return stats_df
    
    def plot_time_series(self):
        """
        Create time-series plots
        """
        fig, axes = plt.subplots(3, 2, figsize=(16, 12))
        
        # Moisture over time
        axes[0, 0].plot(self.data.index, self.data['moisture'], 
                       color='blue', linewidth=2, alpha=0.7)
        axes[0, 0].set_title('Soil Moisture Over Time', fontsize=14, fontweight='bold')
        axes[0, 0].set_xlabel('Time')
        axes[0, 0].set_ylabel('Moisture Level')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Rolling average of moisture
        if 'moisture_smooth' in self.data.columns:
            axes[0, 1].plot(self.data.index, self.data['moisture_smooth'], 
                          color='green', linewidth=2)
            axes[0, 1].set_title('Smoothed Moisture (Moving Average)', fontsize=14, fontweight='bold')
            axes[0, 1].set_xlabel('Time')
            axes[0, 1].set_ylabel('Smoothed Moisture')
            axes[0, 1].grid(True, alpha=0.3)
        
        # Temperature over time
        if 'temperature' in self.data.columns:
            axes[1, 0].plot(self.data.index, self.data['temperature'], 
                          color='red', linewidth=2, alpha=0.7)
            axes[1, 0].set_title('Temperature Over Time', fontsize=14, fontweight='bold')
            axes[1, 0].set_xlabel('Time')
            axes[1, 0].set_ylabel('Temperature (°C)')
            axes[1, 0].grid(True, alpha=0.3)
        
        # Humidity over time
        if 'humidity' in self.data.columns:
            axes[1, 1].plot(self.data.index, self.data['humidity'], 
                          color='purple', linewidth=2, alpha=0.7)
            axes[1, 1].set_title('Humidity Over Time', fontsize=14, fontweight='bold')
            axes[1, 1].set_xlabel('Time')
            axes[1, 1].set_ylabel('Humidity (%)')
            axes[1, 1].grid(True, alpha=0.3)
        
        # Correlation heatmap
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            corr_matrix = self.data[numeric_cols].corr()
            im = axes[2, 0].imshow(corr_matrix, cmap='coolwarm', aspect='auto')
            axes[2, 0].set_title('Feature Correlation Matrix', fontsize=14, fontweight='bold')
            axes[2, 0].set_xticks(range(len(numeric_cols)))
            axes[2, 0].set_xticklabels(numeric_cols, rotation=45, ha='right')
            axes[2, 0].set_yticks(range(len(numeric_cols)))
            axes[2, 0].set_yticklabels(numeric_cols)
            plt.colorbar(im, ax=axes[2, 0])
            
            # Add correlation values
            for i in range(len(numeric_cols)):
                for j in range(len(numeric_cols)):
                    text = axes[2, 0].text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                                          ha="center", va="center", 
                                          color="white" if abs(corr_matrix.iloc[i, j]) > 0.5 else "black")
        
        # Distribution plots
        if 'moisture' in self.data.columns:
            axes[2, 1].hist(self.data['moisture'].dropna(), bins=30, 
                          color='blue', alpha=0.7, edgecolor='black')
            axes[2, 1].axvline(self.data['moisture'].mean(), color='red', 
                             linestyle='--', linewidth=2, label=f'Mean: {self.data["moisture"].mean():.2f}')
            axes[2, 1].axvline(self.data['moisture'].median(), color='green', 
                             linestyle='--', linewidth=2, label=f'Median: {self.data["moisture"].median():.2f}')
            axes[2, 1].set_title('Moisture Distribution', fontsize=14, fontweight='bold')
            axes[2, 1].set_xlabel('Moisture Level')
            axes[2, 1].set_ylabel('Frequency')
            axes[2, 1].legend()
            axes[2, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('data/time_series_analysis.png', dpi=150, bbox_inches='tight')
        plt.show()
        
        return fig
    
    def plot_detailed_analysis(self):
        """
        Create detailed analysis plots
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Box plot for each day
        if 'moisture' in self.data.columns:
            self.data['date'] = self.data.index.date
            daily_stats = self.data.groupby('date')['moisture'].agg(['mean', 'std', 'min', 'max'])
            
            axes[0, 0].boxplot([self.data[self.data['date'] == date]['moisture'].dropna() 
                               for date in self.data['date'].unique()])
            axes[0, 0].set_title('Daily Moisture Distribution (Box Plot)', fontsize=12, fontweight='bold')
            axes[0, 0].set_xlabel('Day')
            axes[0, 0].set_ylabel('Moisture')
            axes[0, 0].set_xticks(range(1, len(daily_stats) + 1))
            axes[0, 0].set_xticklabels([str(d)[5:] for d in daily_stats.index], rotation=45)
            axes[0, 0].grid(True, alpha=0.3)
        
        # Moisture by hour of day
        if 'moisture' in self.data.columns:
            self.data['hour'] = self.data.index.hour
            hourly_avg = self.data.groupby('hour')['moisture'].mean()
            hourly_std = self.data.groupby('hour')['moisture'].std()
            
            axes[0, 1].plot(hourly_avg.index, hourly_avg.values, 
                          marker='o', linewidth=2, color='blue')
            axes[0, 1].fill_between(hourly_avg.index, 
                                   hourly_avg - hourly_std, 
                                   hourly_avg + hourly_std, 
                                   alpha=0.2, color='blue')
            axes[0, 1].set_title('Average Moisture by Hour of Day', fontsize=12, fontweight='bold')
            axes[0, 1].set_xlabel('Hour of Day')
            axes[0, 1].set_ylabel('Average Moisture')
            axes[0, 1].set_xticks(range(0, 24, 2))
            axes[0, 1].grid(True, alpha=0.3)
        
        # Moving statistics
        if 'moisture' in self.data.columns:
            window = 12  # 6 hours for 30-min intervals
            axes[1, 0].plot(self.data.index, self.data['moisture'], 
                          alpha=0.3, label='Raw', linewidth=1)
            axes[1, 0].plot(self.data.index, 
                          self.data['moisture'].rolling(window=window).mean(), 
                          label=f'{window*30/60}-hour Moving Avg', linewidth=2)
            axes[1, 0].plot(self.data.index, 
                          self.data['moisture'].rolling(window=window).std(), 
                          label=f'{window*30/60}-hour Std Dev', linewidth=2, linestyle='--')
            axes[1, 0].set_title('Moving Statistics', fontsize=12, fontweight='bold')
            axes[1, 0].set_xlabel('Time')
            axes[1, 0].set_ylabel('Moisture')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
        
        # Autocorrelation plot
        if 'moisture' in self.data.columns:
            from pandas.plotting import autocorrelation_plot
            autocorrelation_plot(self.data['moisture'].dropna(), ax=axes[1, 1])
            axes[1, 1].set_title('Autocorrelation of Moisture', fontsize=12, fontweight='bold')
            axes[1, 1].set_xlabel('Lag')
            axes[1, 1].set_ylabel('Autocorrelation')
            axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('data/detailed_analysis.png', dpi=150, bbox_inches='tight')
        plt.show()
        
        return fig
    
    def export_report(self):
        """
        Export analysis report to text file
        """
        stats_df = self.calculate_statistics()
        
        with open('data/analysis_report.txt', 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("DATA ANALYSIS REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("1. DATA OVERVIEW\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total records: {len(self.data)}\n")
            f.write(f"Time range: {self.data.index.min()} to {self.data.index.max()}\n")
            f.write(f"Time interval: {pd.Timedelta(self.data.index[1] - self.data.index[0])}\n\n")
            
            f.write("2. DESCRIPTIVE STATISTICS\n")
            f.write("-" * 40 + "\n")
            f.write(stats_df.to_string())
            f.write("\n\n")
            
            f.write("3. DATA QUALITY CHECK\n")
            f.write("-" * 40 + "\n")
            for column in self.data.select_dtypes(include=[np.number]).columns:
                missing = self.data[column].isnull().sum()
                missing_pct = (missing / len(self.data)) * 100
                f.write(f"{column}: {missing} missing values ({missing_pct:.2f}%)\n")
            
            f.write("\n4. KEY INSIGHTS\n")
            f.write("-" * 40 + "\n")
            if 'moisture' in self.data.columns:
                f.write(f"• Moisture decreased from {self.data['moisture'].iloc[0]:.2f} to {self.data['moisture'].iloc[-1]:.2f}\n")
                f.write(f"• Average daily change: {self.data['moisture'].diff().mean():.2f}\n")
                f.write(f"• Maximum 6-hour drop: {self.data['moisture'].rolling(12).apply(lambda x: x[0] - x[-1] if len(x) == 12 else np.nan).max():.2f}\n")
        
        print("Analysis report saved to: data/analysis_report.txt")
        return 'data/analysis_report.txt'

# Main execution
if __name__ == "__main__":
    # Load and analyze data
    analyzer = DataAnalyzer('data/processed_data.csv')
    
    # Calculate statistics
    stats = analyzer.calculate_statistics()
    
    # Create visualizations
    analyzer.plot_time_series()
    analyzer.plot_detailed_analysis()
    
    # Export report
    analyzer.export_report()
