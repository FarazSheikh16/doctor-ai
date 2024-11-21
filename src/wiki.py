import requests
import re
from bs4 import BeautifulSoup
import pandas as pd

class WikipediaPageProcessor:
    WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
    
    # Define the fields we want to extract and their possible variations in the infobox
    DESIRED_FIELDS = {
        'synonyms': ['synonyms', 'other_names', 'alias'],
        'symptoms': ['symptoms', 'symptom', 'signs_symptoms', 'signs_and_symptoms']
    }

    def __init__(self, page_title):
        self.page_title = page_title
        self.wikitext = None
        self.soup = None
        self.metadata = {}
        self.chunks = []


    def fetch_wikitext(self):
        """
        Fetch the wikitext of the Wikipedia page using MediaWiki API.
        """
        params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": self.page_title,
            "rvslots": "main",
            "rvprop": "content"
        }
        response = requests.get(self.WIKIPEDIA_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        pages = data["query"]["pages"]
        self.wikitext = next(iter(pages.values()))["revisions"][0]["slots"]["main"]["*"]
        # Parse infobox right after fetching wikitext
        self.parse_infobox()

    def clean_wikitext(self):
        """
        Clean the wikitext by removing unwanted elements like references, templates, and images.
        """
        # Store infobox before cleaning
        infobox_match = re.search(r"\{\{Infobox.*?\}\}", self.wikitext, flags=re.DOTALL)
        infobox_text = infobox_match.group() if infobox_match else ""
        
        # Clean the wikitext
        self.wikitext = re.sub(r"<ref.*?>.*?</ref>", "", self.wikitext, flags=re.DOTALL)
        self.wikitext = re.sub(r"\{\{(?!Infobox).*?\}\}", "", self.wikitext, flags=re.DOTALL)  # Remove templates except Infobox
        self.wikitext = re.sub(r"\[\[File:.*?\]\]", "", self.wikitext, flags=re.DOTALL)
        self.wikitext = re.sub(r"\[\d+\]", "", self.wikitext)
        self.wikitext = re.sub(r"<.*?>", "", self.wikitext)
        
        # Restore infobox if it existed
        if infobox_text:
            self.wikitext = infobox_text + "\n" + self.wikitext

    def clean_wiki_value(self, value):
        """
        Clean wiki markup from a value string.
        """
        if not value:
            return ""
            
        # Remove HTML comments
        value = re.sub(r'<!--.*?-->', '', value)
        
        # Remove reference tags
        value = re.sub(r'<ref.*?</ref>', '', value, flags=re.DOTALL)
        
        # Extract text from wiki links [[link|text]] -> text or [[text]] -> text
        value = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', value)
        
        # Remove bold/italic markers
        value = re.sub(r"'{2,}", '', value)
        
        # Remove templates {{...}}
        value = re.sub(r'\{\{[^\}]*\}\}', '', value)
        
        # Remove HTML tags
        value = re.sub(r'<[^>]+>', '', value)
        
        # Remove bulleted lists markers
        value = re.sub(r'^\s*[\*\#]\s*', '', value, flags=re.MULTILINE)
        
        # Remove extra whitespace
        value = re.sub(r'\s+', ' ', value.strip())
        
        # Split on commas if it's a list-like value (for synonyms)
        if any(field in self.DESIRED_FIELDS['synonyms'] for field in self.DESIRED_FIELDS['synonyms']):
            value = [item.strip() for item in value.split(',') if item.strip()]
            
        return value


    def parse_infobox(self):
        """
        Parse specific metadata fields from the infobox.
        """
        if not self.wikitext:
            return
            
        infobox_match = re.search(r"\{\{Infobox.*?\}\}", self.wikitext, flags=re.DOTALL)
        if infobox_match:
            infobox_text = infobox_match.group()
            raw_metadata = self.extract_metadata_from_infobox(infobox_text)
            
            # Initialize desired fields
            cleaned_metadata = {
                'synonyms': [],
                'symptoms': ''
            }
            
            # Process each desired field
            for target_field, possible_keys in self.DESIRED_FIELDS.items():
                for key in possible_keys:
                    if key in raw_metadata:
                        value = self.clean_wiki_value(raw_metadata[key])
                        if value:
                            cleaned_metadata[target_field] = value
                            break
            
            self.metadata = {k: v for k, v in cleaned_metadata.items() if v}  # Remove empty fields
        else:
            self.metadata = {}

    @staticmethod
    def extract_metadata_from_infobox(infobox_text):
        """
        Extract key-value metadata from the infobox.
        """
        metadata = {}
        lines = infobox_text.splitlines()
        for line in lines:
            match = re.match(r"\|\s*(.*?)\s*=\s*(.*)", line)
            if match:
                key, value = match.groups()
                key = key.strip().lower()  # Normalize keys to lowercase
                value = value.strip()
                if key and value:
                    metadata[key] = value
        return metadata


    def parse_html_content(self):
        """
        Convert the cleaned wikitext to HTML using the MediaWiki parser.
        """
        params = {
            "action": "parse",
            "format": "json",
            "page": self.page_title,
            "prop": "text",
            "disableeditsection": "true",
        }
        response = requests.get(self.WIKIPEDIA_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        html_content = data["parse"]["text"]["*"]
        self.soup = BeautifulSoup(html_content, "html.parser")

    def extract_text_chunks(self):
        """
        Extract text chunks based on headings and add them to self.chunks.
        """
        current_section = "Introduction"  # Default section for text before first heading
        for element in self.soup.find_all(["h2", "p"]):
            if element.name == "h2":
                heading_text = element.get_text().strip()
                current_section = re.sub(r"\[.*?\]", "", heading_text)
            elif element.name == "p":
                text = element.get_text().strip()
                text = re.sub(r"\[.*?\]", "", text)
                if text:  # Only add non-empty paragraphs
                    chunk = {
                        "metadata": {
                            "page_title": self.page_title,
                            **self.metadata,  # Include all metadata
                            "heading": current_section
                        },
                        "content": text
                    }
                    self.chunks.append(chunk)

    def extract_table_chunks(self):
        """
        Extract tables from the HTML content and add them as chunks.
        """
        current_heading = "Introduction"
        for element in self.soup.find_all(["h2", "table"]):
            if element.name == "h2":
                heading_text = element.get_text().strip()
                current_heading = re.sub(r"\[.*?\]", "", heading_text)
            elif element.name == "table" and "wikitable" in element.get("class", []):
                try:
                    df = pd.read_html(str(element))[0]
                    chunk = {
                        "metadata": {
                            "heading": current_heading,
                            "page_title": self.page_title,
                            **self.metadata  # Include all metadata
                        },
                        "content": df.to_dict(orient="records")
                    }
                    self.chunks.append(chunk)
                except ValueError:
                    continue

    def create_chunks(self):
        """
        Create all chunks with proper metadata.
        """
        self.parse_html_content()
        self.extract_text_chunks()
        self.extract_table_chunks()

    def save_chunks(self, output_file):
        """
        Save chunks to a file.
        """
        import json
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=4)

    def print_chunks(self):
        """
        Print the extracted chunks for verification.
        """
        for i, chunk in enumerate(self.chunks):
            print(f"\nChunk {i + 1}:")
            print("Metadata:", chunk["metadata"])
            print("Content:", chunk["content"][:200] + "..." if isinstance(chunk["content"], str) else chunk["content"])