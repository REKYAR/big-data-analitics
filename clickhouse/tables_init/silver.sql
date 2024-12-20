CREATE DATABASE IF NOT EXISTS BigDataAnalytics;
USE BigDataAnalytics;




---------------- Alpaca silver ----------------------

-- Clean up existing objects

DROP VIEW IF EXISTS feed_consumer_alpaca_silver;
DROP TABLE IF EXISTS alpaca_silver_raw_data;
DROP TABLE IF EXISTS alpaca_silver_consumable;

-- Create Kafka source table for silver (CSV) data
CREATE TABLE IF NOT EXISTS alpaca_silver_raw_data (
    symbol String,
    timestamp String,
    -- Additional columns for all possible crypto pairs
    `AAVE/USD` Nullable(Float64),
    `SHIB/USD` Nullable(Float64),
    `BCH/USD` Nullable(Float64),
    `BTC/USD` Nullable(Float64),
    `DOT/USD` Nullable(Float64),
    `USDC/USD` Nullable(Float64),
    `SUSHI/USD` Nullable(Float64),
    `BAT/USD` Nullable(Float64),
    `LTC/USD` Nullable(Float64),
    `YFI/USD` Nullable(Float64),
    `MKR/USD` Nullable(Float64),
    `USDT/USD` Nullable(Float64),
    `CRV/USD` Nullable(Float64),
    `DOGE/USD` Nullable(Float64),
    `ETH/USD` Nullable(Float64),
    `GRT/USD` Nullable(Float64),
    `LINK/USD` Nullable(Float64),
    `AVAX/USD` Nullable(Float64),
    `UNI/USD` Nullable(Float64),
    `XTZ/USD` Nullable(Float64)
) ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'alpaca_silver',
    kafka_group_name = 'alpaca_silver_clickhouse_group',
    kafka_format = 'CSV',
    kafka_row_delimiter = '\n',
    kafka_skip_broken_messages = 1,
    kafka_num_consumers = 1;

