from kafka import KafkaConsumer, KafkaProducer, errors
from river import neighbors, evaluate, metrics
from predictor import MultiPairPredictor
from typing import List
from transformers import pipeline
from io import StringIO
from email.utils import parsedate_to_datetime
import csv
import datetime
import time
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

    last_update_per_pair = {pair: datetime.date.min for pair in target_pairs}
    while True:
        try:
            consumer = KafkaConsumer(
                bootstrap_servers=['kafka:9092'],
                group_id='multi_predictor_group',
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            logging.info("Successfully connected to Kafka")
            break
        except errors.NoBrokersAvailable as e:
            logging.error(f"Failed to connect to Kafka: {e}")
            time.sleep(10)

    consumer.subscribe(['alpaca_silver', 'marketwatch_silver'])

    print("Consumer started")

    producer = KafkaProducer(
        bootstrap_servers=['kafka:9092']
    )

    print("Producer started")

    predictor = MultiPairPredictor(target_pairs, producer)
    sentiment_pipeline = pipeline(model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
    metrics_id = 1

    while True:
        messages = consumer.poll(max_records=100)
        if not messages:
            continue

        for topic, messages in messages.items():
            print(f"Received {len(messages)} messages for topic {topic.topic}")
            if topic.topic == 'alpaca_silver':
                for message in messages:
                    if has_null_bytes(message.value):
                        continue
                    message = message.value.decode('utf-8')
                    print(message)

                    predictions = predictor.process_message(message)
                    
                    for pair, (prediction, timestamp) in predictions.items():

                        if last_update_per_pair[pair] == timestamp: continue

                        last_update_per_pair[pair] = timestamp
                        producer.send(
                            'alpaca_predictions', 
                            value=f"{pair},{timestamp.isoformat()},{prediction}".encode('utf-8')
                            )
                    
                    # Update models with historical data
                    predictor.update_historical_prices(message)
                predictor.send_metrics(metrics_id)
                metrics_id += 1
            elif topic.topic == 'marketwatch_silver':
                for message in messages:
                    if has_null_bytes(message.value):
                        continue
                    message = message.value.decode('utf-8')

                    csv_reader = csv.reader(StringIO(message))
                    next(csv_reader)  # Skip header

                    row = next(csv_reader)
                    id = row[0]
                    title = row[2]
                    timestamp = row[4]
                    sentiment = sentiment_pipeline(title)

                    producer.send(
                        'marketwatch_sentiment', 
                        value=f"{id},{sentiment[0]['label']},{sentiment[0]['score']},{parsedate_to_datetime(timestamp).strftime('%Y-%m-%dT%H:%M:%S')}".encode('utf-8')
                        )

def test_consumer():
    consumer = KafkaConsumer(
        'marketwatch_silver',
        bootstrap_servers=['kafka:9092']
    )

    for message in consumer:
        print(message.value.decode('utf-8'))


if __name__ == "__main__":
    pairs_to_predict = ['BTC/USD', 'ETH/USD', 'DOGE/USD']
    run_multi_predictor(pairs_to_predict)
    test_consumer()
