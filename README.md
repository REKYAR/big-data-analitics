# Big Data Analytics

Course project at Warsaw Univeristy of Technology


# Development docs

## Setup
- download stuff to run docker with (most likely wsl2)
- download docker compose
- run pipeline by configuring Nifi (below) and then calling ```docker-compose -f dockerCompose.yaml up```, to terminate ```docker-compose -f dockerCompose.yaml down ```

## Nifi
- [Docs are here](nifi/README.md) 

## Kafka
- When running if you want to read a message in terminal go to Exec tab in docker compose and execute ``` opt/kafka/bin/kafka-console-consumer.sh --topic $TOPIC_NAME --bootstrap-server kafka:9092 ```

## Clickhouse
- To run queries go to Exec tab in docker compose and execute ``` cickhouse-client ``` command, clichkouse terminal shall appear
- Execute ```USE BigDataAnalytics; SHOW TABLES;``` to see available tables in our project, note that the tables that directly ingest kafka are locked from reading, refer to their *_consumalbe version

Fo troubleshooting cat server log files to cionsole and copy past into normal text editor, bot error and nonerror log files are useful for the purpose.