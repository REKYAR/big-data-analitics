from kafka import KafkaConsumer, KafkaProducer, errors
from river import neighbors, evaluate, metrics
from predictor import MultiPairPredictor
from typing import List
from transformers import pipeline
from io import StringIO
from email.utils import parsedate_to_datetime
from gold_price_utils import GoldPriceModel
from investingcom_utils import InvestingModel
from threading import Thread
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

def run_alpaca_predictor(predictor, producer, target_pairs):
    while True:
        try:
            consumer = KafkaConsumer(
                bootstrap_servers=['kafka:9092'],
                group_id='alpaca_predictor_group',
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            logging.info("Successfully connected to Kafka (alpaca)")
            break
        except errors.NoBrokersAvailable as e:
            logging.error(f"Failed to connect to Kafka: {e}")
            time.sleep(10)

    consumer.subscribe(['alpaca_silver'])
    print("Consumer (alpaca) connected.")

    metrics_id = 1
    last_update_per_pair = {pair: datetime.date.min for pair in target_pairs}

    for message in consumer:
        if has_null_bytes(message.value):
            continue
        message = message.value.decode('utf-8')

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

def run_marketwatch_predictor(sentiment_pipeline, producer):
    while True:
        try:
            consumer = KafkaConsumer(
                bootstrap_servers=['kafka:9092'],
                group_id='marketwatch_predictor_group',
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            logging.info("Successfully connected to Kafka (marketwatch)")
            break
        except errors.NoBrokersAvailable as e:
            logging.error(f"Failed to connect to Kafka: {e}")
            time.sleep(10)

    consumer.subscribe(['marketwatch_silver'])
    print("Consumer (marketwatch) connected.")

    for message in consumer:
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

def run_gold_predictor(predictor, producer):
    while True:
        try:
            consumer = KafkaConsumer(
                bootstrap_servers=['kafka:9092'],
                group_id='gold_predictor_group',
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            logging.info("Successfully connected to Kafka (gold)")
            break
        except errors.NoBrokersAvailable as e:
            logging.error(f"Failed to connect to Kafka: {e}")
            time.sleep(10)

    consumer.subscribe(['kaggle_gold_silver'])
    print("Consumer (gold) connected.")

    for message in consumer:
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
        prediction = predictor.predict_price(message_data)
        date_str = f"{message_data['date']} {message_data['time']}"
        date_str = datetime.datetime.strptime(date_str, "%Y.%m.%d %H:%M") + datetime.timedelta(hours=1)
        output_date = date_str.strftime("%Y-%m-%dT%H:%M:%S")
        producer.send(
            'kaggle_gold_predictions', 
            value=f"{output_date},{prediction}".encode('utf-8')
            )

def run_investing_predictor(predictor, producer, entities):
    def change_KMB_to_numeric(value):
        if value[-1] == 'K':
            return float(value[:-1]) * 1e3
        elif value[-1] == 'M':
            return float(value[:-1]) * 1e6
        elif value[-1] == 'B':
            return float(value[:-1]) * 1e9
        else:
            return float(value)

    while True:
        try:
            consumer = KafkaConsumer(
                bootstrap_servers=['kafka:9092'],
                group_id='gold_predictor_group',
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            logging.info("Successfully connected to Kafka (gold)")
            break
        except errors.NoBrokersAvailable as e:
            logging.error(f"Failed to connect to Kafka: {e}")
            time.sleep(10)

    consumer.subscribe(['investingcom_silver'])
    print("Consumer (investingcom) connected.")

    for message in consumer:
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
            'volume': change_KMB_to_numeric(row[5])
        }
        entity = row[7].lower().replace('.com', '')
        if entity not in entities:
            print(f"Entity {entity} not supported")
            continue
        prediction = predictor.predict_price(message_data, entity)
        date_str = f"{message_data['date']}"
        date_str = datetime.datetime.strptime(date_str, "%m/%d/%Y") + datetime.timedelta(days=1)
        output_date = date_str.strftime("%Y-%m-%dT%H:%M:%S")
        producer.send(
            'investingcom_predictions', 
            value=f"{output_date},{entity},{prediction}".encode('utf-8')
            )

if __name__ == "__main__":
    target_pairs = ['BTC/USD', 'ETH/USD', 'DOGE/USD']
    
    producer = KafkaProducer(
        bootstrap_servers=['kafka:9092']
    )

    print("Producer started")

    predictor = MultiPairPredictor(target_pairs, producer)
    sentiment_pipeline = pipeline(model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
    gold_price_predictor = GoldPriceModel()
    entities = ['amazon', 'tesla', 'bitcoin']
    investing_model = InvestingModel(entities)

    threads = []

    thread_alpaca = Thread(
        target=run_alpaca_predictor,
        args=(predictor, producer, target_pairs),
        name="thread_alpaca"
    )
    threads.append(thread_alpaca)

    thread_marketwatch = Thread(
        target=run_marketwatch_predictor,
        args=(sentiment_pipeline, producer),
        name="thread_marketwatch"
    )
    threads.append(thread_marketwatch)

    thread_gold = Thread(
        target=run_gold_predictor,
        args=(gold_price_predictor, producer),
        name="thread_gold"
    )
    threads.append(thread_gold)

    thread_investing = Thread(
        target=run_investing_predictor,
        args=(investing_model, producer, entities),
        name="thread_investing"
    )
    threads.append(thread_investing)

    for thread in threads:
        thread.daemon = True
        thread.start()
        print(f"Thread {thread.name} started")

    while True:
        time.sleep(1)

