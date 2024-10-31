#!/bin/bash
cd /usr/local/kafka

TOPICS=(
  # MarketWatch
  "marketwatch_bronze"
  "marketwatch_silver"
  # FreeCurrencyAPI
  "freecurrencyapi_bronze"
  "freecurrencyapi_silver"
  # Historical crypto/stock from investing.com
  "investingcom_bitcoin_bronze"
  "investingcom_tsla_bronze"
  "investingcom_amzn_bronze"
  "investingcom_silver"
  # Gold data
  "kaggle_gold_bronze"
  "kaggle_gold_silver"
)

for TOPIC_NAME in "${TOPICS[@]}"; do
  bin/kafka-topics.sh --create \
	--topic "$TOPIC_NAME" \
	--bootstrap-server localhost:9092 \
	--replication-factor 1 \
	--partitions 1
done

