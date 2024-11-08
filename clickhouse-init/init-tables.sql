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


--alpaca bronze