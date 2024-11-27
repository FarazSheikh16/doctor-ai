# Use Python 3.12 slim as base image
FROM python:3.12-slim AS base

# Install required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory in container
WORKDIR /app

# Copy the requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the project files
COPY . /app

# Expose the ports for FastAPI and Streamlit
EXPOSE 8000 8501

# Run both services using bash
CMD bash -c "uvicorn api:app --host 0.0.0.0 --port 8000 --reload & streamlit run app.py --server.port 8501 --server.address 0.0.0.0"