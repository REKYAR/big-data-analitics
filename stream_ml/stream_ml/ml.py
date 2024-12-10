from kafka import KafkaConsumer, KafkaProducer, errors
from river import neighbors, evaluate, metrics
import datetime
import time
from predictor import MultiPairPredictor
from typing import List
import logging

def has_null_bytes(message):
    """
    Check if a message contains NULL bytes (\0).
    
    Args:
        message (str or bytes): The message to check
        
    Returns:
        bool: True if NULL bytes are found, False otherwise
    """
    if isinstance(message, bytes):
        return b'\0' in message
    return '\0' in message

def run_multi_predictor(target_pairs: List[str]):

    predictor = MultiPairPredictor(target_pairs)

    while True:
        try:
            consumer = KafkaConsumer(
                'alpaca_silver',
                bootstrap_servers=['kafka:9092']
            )
            logging.info("Successfully connected to Kafka")
            break
        except errors.NoBrokersAvailable as e:
            logging.error(f"Failed to connect to Kafka: {e}")
            time.sleep(10)

    producer = KafkaProducer(
        bootstrap_servers=['kafka:9092']
    )

    for message in consumer:
        if has_null_bytes(message.value):
            continue

        message = message.value.decode('utf-8')
        print(message)

        # Make predictions for available pairs
        predictions = predictor.process_message(message)
        
        # Print predictions for pairs that were present and successfully processed
        for pair, (prediction, timestamp) in predictions.items():
            
            producer.send(
                'alpaca_predictions', 
                value=f"{pair},{timestamp.isoformat()},{prediction}".encode('utf-8')
                )
        
        # Update models with historical data
        predictor.update_historical_prices(message)


if __name__ == "__main__":
    pairs_to_predict = ['BTC/USD', 'ETH/USD', 'DOGE/USD']
    run_multi_predictor(pairs_to_predict)
