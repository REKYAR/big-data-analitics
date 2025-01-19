# Big Data Analytics

Course project at Warsaw Univeristy of Technology


# Development docs

## Setup
- download stuff to run docker with (most likely wsl2)
- download docker compose
- if any changes have been made to code in [the ML related section](stream_ml) (or before the first execution), ```docker-compose -f dockerCompose.yaml build``` has to be run
- run pipeline by configuring Nifi (below) and then calling ```docker-compose -f dockerCompose.yaml up```, to terminate ```docker-compose -f dockerCompose.yaml down ```

## Nifi
- [Docs are here](nifi/README.md) 

## Kafka
- When running if you want to read a message in terminal go to Exec tab in docker compose and execute ``` opt/kafka/bin/kafka-console-consumer.sh --topic $TOPIC_NAME --bootstrap-server kafka:9092 ```

## Clickhouse
- To run queries go to Exec tab in docker compose and execute ``` cickhouse-client ``` command, clichkouse terminal shall appear
- Execute ```USE BigDataAnalytics; SHOW TABLES;``` to see available tables in our project, note that the tables that directly ingest kafka are locked from reading, refer to their *_consumalbe version

## Grafana
- Visit https://localhost:3000
- Use credentials from the `dockerCompose.yaml` file to authenticate
- Click 'Dashboards' on the left panel to see the list of available dashboards

Fo troubleshooting cat server log files to cionsole and copy past into normal text editor, bot error and nonerror log files are useful for the purpose.
