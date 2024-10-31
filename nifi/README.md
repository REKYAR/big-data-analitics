# NiFi

In this directory there are placed templates for NiFi flows for each data source.
This file summarises the most important information related to them.

## Secrets

The following environment variables need to be set up:
- `ALPACA_API_KEY`
- `FREECURRENCY_API_KEY`

## Processors colours guide

- **Banana:** reading stream data
- **Lavender:** reading batch data
- **Bronze:** publishing bronze to Kafka
- **Silver:** publishing silver to Kafka
- **Red:** handling failures

## Input data

Data files which should be manually placed:
- investing.com: place in `~/data/investingcom/`
- Kaggle's gold data: place in `~/data/gold/`

The rest of the data is fetched inside NiFi.

## Failures

All bronze data that fails to be published to Kafka is saved to `~/data/_failures/` folder.

## Kafka topics

Broker is expected to be on `localhost:9092`.
For bronze topics, data is published in the original format. For silver topics, it is always converted to CSV.

**Note:** Setup script for Kafka is placed in: `kafka/topics_init.sh`

### MarketWatch data

**Note:** MarketWatch offers access to RSS channels. However, it is impossile to listen to RSS using NiFi, 
so instead regular HTTP requests are made every 10 seconds to quickly detect any new data. However,
this means that most data arriving in the topics is duplicate, so in the case of a silver topic,
it is key for consumers to handle duplicate IDs across separate messages.

**Bronze topic:** `marketwatch_bronze`

**Silver topic:** `marketwatch_silver`

### FreeCurrencyAPI data

**Bronze topic:** `freecurrencyapi_bronze`

**Silver topic:** `freecurrencyapi_silver`

### investing.com data

**Bronze topics:**
- `investingcom_bitcoin_bronze`
- `investingcom_tsla_bronze`
- `investingcom_amzn_bronze`

**Silver topic:** `investingcom_silver`

### Gold prices data

**Bronze topic:** `kaggle_gold_bronze`

**Silver topic:** `kaggle_gold_silver`
