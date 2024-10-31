CREATE TABLE IF NOT EXISTS marketwatch_headlines
(
    timestamp DateTime,
    headline String,
    author String,
    guid String
)
ENGINE = MergeTree()
ORDER BY timestamp;

CREATE TABLE IF NOT EXISTS kafka_marketwatch_feed
(
    timestamp DateTime,
    headline String,
    author String,
    guid String
)
ENGINE = Kafka
SETTINGS kafka_broker_list = 'kafka:9092',
         kafka_topic_list = 'marketwatch_headlines',
         kafka_group_name = 'clickhouse_marketwatch_group',
         kafka_format = 'JSONEachRow';

CREATE MATERIALIZED VIEW IF NOT EXISTS kafka_marketwatch_consumer TO marketwatch_headlines
AS SELECT * FROM kafka_marketwatch_feed;