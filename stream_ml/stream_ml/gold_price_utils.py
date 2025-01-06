import pickle
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import StandardScaler

class GoldPriceModel:
    def __init__(self, model_path = 'stream_ml/models/gold_price_model.pkl', scaler_path = 'stream_ml/models/gold_price_scaler.pkl'):
        self.model, self.scaler = self.load_model_and_scaler(model_path=model_path, scaler_path=scaler_path)
        self.historical_data = []

    def load_model_and_scaler(self, model_path='stream_ml/models/gold_price_model.pkl', scaler_path='stream_ml/models/gold_price_scaler.pkl'):
        """
        Load the trained model and scaler from pickle files.
        """
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
        
        return model, scaler

    def prepare_features(self, message_data):
        """
        Prepare features for prediction using the current message and historical data.
        """
        # Create current row data
        current_data = {
            'datetime': pd.to_datetime(message_data['date'] + ' ' + message_data['time']),
            'open': float(message_data['open']),
            'high': float(message_data['high']),
            'low': float(message_data['low']),
            'close': float(message_data['close']),
            'volume': float(message_data['volume'])
        }
        
        # Add current row to historical data
        self.historical_data.append(current_data)
        
        # Keep only last 24 hours of data
        if len(self.historical_data) > 24:
            self.historical_data.pop(0)
        
        # Convert to DataFrame
        df = pd.DataFrame(self.historical_data)
        
        # Extract time features
        current_datetime = current_data['datetime']
        features = {
            'hour': current_datetime.hour,
            'day_of_week': current_datetime.dayofweek,
            'month': current_datetime.month,
            'price_range': current_data['high'] - current_data['low'],
            'price_change': current_data['close'] - current_data['open']
        }
        
        # Calculate lagged features
        if len(self.historical_data) >= 3:
            for i in range(1, 4):
                features[f'close_lag_{i}'] = self.historical_data[-i]['close']
                features[f'volume_lag_{i}'] = self.historical_data[-i]['volume']
                features[f'range_lag_{i}'] = self.historical_data[-i]['high'] - self.historical_data[-i]['low']
        else:
            # Fill with zeros if not enough historical data
            for i in range(1, 4):
                features[f'close_lag_{i}'] = 0
                features[f'volume_lag_{i}'] = 0
                features[f'range_lag_{i}'] = 0
        
        # Calculate rolling statistics if enough data
        if len(df) >= 24:
            features['rolling_mean_price'] = df['close'].rolling(window=24).mean().iloc[-1]
            features['rolling_std_price'] = df['close'].rolling(window=24).std().iloc[-1]
            features['rolling_volume'] = df['volume'].rolling(window=24).mean().iloc[-1]
        else:
            features['rolling_mean_price'] = df['close'].mean()
            features['rolling_std_price'] = df['close'].std() if len(df) > 1 else 0
            features['rolling_volume'] = df['volume'].mean()
        
        # Create DataFrame with features in correct order
        feature_order = [
            'hour', 'day_of_week', 'month', 
            'price_range', 'price_change',
            'close_lag_1', 'close_lag_2', 'close_lag_3',
            'volume_lag_1', 'volume_lag_2', 'volume_lag_3',
            'range_lag_1', 'range_lag_2', 'range_lag_3',
            'rolling_mean_price', 'rolling_std_price', 'rolling_volume'
        ]
        
        return pd.DataFrame([features])[feature_order]

    def predict_price(self, message_data):
        """
        Predict the next hour's closing price based on the current message data.
        """
        features = self.prepare_features(message_data)
        scaled_features = self.scaler.transform(features)
        prediction = self.model.predict(scaled_features)
        return prediction[0]