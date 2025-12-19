"""
Machine Learning Models for Moisture Prediction
Linear Regression and LSTM models
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
import warnings
warnings.filterwarnings('ignore')

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

class MoisturePredictor:
    def __init__(self, data_path):
        """
        Initialize predictor with data
        """
        self.data = pd.read_csv(data_path, parse_dates=['timestamp'])
        self.data.set_index('timestamp', inplace=True)
        
    def prepare_data(self, target_col='moisture', forecast_hours=12):
        """
        Prepare data for time series prediction
        forecast_hours: Number of hours to forecast ahead
        """
        # Use smoothed moisture if available
        if 'moisture_smooth' in self.data.columns:
            target_col = 'moisture_smooth'
        
        # Create features and target
        self.data['target'] = self.data[target_col].shift(-forecast_hours*2)  # 30-min intervals
        
        # Remove rows with NaN in target
        self.data_clean = self.data.dropna(subset=['target']).copy()
        
        # Feature selection
        feature_cols = [target_col]
        if 'temperature' in self.data_clean.columns:
            feature_cols.append('temperature')
        if 'humidity' in self.data_clean.columns:
            feature_cols.append('humidity')
        if 'hour' in self.data_clean.columns:
            feature_cols.append('hour')
        if 'moisture_6h_mean' in self.data_clean.columns:
            feature_cols.append('moisture_6h_mean')
        
        self.X = self.data_clean[feature_cols].values
        self.y = self.data_clean['target'].values
        
        print(f"Data shape: {self.X.shape}")
        print(f"Features used: {feature_cols}")
        
        return self.X, self.y, feature_cols
    
    def train_linear_regression(self, test_size=0.2):
        """
        Train linear regression model
        """
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            self.X, self.y, test_size=test_size, shuffle=False
        )
        
        # Train model
        self.lr_model = LinearRegression()
        self.lr_model.fit(X_train, y_train)
        
        # Predictions
        y_train_pred = self.lr_model.predict(X_train)
        y_test_pred = self.lr_model.predict(X_test)
        
        # Calculate metrics
        train_mae = mean_absolute_error(y_train, y_train_pred)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
        train_r2 = r2_score(y_train, y_train_pred)
        
        test_mae = mean_absolute_error(y_test, y_test_pred)
        test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
        test_r2 = r2_score(y_test, y_test_pred)
        
        print("=" * 60)
        print("LINEAR REGRESSION RESULTS")
        print("=" * 60)
        print(f"Training MAE: {train_mae:.4f}")
        print(f"Training RMSE: {train_rmse:.4f}")
        print(f"Training R²: {train_r2:.4f}")
        print("-" * 40)
        print(f"Test MAE: {test_mae:.4f}")
        print(f"Test RMSE: {test_rmse:.4f}")
        print(f"Test R²: {test_r2:.4f}")
        
        # Feature importance
        if hasattr(self.lr_model, 'coef_'):
            print("\nFeature Coefficients:")
            for i, coef in enumerate(self.lr_model.coef_):
                print(f"  Feature {i}: {coef:.4f}")
        
        return {
            'model': self.lr_model,
            'y_test': y_test,
            'y_test_pred': y_test_pred,
            'metrics': {
                'train_mae': train_mae,
                'train_rmse': train_rmse,
                'train_r2': train_r2,
                'test_mae': test_mae,
                'test_rmse': test_rmse,
                'test_r2': test_r2
            }
        }
    
    def prepare_lstm_data(self, sequence_length=24):
        """
        Prepare data for LSTM (3D format)
        """
        X_seq, y_seq = [], []
        
        for i in range(len(self.X) - sequence_length):
            X_seq.append(self.X[i:i+sequence_length])
            y_seq.append(self.y[i+sequence_length])
        
        X_seq = np.array(X_seq)
        y_seq = np.array(y_seq)
        
        # Split data (80% train, 20% test)
        split_idx = int(len(X_seq) * 0.8)
        X_train = X_seq[:split_idx]
        y_train = y_seq[:split_idx]
        X_test = X_seq[split_idx:]
        y_test = y_seq[split_idx:]
        
        return X_train, X_test, y_train, y_test
    
    def train_lstm(self, sequence_length=24, epochs=50):
        """
        Train LSTM model
        """
        # Prepare LSTM data
        X_train, X_test, y_train, y_test = self.prepare_lstm_data(sequence_length)
        
        print(f"LSTM Data shapes:")
        print(f"  X_train: {X_train.shape}")
        print(f"  X_test: {X_test.shape}")
        
        # Build LSTM model
        model = Sequential([
            LSTM(64, activation='relu', return_sequences=True, 
                 input_shape=(sequence_length, X_train.shape[2])),
            Dropout(0.2),
            LSTM(32, activation='relu'),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1)
        ])
        
        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        # Early stopping
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        # Train model
        print("\nTraining LSTM model...")
        history = model.fit(
            X_train, y_train,
            validation_split=0.1,
            epochs=epochs,
            batch_size=16,
            callbacks=[early_stop],
            verbose=1
        )
        
        # Predictions
        y_train_pred = model.predict(X_train).flatten()
        y_test_pred = model.predict(X_test).flatten()
        
        # Calculate metrics
        train_mae = mean_absolute_error(y_train, y_train_pred)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
        train_r2 = r2_score(y_train, y_train_pred)
        
        test_mae = mean_absolute_error(y_test, y_test_pred)
        test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
        test_r2 = r2_score(y_test, y_test_pred)
        
        print("=" * 60)
        print("LSTM MODEL RESULTS")
        print("=" * 60)
        print(f"Training MAE: {train_mae:.4f}")
        print(f"Training RMSE: {train_rmse:.4f}")
        print(f"Training R²: {train_r2:.4f}")
        print("-" * 40)
        print(f"Test MAE: {test_mae:.4f}")
        print(f"Test RMSE: {test_rmse:.4f}")
        print(f"Test R²: {test_r2:.4f}")
        
        self.lstm_model = model
        self.lstm_history = history
        
        return {
            'model': model,
            'history': history,
            'y_test': y_test,
            'y_test_pred': y_test_pred,
            'metrics': {
                'train_mae': train_mae,
                'train_rmse': train_rmse,
                'train_r2': train_r2,
                'test_mae': test_mae,
                'test_rmse': test_rmse,
                'test_r2': test_r2
            }
        }
    
    def plot_predictions(self, lr_results, lstm_results):
        """
        Plot model predictions vs actual values
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Linear Regression predictions
        axes[0, 0].plot(lr_results['y_test'][:100], label='Actual', 
                       linewidth=2, alpha=0.7)
        axes[0, 0].plot(lr_results['y_test_pred'][:100], label='Predicted', 
                       linewidth=2, linestyle='--', alpha=0.7)
        axes[0, 0].set_title('Linear Regression: Actual vs Predicted (First 100 samples)', 
                           fontsize=14, fontweight='bold')
        axes[0, 0].set_xlabel('Sample Index')
        axes[0, 0].set_ylabel('Moisture')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # LSTM predictions
        axes[0, 1].plot(lstm_results['y_test'][:100], label='Actual', 
                       linewidth=2, alpha=0.7)
        axes[0, 1].plot(lstm_results['y_test_pred'][:100], label='Predicted', 
                       linewidth=2, linestyle='--', alpha=0.7)
        axes[0, 1].set_title('LSTM: Actual vs Predicted (First 100 samples)', 
                           fontsize=14, fontweight='bold')
        axes[0, 1].set_xlabel('Sample Index')
        axes[0, 1].set_ylabel('Moisture')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # LSTM training history
        axes[1, 0].plot(lstm_results['history'].history['loss'], 
                       label='Training Loss', linewidth=2)
        axes[1, 0].plot(lstm_results['history'].history['val_loss'], 
                       label='Validation Loss', linewidth=2)
        axes[1, 0].set_title('LSTM Training History', fontsize=14, fontweight='bold')
        axes[1, 0].set_xlabel('Epoch')
        axes[1, 0].set_ylabel('Loss (MSE)')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # Model comparison
        metrics_df = pd.DataFrame({
            'Linear Regression': [
                lr_results['metrics']['test_mae'],
                lr_results['metrics']['test_rmse'],
                lr_results['metrics']['test_r2']
            ],
            'LSTM': [
                lstm_results['metrics']['test_mae'],
                lstm_results['metrics']['test_rmse'],
                lstm_results['metrics']['test_r2']
            ]
        }, index=['MAE', 'RMSE', 'R²'])
        
        x = np.arange(len(metrics_df))
        width = 0.35
        
        axes[1, 1].bar(x - width/2, metrics_df['Linear Regression'], 
                      width, label='Linear Regression', alpha=0.8)
        axes[1, 1].bar(x + width/2, metrics_df['LSTM'], 
                      width, label='LSTM', alpha=0.8)
        axes[1, 1].set_title('Model Performance Comparison', fontsize=14, fontweight='bold')
        axes[1, 1].set_xlabel('Metric')
        axes[1, 1].set_ylabel('Value')
        axes[1, 1].set_xticks(x)
        axes[1, 1].set_xticklabels(metrics_df.index)
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for i, v in enumerate(metrics_df['Linear Regression']):
            axes[1, 1].text(i - width/2, v + 0.01, f'{v:.3f}', 
                          ha='center', va='bottom', fontsize=9)
        for i, v in enumerate(metrics_df['LSTM']):
            axes[1, 1].text(i + width/2, v + 0.01, f'{v:.3f}', 
                          ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig('data/model_predictions.png', dpi=150, bbox_inches='tight')
        plt.show()
        
        return fig
    
    def forecast_future(self, hours_ahead=24):
        """
        Generate future predictions
        """
        if hasattr(self, 'lstm_model'):
            # Use last sequence for prediction
            last_sequence = self.X[-self.lstm_model.input_shape[1]:]
            last_sequence = last_sequence.reshape(1, -1, self.X.shape[1])
            
            # Generate multi-step forecast
            forecasts = []
            current_sequence = last_sequence.copy()
            
            for _ in range(hours_ahead * 2):  # 30-min intervals
                pred = self.lstm_model.predict(current_sequence, verbose=0)[0, 0]
                forecasts.append(pred)
                
                # Update sequence (simplified - in practice would need feature updates)
                new_row = current_sequence[0, -1].copy()
                new_row[0] = pred  # Update moisture value
                current_sequence = np.roll(current_sequence, -1, axis=1)
                current_sequence[0, -1] = new_row
            
            # Create forecast timeline
            last_timestamp = self.data.index[-1]
            forecast_timestamps = pd.date_range(
                start=last_timestamp + pd.Timedelta(minutes=30),
                periods=len(forecasts),
                freq='30min'
            )
            
            forecast_df = pd.DataFrame({
                'timestamp': forecast_timestamps,
                'predicted_moisture': forecasts
            })
            
            # Plot forecast
            plt.figure(figsize=(12, 6))
            plt.plot(self.data.index[-48:], self.data['moisture_smooth'][-48:], 
                    label='Historical', linewidth=2)
            plt.plot(forecast_timestamps, forecasts, 
                    label='Forecast', linewidth=2, linestyle='--')
            plt.axvline(x=last_timestamp, color='red', linestyle=':', 
                       alpha=0.7, label='Now')
            plt.fill_between(forecast_timestamps, 
                           np.array(forecasts) * 0.9, 
                           np.array(forecasts) * 1.1, 
                           alpha=0.2, color='green', label='Confidence Interval')
            plt.title(f'{hours_ahead}-Hour Moisture Forecast', fontsize=16, fontweight='bold')
            plt.xlabel('Time')
            plt.ylabel('Moisture')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig('data/future_forecast.png', dpi=150, bbox_inches='tight')
            plt.show()
            
            return forecast_df
        
        return None

# Main execution
if __name__ == "__main__":
    # Initialize predictor
    predictor = MoisturePredictor('data/processed_data.csv')
    
    # Prepare data
    X, y, features = predictor.prepare_data(forecast_hours=12)
    
    # Train Linear Regression
    print("\n" + "="*60)
    print("TRAINING LINEAR REGRESSION MODEL")
    print("="*60)
    lr_results = predictor.train_linear_regression(test_size=0.2)
    
    # Train LSTM
    print("\n" + "="*60)
    print("TRAINING LSTM MODEL")
    print("="*60)
    lstm_results = predictor.train_lstm(sequence_length=24, epochs=50)
    
    # Plot results
    predictor.plot_predictions(lr_results, lstm_results)
    
    # Generate future forecast
    print("\n" + "="*60)
    print("GENERATING FUTURE FORECAST")
    print("="*60)
    forecast_df = predictor.forecast_future(hours_ahead=24)
    
    if forecast_df is not None:
        print(f"\n24-hour Forecast Summary:")
        print(f"Start: {forecast_df['timestamp'].iloc[0]}")
        print(f"End: {forecast_df['timestamp'].iloc[-1]}")
        print(f"Initial moisture: {forecast_df['predicted_moisture'].iloc[0]:.2f}")
        print(f"Final moisture: {forecast_df['predicted_moisture'].iloc[-1]:.2f}")
        print(f"Total change: {forecast_df['predicted_moisture'].iloc[-1] - forecast_df['predicted_moisture'].iloc[0]:.2f}")
        
        # Check if watering is needed
        watering_threshold = 30  # Example threshold
        min_forecast = forecast_df['predicted_moisture'].min()
        if min_forecast < watering_threshold:
            min_time = forecast_df.loc[forecast_df['predicted_moisture'].idxmin(), 'timestamp']
            print(f"\n⚠️  ALERT: Plant will need watering around {min_time}")
            print(f"  Predicted minimum moisture: {min_forecast:.2f}")
        else:
            print(f"\n✅ No watering needed in next 24 hours")
            print(f"  Minimum predicted moisture: {min_forecast:.2f}")
