CREATE DATABASE IF NOT EXISTS BigDataAnalytics;
USE BigDataAnalytics;

drop VIEW if exists feed_consumeer_marketwatch_silver;
drop TABLE if exists marketwatch_silver_raw_data;
drop TABLE if exists marketwatch_silver_consumable;

-- marketwatch sivler
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