# NiFi

In this directory there are placed templates for NiFi flows for each data source.
This file summarises the most important information related to them.

## Input data

Data files which should be manually placed:
- investing.com: place in `./nifi/volumes/BIG_DATA/investingcom/`
- Kaggle's gold data: place in `./nifi/volumes/BIG_DATA/gold/`

The rest of the data is fetched inside NiFi.

## How to run the flow

To access NiFi, visit `http://localhost:8443/nifi` in a browser. 

**Note:** it is important that `http` is used, and not `https`, otherwise it will not work. The browser may warn of an unsafe connection, but this warning can be dismissed.

Steps 1-3 are needed to be performed only when running the flow for the first time, or if the templates are updated.

1. Import each template to NiFi. On the left-hand side, there is an "Operate" panel, and the button to upload templates is the last button in the first row of buttons;
2. Add each template to the flow by dragging the template icon from the top bar onto the canvas (second-to-last icon); 
3. Make sure that all controllers are running:
   - In the "Operate" panel, click on the settings icon. A window will show up;
   - In the top bar, navigate to "Controller services";
   - Make sure that the "XMLRecordSetWriter" controller has "Name of Record Tag" property set to rss. If not, set it;
   - For each controller, press the lightning icon on the right-hand side to start it (if it is running, the icon will show a crossed-out lightning and there will be no delete icon);
   - Once all controllers are running you can close the settings window;
4. At this point there should be no more warnings (triangular exclamation mark icons on the processors); If there are any then abort and consult it with the team;
5. Place the necessary input files in their specified directories (see "Input data" section above);
6. Press CTRL+A to select all processors, and click the start button in the "Operate" panel.

## Processors colours guide

- **Banana:** reading stream data
- **Lavender:** reading batch data
- **Bronze:** publishing bronze to Kafka
- **Silver:** publishing silver to Kafka

## Kafka topics

Broker is expected to be on `kafka:9092`.
For bronze topics, data is published in the original format. For silver topics, it is always converted to CSV.

### Alpaca Markets data

**Bronze topic:** `alpaca_bronze`

**Silver topic:** `alpaca_silver`

### MarketWatch data

**Note:** MarketWatch offers access to RSS channels. However, it is impossile to listen to RSS using NiFi, 
so instead regular HTTP requests are made every 10 seconds to quickly detect any new data. However,
this means that most data arriving in the topics is duplicate, so in the case of a silver topic,
it is key for consumers to handle duplicate IDs across separate messages.

**Bronze topic:** `marketwatch_bronze`

**Silver topic:** `marketwatch_silver`

### investing.com data

**Bronze topics:**`investingcom_bronze`

**Silver topic:** `investingcom_silver`

### Gold prices data

**Bronze topic:** `kaggle_gold_bronze`

**Silver topic:** `kaggle_gold_silver`
