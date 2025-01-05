import pandas as pd
import numpy as np
import pickle
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler

def prepare_data(df):
    """
    Prepare the dataset by creating relevant features for time series prediction.
    """
    # Ensure datetime format
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    
    # Sort by datetime to ensure proper order
    df = df.sort_values('datetime')
    
    # Create time-based features
    df['hour'] = df['datetime'].dt.hour
    df['day_of_week'] = df['datetime'].dt.dayofweek
    df['month'] = df['datetime'].dt.month
    
    # Create price-based features
    df['price_range'] = df['high'] - df['low']
    df['price_change'] = df['close'] - df['open']
    
    # Create lagged features (previous hours)
    for i in range(1, 4):  # Using last 3 hours
        df[f'close_lag_{i}'] = df['close'].shift(i)
        df[f'volume_lag_{i}'] = df['volume'].shift(i)
        df[f'range_lag_{i}'] = df['price_range'].shift(i)
    
    # Create rolling statistics
    df['rolling_mean_price'] = df['close'].rolling(window=24).mean()  # 24-hour moving average
    df['rolling_std_price'] = df['close'].rolling(window=24).std()
    df['rolling_volume'] = df['volume'].rolling(window=24).mean()
    
    # Create target variable (next hour's closing price)
    df['target'] = df['close'].shift(-1)
    
    # Drop rows with NaN values
    df = df.dropna()
    
    return df

def split_data(df, train_ratio=0.8):
    """
    Split the data into training and testing sets, preserving time order.
    """
    train_size = int(len(df) * train_ratio)
    train_data = df.iloc[:train_size]
    test_data = df.iloc[train_size:]
    
    feature_columns = ['hour', 'day_of_week', 'month', 
                      'price_range', 'price_change',
                      'close_lag_1', 'close_lag_2', 'close_lag_3',
                      'volume_lag_1', 'volume_lag_2', 'volume_lag_3',
                      'range_lag_1', 'range_lag_2', 'range_lag_3',
                      'rolling_mean_price', 'rolling_std_price', 'rolling_volume']
    
    return (train_data[feature_columns], train_data['target'],
            test_data[feature_columns], test_data['target'])

def train_model(X_train, y_train):
    """
    Train an XGBoost model with optimized parameters.
    """
    model = XGBRegressor(
        n_estimators=1000,
        learning_rate=0.01,
        max_depth=4,
        min_child_weight=3,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=1307
    )
    
    # Train the model
    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train)],
        verbose=100
    )
    
    return model

def evaluate_model(model, X_test, y_test):
    """
    Evaluate the model using multiple metrics.
    """
    predictions = model.predict(X_test)
    
    results = {
        'RMSE': np.sqrt(mean_squared_error(y_test, predictions)),
        'MAE': mean_absolute_error(y_test, predictions),
        'R2': r2_score(y_test, predictions)
    }
    
    return results

def save_model_and_scaler(model, scaler, model_path='stream_ml/models/gold_price_model.pkl', scaler_path='stream_ml/models/gold_price_scaler.pkl'):
    """
    Save the trained model and scaler to pickle files.
    """
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    
    print(f"Model saved to {model_path}")
    print(f"Scaler saved to {scaler_path}")

def load_model_and_scaler(model_path='stream_ml/models/gold_price_model.pkl', scaler_path='stream_ml/models/gold_price_scaler.pkl'):
    """
    Load the trained model and scaler from pickle files.
    """
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    
    return model, scaler

# def predict_next_hour(model, current_data):
#     """
#     Make a prediction for the next hour's closing price.
#     """
#     return model.predict(current_data)[0]

# Usage example:
def main():
    # Load your data
    df = pd.read_csv('gold_prices.csv')
    
    # Prepare the data
    prepared_data = prepare_data(df)
    
    # Split the data
    X_train, y_train, X_test, y_test = split_data(prepared_data)
    
    # Scale the features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train the model
    model = train_model(X_train_scaled, y_train)
    
    # Evaluate the model
    results = evaluate_model(model, X_test_scaled, y_test)
    print("Model Performance:")
    for metric, value in results.items():
        print(f"{metric}: {value}")
    
    # Save the model and scaler

    save_model_and_scaler(model, scaler)

if __name__ == "__main__":
    main()