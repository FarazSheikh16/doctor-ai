FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

CMD uvicorn api:app --host 0.0.0.0 --port 8000 --reload & streamlit run app.py --server.port 8501 --server.address 0.0.0.0
