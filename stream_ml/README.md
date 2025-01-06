# ML

In this directory, files related to machine learning processes are stored, both actually executed during the application execution and those used to prepare the final pipeline.

## stream_ml

This is the main directory, used during the execution of the application. **ml.py** is the file executed by Docker and it imports classes from *predictor.py* (used for Alpaca data), *gold_price_utils.py* and  *investingcom_utils.py*. *Models* contains pickled models and scalers used for Kaggle Gold and investing.com data. 

## Dockerfile

This is the dockerfile used by Docker to build the container. *requirements.txt* is the requirements file used there as well.