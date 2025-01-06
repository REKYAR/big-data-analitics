from river import neighbors, preprocessing
from kafka import KafkaConsumer, KafkaProducer, errors
from collections import deque
from datetime import datetime, timedelta
import json
from typing import Dict, Tuple, List, Optional
import time
import csv
from io import StringIO
import numpy as np

class MultiPairPredictor:
    def __init__(self, target_pairs: List[str], metrics_producer: KafkaProducer, learning_delay_minutes: int = 1):
        """
        Initialize predictors for multiple trading pairs.
        
        Args:
            target_pairs: List[str] - List of cryptocurrency pairs to predict (e.g., ['BTC/USD', 'ETH/USD'])
            learning_delay_minutes: int - How long to wait before using data for training
        """
        self.predictors = {
            pair: SinglePairPredictor(pair, learning_delay_minutes)
            for pair in target_pairs
        }
        self.most_recent_prices = {pair: [datetime.now().isoformat(), 0] for pair in target_pairs}
        self.metrics_producer = metrics_producer

    def _get_row(self, message: str, row_number: int) -> List[str]:
        """Get a specific row from a CSV message."""
        reader = csv.reader(StringIO(message))
        for _ in range(row_number):
            next(reader)
        return next(reader)

    def _parse_columns(self, message: str) -> Tuple[List[str], Optional[Dict[str, int]]]:
        """Parse message headers and return column indices for target pairs if present."""
        try:
            header = self._get_row(message, 0)  # Get first row (header)

            if 'timestamp' not in header:
                raise ValueError("Message missing required timestamp column")
                
            column_indices = {
                pair: idx for pair in self.predictors.keys()
                for idx, col in enumerate(header)
                if col == pair
            }
            
            return header, column_indices
            
        except StopIteration:
            raise ValueError("Empty message received")

    def _parse_row(self, message: str, header: List[str], column_indices: Dict[str, int]) -> Dict:
        """Parse a data row into a dictionary with present values."""
        try:
            row = self._get_row(message, 1)  # Get second row (data)
            if len(row) != len(header):
                raise ValueError(f"Row length {len(row)} doesn't match header length {len(header)}")
                
            timestamp = datetime.strptime(row[header.index('timestamp')], '%Y-%m-%dT%H:%M:%SZ')
            
            data = {
                pair: float(row[idx])
                for pair, idx in column_indices.items()
                if idx < len(row) and row[idx].strip()
            }
            
            return {'timestamp': timestamp, 'data': data}
            
        except (StopIteration, ValueError, IndexError) as e:
            raise ValueError(f"Error parsing row: {str(e)}")

    def process_message(self, message: str) -> Dict[str, Tuple[float, datetime]]:
        """Process incoming message for all available pairs."""
        try:
            header, column_indices = self._parse_columns(message)
            if not column_indices:  # If none of our target pairs are present
                return {}
                
            parsed_data = self._parse_row(message, header, column_indices)
            predictions = {}
            
            # Only process pairs that are present in this message
            for pair, value in parsed_data['data'].items():
                predictor = self.predictors[pair]
                timestamp = parsed_data['timestamp']
                prediction = predictor.process_message(value, timestamp)
                if prediction is not None:
                    predictions[pair] = prediction
                    
            return predictions
            
        except ValueError as e:
            print(f"Warning: Skipping invalid message: {str(e)}")
            return {}

    def update_historical_prices(self, message: str):
        """Update historical prices for all available pairs."""
        try:
            header, column_indices = self._parse_columns(message)
            if not column_indices:  # If none of our target pairs are present
                return
                
            parsed_data = self._parse_row(message, header, column_indices)
            
            # Only update pairs that are present in this message
            for pair, value in parsed_data['data'].items():
                self.most_recent_prices[pair] = [parsed_data['timestamp'], value]
                predictor = self.predictors[pair]
                predictor.update_historical_price(value, parsed_data['timestamp'])
                
        except ValueError as e:
            print(f"Warning: Skipping invalid message for historical update: {str(e)}")

    def send_metrics(self, metrics_id: int):
        """Send metrics for all available pairs."""
        def calculate_mape(predictions, prices):
            return np.mean(np.abs(np.array(predictions) - np.array(prices)) / np.array(prices))

        def calculate_rmse(predictions, prices):
            return np.sqrt(np.mean((np.array(predictions) - np.array(prices)) ** 2))

        for pair, predictor in self.predictors.items():
            if len(predictor.last_10_features) < 10:
                print(f"Warning: Not enough data to calculate metrics for {pair}, only {len(predictor.last_10_features)} samples available")
                continue
            try:
                predictions = []
                for feature in predictor.last_10_features:
                    predictions.append(predictor.model.predict_one(feature))
                self.metrics_producer.send(
                    'model_metrics',
                    value=f"{metrics_id},alpaca_{pair},{'MAPE'},{calculate_mape(predictions, predictor.last_10_prices)},{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}".encode('utf-8')
                    )
                self.metrics_producer.send(
                    'model_metrics',
                    value=f"{metrics_id},alpaca_{pair},{'RMSE'},{calculate_rmse(predictions, predictor.last_10_prices)},{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}".encode('utf-8')
                    )
            except errors.KafkaError as e:
                print(f"Warning: Error sending metrics for {pair}: {str(e)}")

class SinglePairPredictor:
    def __init__(self, target_pair: str, metrics_producer: KafkaProducer, learning_delay_minutes: int = 1):
        self.target_pair = target_pair
        self.model = preprocessing.StandardScaler() | neighbors.KNNRegressor(
            n_neighbors=5
        )
        self.prediction_buffer = deque()
        self.learning_delay = timedelta(minutes=learning_delay_minutes)
        self.last_10_features = deque(maxlen=10)
        self.last_10_prices = deque(maxlen=10)
        self.last_timestamp = None
        
    def _extract_features(self, price: float) -> Dict:
        """Extract features from the price data."""
        return {'price': price}
        
    def process_message(self, price: float, timestamp: datetime) -> Optional[Tuple[float, datetime]]:
        """Process a single price point."""
        try:
            features = self._extract_features(price)
            prediction = self.model.predict_one(features)
            
            self.prediction_buffer.append({
                'features': features,
                'timestamp': timestamp + timedelta(minutes=1),
                'actual_price': None
            })
            
            self._clean_prediction_buffer()
            
            return prediction, timestamp
            
        except Exception as e:
            print(f"Warning: Error processing message for {self.target_pair}: {str(e)}")
            return None
    
    def update_historical_price(self, price: float, timestamp: datetime):
        """Update model with historical price."""

        try:
            current_time = timestamp
            for entry in self.prediction_buffer:
                time_diff = current_time - entry['timestamp']
                if self.last_timestamp is None or entry['timestamp'] > self.last_timestamp:
                    self.last_timestamp = entry['timestamp']
                
                if entry['actual_price'] is None:
                    self.last_10_features.append(entry['features'])
                    self.last_10_prices.append(price)
                    entry['actual_price'] = price
                    self.model.learn_one(entry['features'], entry['actual_price'])


                    
        except Exception as e:
            print(f"Warning: Error updating historical price for {self.target_pair}: {str(e)}")
    
    def _clean_prediction_buffer(self):
        """Remove old entries from the prediction buffer."""
        current_time = datetime.now()
        while self.prediction_buffer:
            oldest_entry = self.prediction_buffer[0]['timestamp']
            if current_time - oldest_entry > self.learning_delay * 3:
                self.prediction_buffer.popleft()
            else:
                break