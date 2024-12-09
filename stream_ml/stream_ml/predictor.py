from river import neighbors, preprocessing
from collections import deque
from datetime import datetime, timedelta
import json
from typing import Dict, Tuple, List, Optional
import time
import csv
from io import StringIO
import numpy as np

class MultiPairPredictor:
    def __init__(self, target_pairs: List[str], learning_delay_minutes: int = 1):
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
                prediction = predictor.process_message(value, parsed_data['timestamp'])
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

class SinglePairPredictor:
    def __init__(self, target_pair: str, learning_delay_minutes: int = 1):
        self.target_pair = target_pair
        self.model = preprocessing.StandardScaler() | neighbors.KNNRegressor(
            n_neighbors=5
        )
        self.prediction_buffer = deque()
        self.learning_delay = timedelta(minutes=learning_delay_minutes)
        
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
                'timestamp': timestamp,
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
                
                if time_diff >= self.learning_delay and entry['actual_price'] is None:
                    entry['actual_price'] = price
                    self.model.learn_one(entry['features'], entry['actual_price'])
                    
        except Exception as e:
            print(f"Warning: Error updating historical price for {self.target_pair}: {str(e)}")
    
    def _clean_prediction_buffer(self):
        """Remove old entries from the prediction buffer."""
        current_time = datetime.now()
        while self.prediction_buffer:
            oldest_entry = self.prediction_buffer[0]
            if current_time - oldest_entry['timestamp'] > self.learning_delay * 2:
                self.prediction_buffer.popleft()
            else:
                break