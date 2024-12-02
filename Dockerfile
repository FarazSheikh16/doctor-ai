FROM python:3.12-slim AS base

# Install system dependencies including cmake and C++ compiler needed for LlamaCpp
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create models directory
RUN mkdir -p /app/models

COPY . /app

CMD uvicorn api:app --host 0.0.0.0 --port 8000 --reload & streamlit run app.py --server.port 8501 --server.address 0.0.0.0