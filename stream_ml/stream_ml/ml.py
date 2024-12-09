from kafka import KafkaConsumer, KafkaProducer
from river import neighbors, evaluate, metrics
import datetime
import time
from predictor import MultiPairPredictor
from typing import List

def run_multi_predictor(target_pairs: List[str]):
    predictor = MultiPairPredictor(target_pairs=target_pairs, learning_delay_minutes=1)
    
    consumer = KafkaConsumer(
        'alpaca_silver',
        bootstrap_servers=['localhost:9092']
    )

    producer = KafkaProducer(
        bootstrap_servers=['localhost:9092']
    )

    for message in consumer:
        # Make predictions for available pairs
        predictions = predictor.process_message(message.value)
        
        # Print predictions for pairs that were present and successfully processed
        for pair, (prediction, timestamp) in predictions.items():
            producer.send('alpaca_predictions', value=f"{pair},{timestamp},{prediction}")
        
        # Update models with historical data
        predictor.update_historical_prices(message.value)

if __name__ == "__main__":
    pairs_to_predict = ['BTC/USD', 'ETH/USD', 'DOGE/USD']
    run_multi_predictor(pairs_to_predict)
