CREATE DATABASE IF NOT EXISTS BigDataAnalytics;
USE BigDataAnalytics;
-- SELECT sleep(3);
-- SELECT sleep(3);
-- SELECT sleep(3);




-- marketwatch sivler
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


--marketwatch bronze
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
    kafka_format = 'JSONAsString';


CREATE TABLE IF NOT EXISTS marketwatch_bronze_consumable
(
    channel_title String,
    article_title String,
    description Nullable(String),
    link String,
    pub_date DateTime,
    author Nullable(String),
    content_type Nullable(String),
    content_url Nullable(String),
    content_credit Nullable(String),
    raw_data String,
    processed_time DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (channel_title, pub_date);

-- Create materialized view to parse and transform data
CREATE MATERIALIZED VIEW IF NOT EXISTS feed_consumer_marketwatch_bronze 
TO marketwatch_bronze_consumable AS
SELECT
    JSONExtractString(raw_data, 'channel', 'title') as channel_title,
    JSONExtractString(item, 'title') as article_title,
    JSONExtractString(item, 'description') as description,
    JSONExtractString(item, 'link') as link,
    parseDateTimeBestEffort(JSONExtractString(item, 'pubDate')) as pub_date,
    JSONExtractString(item, 'author') as author,
    JSONExtractString(JSONExtractString(item, 'content'), 'type') as content_type,
    JSONExtractString(JSONExtractString(item, 'content'), 'url') as content_url,
    JSONExtractString(JSONExtractString(item, 'content'), 'credit') as content_credit,
    raw_data,
    now() as processed_time
FROM marketwatch_bronze_raw_data
ARRAY JOIN JSONExtractArrayRaw(raw_data, 'channel', 'item') AS item
WHERE length(raw_data) > 2;


-- investingcom silver
-- Drop existing views and tables
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

--alpaca bronze

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


-- Clean up existing objects
DROP VIEW IF EXISTS feed_consumer_alpaca_bronze;
DROP TABLE IF EXISTS alpaca_bronze_raw_data;
DROP TABLE IF EXISTS alpaca_bronze_consumable;

-- Create Kafka source table for bronze (JSON) data
CREATE TABLE IF NOT EXISTS alpaca_bronze_raw_data (
    bars String
) ENGINE = Kafka()
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'alpaca_bronze',
    kafka_group_name = 'alpaca_bronze_clickhouse_group',
    kafka_format = 'JSONAsString',
    kafka_row_delimiter = '\n',
    kafka_skip_broken_messages = 1,
    kafka_num_consumers = 1;

-- Create target table for bronze processed data
CREATE TABLE IF NOT EXISTS alpaca_bronze_consumable (
    symbol String,
    timestamp DateTime('UTC'),
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume Float64,
    number_of_trades Int32,
    vwap Float64,
    update_time DateTime('UTC') DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (symbol, timestamp);

-- Create materialized view to transform bronze data
CREATE MATERIALIZED VIEW IF NOT EXISTS feed_consumer_alpaca_bronze 
TO alpaca_bronze_consumable AS
SELECT
    symbol_data.1 AS symbol,
    parseDateTimeBestEffort(JSONExtractString(symbol_data.2, 't')) AS timestamp,
    JSONExtractFloat(symbol_data.2, 'o') AS open,
    JSONExtractFloat(symbol_data.2, 'h') AS high,
    JSONExtractFloat(symbol_data.2, 'l') AS low,
    JSONExtractFloat(symbol_data.2, 'c') AS close,
    coalesce(JSONExtractFloat(symbol_data.2, 'v'), 0) AS volume,
    coalesce(JSONExtractInt(symbol_data.2, 'n'), 0) AS number_of_trades,
    coalesce(JSONExtractFloat(symbol_data.2, 'vw'), 0) AS vwap
FROM 
(
    SELECT
        arrayJoin(JSONExtractKeysAndValues(
            JSONExtractString(bars, 'bars'),
            'String'  -- Specify the key type
        )) AS symbol_data
    FROM alpaca_bronze_raw_data
    WHERE JSONHas(bars, 'bars') = 1
)
WHERE JSONLength(symbol_data.2) > 0;