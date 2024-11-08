# Big Data Analytics

Course project at Warsaw Univeristy of Technology


# Development docs

## Setup

## Nifi
- [Docs are here](nifi/README.md) 

## Kafka
- When running if you want to read a message in terminal go to Exec tab in docker compose and execute ``` opt/kafka/bin/kafka-console-consumer.sh --topic $TOPIC_NAME --bootstrap-server kafka:9092 ```

## Clickhouse
- To run queries go to Exec tab in docker compose and execute ``` cickhouse-client ``` command, clichkouse terminal shall appear
- Execute ```USE BigDataAnalytics; SHOW TABLES;``` to see available tables in our project, note that the tables that directly ingest kafka are locked from reading, refer to their *_consumalbe version