FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./stream_ml /code/stream_ml

EXPOSE 5000

# CMD ["uvicorn", "query_api.main:app", "--host", "0.0.0.0", "--port", "80", "&&", "python", "query_api.simulate_request.py" uvicorn query_api.main:app --host 0.0.0.0 --port 80 && ]
CMD ["bash", "-c", "python3 stream_ml/ml.py"]