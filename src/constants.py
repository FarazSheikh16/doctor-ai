import re
from src.utils import load_config

CONFIG_PATH = "configs/configs.yaml"
CONFIG = load_config(CONFIG_PATH)
API_URL = CONFIG['wikipedia_api']['base_url']

CANCER_TYPES = [
   "Basal-cell carcinoma", "Leiomyosarcoma", "Gastrinoma",
   "Acute myeloid leukemia", "Chronic lymphocytic leukemia",
   "Small cell lung cancer", "Glioma", "Ependymoma",
   "Pancreatic Cancer", "Thyroid cancer"
]


CLEAN_TEXT_PATTERNS = [
    {"pattern": r'<ref.*?</ref>', "replacement": ''},                     # Remove references
    {"pattern": r'<!--.*?-->', "replacement": ''},                        # Remove HTML comments
    {"pattern": r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', "replacement": r'\1'}, # Extract text from wiki links
    {"pattern": r'\{\{.*?\}\}', "replacement": ''},                       # Remove templates
    {"pattern": r'\[\[File:.*?\]\]', "replacement": ''},                  # Remove file references
    {"pattern": r'\[\d+\]', "replacement": ''},                           # Remove numbered references
    {"pattern": r'<[^>]+>', "replacement": ''},                           # Remove HTML tags
    {"pattern": r"'{2,}", "replacement": ''},                             # Remove bold/italic markers
    {"pattern": r'^\s*[\*\#]\s*', "replacement": '', "flags": re.MULTILINE},  # Remove list markers
    {"pattern": r'\s+', "replacement": ' '}                               # Remove extra whitespace
]

