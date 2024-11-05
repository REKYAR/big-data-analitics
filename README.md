# Big Data Analytics

Course project at Warsaw Univeristy of Technology


# clickhouse troubleshooting
what we want to do https://clickhouse.com/docs/en/integrations/kafka/kafka-table-engine
run pipeline
go to clickhouse container cat the error log file and inspect - I noticed the issue with connection to kafka
somethin may be wrong with the init script and you need to manuall remove container data (trashcan button in docker desktop ui) in order to reload new config