-- Create target table for silver processed data
CREATE TABLE IF NOT EXISTS alpaca_silver_consumable (
    symbol String,
    price Float64,
    timestamp DateTime('UTC'),
    update_time DateTime('UTC') DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (symbol, timestamp);

-- Create materialized view to transform silver data
CREATE MATERIALIZED VIEW IF NOT EXISTS feed_consumer_alpaca_silver 
TO alpaca_silver_consumable AS
SELECT 
    pair.1 AS symbol,
    pair.2 AS price,
    parseDateTimeBestEffort(base.timestamp) as timestamp
FROM 
(
    SELECT
        timestamp,
        arrayJoin([
            ('AAVE/USD', nullIf(`AAVE/USD`, 0)),
            ('SHIB/USD', nullIf(`SHIB/USD`, 0)),
            ('BCH/USD', nullIf(`BCH/USD`, 0)),
            ('BTC/USD', nullIf(`BTC/USD`, 0)),
            ('DOT/USD', nullIf(`DOT/USD`, 0)),
            ('USDC/USD', nullIf(`USDC/USD`, 0)),
            ('SUSHI/USD', nullIf(`SUSHI/USD`, 0)),
            ('BAT/USD', nullIf(`BAT/USD`, 0)),
            ('LTC/USD', nullIf(`LTC/USD`, 0)),
            ('YFI/USD', nullIf(`YFI/USD`, 0)),
            ('MKR/USD', nullIf(`MKR/USD`, 0)),
            ('USDT/USD', nullIf(`USDT/USD`, 0)),
            ('CRV/USD', nullIf(`CRV/USD`, 0)),
            ('DOGE/USD', nullIf(`DOGE/USD`, 0)),
            ('ETH/USD', nullIf(`ETH/USD`, 0)),
            ('GRT/USD', nullIf(`GRT/USD`, 0)),
            ('LINK/USD', nullIf(`LINK/USD`, 0)),
            ('AVAX/USD', nullIf(`AVAX/USD`, 0)),
            ('UNI/USD', nullIf(`UNI/USD`, 0)),
            ('XTZ/USD', nullIf(`XTZ/USD`, 0))
        ]) AS pair
    FROM alpaca_silver_raw_data
) AS base
WHERE pair.2 IS NOT NULL;




------------------ MarketWatch silver -----------------

drop VIEW if exists feed_consumeer_marketwatch_silver;
drop TABLE if exists marketwatch_silver_raw_data;
drop TABLE if exists marketwatch_silver_consumable;

CREATE TABLE IF NOT EXISTS marketwatch_silver_raw_data (
    id String,
    feedTitle String,
    title String,
    description String,
    date String
) ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:9092',            -- replace with your Kafka broker list
    kafka_topic_list = 'marketwatch_silver',           -- replace with your topic
    kafka_group_name = 'marketwatch_clickhouse_group',
    kafka_format = 'CSV',
    kafka_row_delimiter = '\n',
    kafka_num_consumers = 1;

CREATE TABLE IF NOT EXISTS marketwatch_silver_consumable (
    id String,
    feedTitle String,
    title String,
    description String,
    date DateTime('UTC')  -- Assuming the incoming date is UTC
) ENGINE = MergeTree()
ORDER BY id;

CREATE MATERIALIZED VIEW IF NOT EXISTS feed_consumeer_marketwatch_silver TO marketwatch_silver_consumable
AS
SELECT
    id,
    feedTitle,
    title,
    description,
    parseDateTimeBestEffort(date) AS date
FROM marketwatch_silver_raw_data;




---------------- Investingcom silver ------------

-- Drop existing views and tables

DROP VIEW IF EXISTS feed_consumer_investingcom_silver;
DROP TABLE IF EXISTS investingcom_silver_raw_data;
DROP TABLE IF EXISTS investingcom_silver_consumable;

-- Create raw data table connected to Kafka
CREATE TABLE IF NOT EXISTS investingcom_silver_raw_data (
    Date String,
    Price String,
    Open String,
    High String,
    Low String,
    `Vol.` String,
    `Change %` String,
    entity String
) ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'investingcom_silver',
    kafka_group_name = 'investingcom_clickhouse_group',
    kafka_format = 'CSVWithNames',
    kafka_row_delimiter = '\n',
    kafka_skip_broken_messages = 100,
    kafka_num_consumers = 1;

-- Create target table for processed data with proper types
CREATE TABLE IF NOT EXISTS investingcom_silver_consumable (
    Date Date,
    Price Float64,
    Open Float64,
    High Float64,
    Low Float64,
    Volume Float64,
    ChangePercent Float64,
    entity String
) ENGINE = MergeTree()
ORDER BY (Date, entity);

-- Create materialized view with type casting
CREATE MATERIALIZED VIEW IF NOT EXISTS feed_consumer_investingcom_silver 
TO investingcom_silver_consumable AS
SELECT
    parseDateTimeBestEffort(Date) AS Date,
    toFloat64OrNull(replaceRegexpAll(Price, ',', '')) AS Price,
    toFloat64OrNull(replaceRegexpAll(Open, ',', '')) AS Open,
    toFloat64OrNull(replaceRegexpAll(High, ',', '')) AS High,
    toFloat64OrNull(replaceRegexpAll(Low, ',', '')) AS Low,
    -- Handle volume with K/M suffixes
    toFloat64OrNull(replaceRegexpAll(
        replaceRegexpAll(`Vol.`, '[KMB]', ''),
        ',', ''
    )) * 
    CASE
        WHEN endsWith(`Vol.`, 'K') THEN 1000
        WHEN endsWith(`Vol.`, 'M') THEN 1000000
        WHEN endsWith(`Vol.`, 'B') THEN 1000000000
        ELSE 1
    END AS Volume,
    -- Remove % and convert to float
    toFloat64OrNull(replaceRegexpAll(`Change %`, '%', '')) AS ChangePercent,
    entity
FROM investingcom_silver_raw_data;




----------------- Kaggle gold silver -----------------------

-- Drop existing views and tables

DROP VIEW IF EXISTS feed_consumer_kaggle_gold_silver;
DROP TABLE IF EXISTS kaggle_gold_silver_raw_data;
DROP TABLE IF EXISTS kaggle_gold_silver_consumable;

-- Create raw data table connected to Kafka for Gold Silver
CREATE TABLE IF NOT EXISTS kaggle_gold_silver_raw_data (
    Date String,
    Time String,
    Open String,
    High String,
    Low String,
    Close String,
    Volume String
) ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'kaggle_gold_silver',
    kafka_group_name = 'kaggle_gold_silver_group',
    kafka_format = 'CSVWithNames',
    kafka_row_delimiter = '\n',
    kafka_skip_broken_messages = 100,
    kafka_num_consumers = 1;

-- Create target table for processed Gold Silver data
CREATE TABLE IF NOT EXISTS kaggle_gold_silver_consumable (
    DateTime DateTime,
    Open Float64,
    High Float64,
    Low Float64,
    Close Float64,
    Volume Float64
) ENGINE = MergeTree()
ORDER BY DateTime;

-- Create materialized view for Gold Silver with type casting
CREATE MATERIALIZED VIEW IF NOT EXISTS feed_consumer_kaggle_gold_silver 
TO kaggle_gold_silver_consumable AS
SELECT
    parseDateTimeBestEffort(concat(Date, ' ', Time)) AS DateTime,
    toFloat64OrNull(Open) AS Open,
    toFloat64OrNull(High) AS High,
    toFloat64OrNull(Low) AS Low,
    toFloat64OrNull(Close) AS Close,
    toFloat64OrNull(Volume) AS Volume
FROM kaggle_gold_silver_raw_data;
