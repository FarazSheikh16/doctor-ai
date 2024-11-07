# MedBot

## Overview

MedBot is a medical chatbot which will help you in medical related things like telling you if you have any symptoms, it will tell you the dieseases that you might have, also tell you about the medicine and precautionary measures you should do.

## Table of Contents
- [Dataset](#dataset)
- [Environment Setup](#environment-setup)
- [Ingestion](#training)

# Dataset
The dataset used in this project is the one provided by the ultralytics and it can be downloaded by the link below :
https://notesmed.com/harrison-principles-of-internal-medicine-21st-edition/


## Environment Setup

To set up your development environment using Conda, follow these steps:

1. **Create a new Conda environment:**

   ```bash
   conda create -n medbot python=3.12.7
   ```
   
2. **Activate the Conda environment:**
    ```bash
    conda activate medbot
    ```
3. **Clone the repository:**
     ```bash
     git clone https://github.com:FarazSheikh16/doctor-ai.git
     cd ai_doctor
     ```
4. **Install the required pakages from requirements.txt:**
     You can install all the required pakages mentioned in requirements.txt using below command
     ```bash
     pip install -r requirements.txt
     ```

## Ingestion
To run the injestion module use the below command:

     python process_injestion.py
