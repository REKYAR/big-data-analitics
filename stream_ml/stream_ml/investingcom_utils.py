import pickle
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import StandardScaler

class InvestingModel:
    def __init__(self, entities):
        self.models = {}
        self.scalers = {}
        for entity in entities:
            model_path = f'stream_ml/models/{entity}_model.pkl'
            scaler_path = f'stream_ml/models/{entity}_scaler.pkl'
            self.models[entity], self.scalers[entity] = self.load_model_and_scaler(entity)
        self.historical_data = []

    def load_model_and_scaler(self, entity):
        """
        Load the trained model and scaler from pickle files.
        """
        model_path=f'stream_ml/models/{entity}_model.pkl'
        scaler_path=f'stream_ml/models/{entity}_scaler.pkl'

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
            'date': pd.to_datetime(message_data['date']),
            'open': float(message_data['open']),
            'high': float(message_data['high']),
            'low': float(message_data['low']),
            'volume': float(message_data['volume'])
        }
        
        # Add current row to historical data
        self.historical_data.append(current_data)
        
        # Keep only last 7 days of data
        if len(self.historical_data) > 7:
            self.historical_data.pop(0)
        
        # Convert to DataFrame
        df = pd.DataFrame(self.historical_data)
        
        # Extract time features
        current_date = current_data['date']
        features = {
            'day_of_week': current_date.dayofweek,
            'month': current_date.month,
            'price_range': current_data['high'] - current_data['low'],
        }
        
        # Calculate lagged features
        if len(self.historical_data) >= 3:
            for i in range(1, 4):
                features[f'volume_lag_{i}'] = self.historical_data[-i]['volume']
                features[f'range_lag_{i}'] = self.historical_data[-i]['high'] - self.historical_data[-i]['low']
        else:
            # Fill with zeros if not enough historical data
            for i in range(1, 4):
                features[f'volume_lag_{i}'] = 0
                features[f'range_lag_{i}'] = 0
        
        # Calculate rolling statistics if enough data
        if len(df) >= 24:
            features['rolling_mean_price'] = df['high'].rolling(window=24).mean().iloc[-1]
            features['rolling_std_price'] = df['high'].rolling(window=24).std().iloc[-1]
            features['rolling_volume'] = df['volume'].rolling(window=24).mean().iloc[-1]
        else:
            features['rolling_mean_price'] = df['high'].mean()
            features['rolling_std_price'] = df['high'].std() if len(df) > 1 else 0
            features['rolling_volume'] = df['volume'].mean()
        
        # Create DataFrame with features in correct order
        feature_order = ['day_of_week', 'month',
        'price_range', 
        'volume_lag_1', 'volume_lag_2', 'volume_lag_3',
        'range_lag_1', 'range_lag_2', 'range_lag_3',
        'rolling_mean_price', 'rolling_std_price', 'rolling_volume']
        
        return pd.DataFrame([features])[feature_order]

    def predict_price(self, message_data, entity):
        """
        Predict the next day's high price based on the current message data.
        """
        features = self.prepare_features(message_data)
        scaled_features = self.scalers[entity].transform(features)
        prediction = self.models[entity].predict(scaled_features)
        return prediction[0]