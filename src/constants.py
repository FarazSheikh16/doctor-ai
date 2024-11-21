from typing import Dict
from src.utils import load_config

config_path = "configs/configs.yaml"
CONFIG = load_config("configs/configs.yaml")
API_URL = CONFIG['WIKIPEDIA_API']['BASE_URL']

cancer_types = [
   "Basal-cell carcinoma", "Leiomyosarcoma", "Gastrinoma"
]
