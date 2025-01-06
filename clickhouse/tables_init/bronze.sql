CREATE DATABASE IF NOT EXISTS BigDataAnalytics;
USE BigDataAnalytics;




-- ------------ Alpaca bronze --------------

-- -- Clean up existing objects

DROP VIEW IF EXISTS feed_consumer_alpaca_bronze;
DROP TABLE IF EXISTS alpaca_bronze_raw_data;
DROP TABLE IF EXISTS alpaca_bronze_consumable;

-- Create Kafka source table for bronze (JSON) data
CREATE TABLE IF NOT EXISTS alpaca_bronze_raw_data (
    raw_data String
) ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'alpaca_bronze',
    kafka_group_name = 'alpaca_bronze_clickhouse_group',
    kafka_format = 'LineAsString',
    kafka_row_delimiter = '\n',
    kafka_skip_broken_messages = 1,
    kafka_num_consumers = 1;

-- Create target table for bronze processed data
CREATE TABLE IF NOT EXISTS alpaca_bronze_consumable (
    raw_data String,
    processed_time DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (processed_time);

-- Create materialized view to transform bronze data
CREATE MATERIALIZED VIEW IF NOT EXISTS feed_consumer_alpaca_bronze 
TO alpaca_bronze_consumable AS
SELECT
    raw_data,
    now() as processed_time
FROM alpaca_bronze_raw_data;




--------------- MarketWatch bronze -----------------

DROP VIEW IF EXISTS feed_consumer_marketwatch_bronze;
DROP TABLE IF EXISTS marketwatch_bronze_raw_data;
DROP TABLE IF EXISTS marketwatch_bronze_consumable;

CREATE TABLE IF NOT EXISTS marketwatch_bronze_raw_data
(
    raw_data String
) ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'marketwatch_bronze',
    kafka_group_name = 'marketwatch_clickhouse_group',
    kafka_format = 'LineAsString',
    kafka_row_delimiter = '\n',
    kafka_skip_broken_messages = 1,
    kafka_num_consumers = 1;


CREATE TABLE IF NOT EXISTS marketwatch_bronze_consumable
(
    raw_data String,
    processed_time DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (processed_time);

-- Create materialized view to parse and transform data
CREATE MATERIALIZED VIEW IF NOT EXISTS feed_consumer_marketwatch_bronze 
TO marketwatch_bronze_consumable AS
SELECT
    raw_data,
    now() as processed_time
FROM marketwatch_bronze_raw_data;




--------------- Investingcom bronze ----------------

DROP VIEW IF EXISTS feed_consumer_investingcom_bronze;
DROP TABLE IF EXISTS investingcom_bronze_raw_data;
DROP TABLE IF EXISTS investingcom_bronze_consumable;


CREATE TABLE IF NOT EXISTS investingcom_bronze_raw_data
(
    raw_data String
) ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'investingcom_bronze',
    kafka_group_name = 'investingcom_clickhouse_group',
    kafka_format = 'LineAsString',
    kafka_row_delimiter = '\n',
    kafka_skip_broken_messages = 1,
    kafka_num_consumers = 1;


CREATE TABLE IF NOT EXISTS investingcom_bronze_consumable
(
    raw_data String,
    processed_time DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (processed_time);

-- Create materialized view to parse and transform data
CREATE MATERIALIZED VIEW IF NOT EXISTS feed_consumer_investingcom_bronze 
TO investingcom_bronze_consumable AS
SELECT
    raw_data,
    now() as processed_time
FROM investingcom_bronze_raw_data;




-------------- Kaggle gold bronze ----------------

-- Drop existing views and tables

DROP VIEW IF EXISTS feed_consumer_kaggle_gold_bronze;
DROP TABLE IF EXISTS kaggle_gold_bronze_raw_data;
DROP TABLE IF EXISTS kaggle_gold_bronze_consumable;

-- Create raw data table connected to Kafka for Gold Bronze
CREATE TABLE IF NOT EXISTS kaggle_gold_bronze_raw_data (
    raw_data String
) ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'kaggle_gold_bronze',
    kafka_group_name = 'kaggle_gold_bronze_group',
    kafka_format = 'LineAsString',
    kafka_row_delimiter = '\n',
    kafka_skip_broken_messages = 1,
    kafka_num_consumers = 1;

-- Create target table for processed Gold Bronze data
CREATE TABLE IF NOT EXISTS kaggle_gold_bronze_consumable (
    raw_data String,
    processed_time DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (processed_time);

-- Create materialized view for Gold Bronze with type casting
CREATE MATERIALIZED VIEW IF NOT EXISTS feed_consumer_kaggle_gold_bronze 
TO kaggle_gold_bronze_consumable AS
SELECT
    raw_data,
    now() as processed_time
FROM kaggle_gold_bronze_raw_data;
