from kafka import KafkaConsumer, KafkaProducer, errors
from river import neighbors, evaluate, metrics
from predictor import MultiPairPredictor
from typing import List
from transformers import pipeline
from io import StringIO
from email.utils import parsedate_to_datetime
from gold_price_utils import GoldPriceModel
from investingcom_utils import InvestingModel
import pandas as pd
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

    consumer.subscribe(['alpaca_silver', 'marketwatch_silver', 'kaggle_gold_silver', 'investingcom_silver'])

    print("Consumer started")

    producer = KafkaProducer(
        bootstrap_servers=['kafka:9092']
    )

    print("Producer started")

    predictor = MultiPairPredictor(target_pairs, producer)
    sentiment_pipeline = pipeline(model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
    gold_price_predictor = GoldPriceModel()
    entities = ['amazon', 'tesla', 'bitcoin']
    investing_model = InvestingModel(entities)
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

            elif topic.topic == 'kaggle_gold_silver':
                for message in messages:
                    if has_null_bytes(message.value):
                        continue
                    message = message.value.decode('utf-8')

                    csv_reader = csv.reader(StringIO(message))
                    next(csv_reader)  # Skip header
                    
                    row = next(csv_reader)
                    message_data = {
                        'date': row[0],
                        'time': row[1],
                        'open': row[2],
                        'high': row[3],
                        'low': row[4],
                        'close': row[5],
                        'volume': row[6]
                    }
                    prediction = gold_price_predictor.predict_price(message_data)
                    date_str = f"{message_data['date']} {message_data['time']}"
                    date_str = datetime.datetime.strptime(date_str, "%Y.%m.%d %H:%M") + datetime.timedelta(hours=1)
                    output_date = date_str.strftime("%Y-%m-%dT%H:%M:%S")
                    producer.send(
                        'kaggle_gold_predictions', 
                        value=f"{output_date},{prediction}".encode('utf-8')
                        )
            elif topic.topic == 'investingcom_silver':
                for message in messages:
                    if has_null_bytes(message.value):
                        continue
                    message = message.value.decode('utf-8')

                    csv_reader = csv.reader(StringIO(message))
                    next(csv_reader)  # Skip header

                    row = next(csv_reader)
                    message_data = {
                        'date': row[0],
                        'open': row[2].replace(',', ''),
                        'high': row[3].replace(',', ''),
                        'low': row[4].replace(',', ''),
                        'volume': row[5].replace(',', '').replace('K', '').replace('M', '')
                    }
                    entity = row[7].lower().replace('.com', '')
                    if entity not in entities:
                        print(f"Entity {entity} not supported")
                        continue
                    prediction = investing_model.predict_price(message_data, entity)
                    date_str = f"{message_data['date']}"
                    date_str = datetime.datetime.strptime(date_str, "%m/%d/%Y") + datetime.timedelta(days=1)
                    output_date = date_str.strftime("%Y-%m-%dT%H:%M:%S")
                    producer.send(
                        'investingcom_predictions', 
                        value=f"{output_date},{entity},{prediction}".encode('utf-8')
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
