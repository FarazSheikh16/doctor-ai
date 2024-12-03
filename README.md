# MedBot 🏥

## Overview

MedBot is an intelligent medical chatbot designed to provide guidance related to cancer diagnosis and treatment. It helps users by:
- Analyzing symptoms and suggesting possible cancer types
- Providing information about relevant cancer
- Offering preventive measures and precautionary guidelines

## Table of Contents
- [Dataset](#dataset)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Command Line Interface](#command-line-interface)
- [Contributing](#contributing)


## Dataset
The knowledge base is constructed from curated Wikipedia articles related to cancer, ensuring reliable and up-to-date medical information. The data extraction process focuses on Cancer types and symptoms

## Prerequisites
- Python 3.12.7
- Qdrant vector database
- Ollama (for LLM support)

## Installation

### 1. Set Up Development Environment
```bash
# Create and activate Conda environment
conda create -n medbot python=3.12.7
conda activate medbot

# Clone the repository
git clone https://github.com/FarazSheikh16/doctor-ai.git
cd ai_doctor

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Qdrant
Follow the [Qdrant Quickstart Guide](https://qdrant.tech/documentation/quickstart/) for database setup and configuration.

### 3. Set Up Ollama (Required for Generation)
```bash
ollama pull llama3.2
ollama run llama3.2
```

## Configuration
Ensure all necessary environment variables and configurations are set before running the application.

## Usage

### Starting the Application

1. Launch the API server:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

2. Start the Streamlit interface:
```bash
streamlit run app.py
```

## Command Line Interface

MedBot provides several CLI commands for different functionalities:

### Data Ingestion
Process and store new medical data:
```bash
python main.py --ingest
```

### Search Functionality
Query the medical knowledge base:
```bash
python main.py --search "your search query"
```

### Interactive Mode
Start an interactive session with the bot:
```bash
python main.py --interactive
```

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.


## Disclaimer
MedBot is designed to provide general medical information and should not be used as a substitute for professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare providers for medical decisions.