import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
from typing import Dict, List, Optional
import json
from src.constants import API_URL, CLEAN_TEXT_PATTERNS

class WikipediaPageProcessor:
    """Process Wikipedia pages to extract structured content and metadata."""
    
    def __init__(self, page_title: str):
        """
        Initialize the Wikipedia page processor.
        
        Args:
            page_title (str): Title of the Wikipedia page to process
        """
        self.page_title = page_title
        self.wikitext: Optional[str] = None
        self.soup: Optional[BeautifulSoup] = None
        self.metadata: Dict = {}
        self.chunks: List[Dict] = []

    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing wiki markup, references, and other unwanted elements.
        
        Args:
            text (str): Raw text to clean
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        for pattern_dict in CLEAN_TEXT_PATTERNS:
            pattern = pattern_dict["pattern"]
            replacement = pattern_dict["replacement"]
            flags = pattern_dict.get("flags", re.DOTALL)
            text = re.sub(pattern, replacement, text, flags=flags)
        
        return text.strip()


    def fetch_wikitext(self) -> None:
        """Fetch the wikitext content of the Wikipedia page using MediaWiki API."""
        params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": self.page_title,
            "rvslots": "main",
            "rvprop": "content"
        }
        
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        pages = data["query"]["pages"]
        self.wikitext = next(iter(pages.values()))["revisions"][0]["slots"]["main"]["*"]       
    
    def _extract_content_chunks(self) -> None:
        """Extract text content chunks based on headings as well as extract and process table content into chunks, replacing NaN values."""
        
        current_section = "Introduction"
        for element in self.soup.find_all(["h2", "p", "table"]):
            if element.name == "h2":
                current_section = self._clean_text(element.get_text().strip())
            elif element.name == "p":
                if text := self._clean_text(element.get_text().strip()):
                    self.chunks.append({
                        "metadata": {
                            "page_title": self.page_title,
                            **self.metadata,
                            "heading": current_section
                        },
                        "content": text
                    })
            
            elif element.name == "table" and "wikitable" in element.get("class", []):
                try:
                    table_data = pd.read_html(str(element))[0].fillna("Unknown").to_dict(orient="records")
                    self.chunks.append({
                        "metadata": {
                            "page_title": self.page_title,
                            **self.metadata,
                            "heading": current_section
                        },
                        "content": table_data
                    })
                except ValueError:
                    continue
    
    def process_page(self) -> List[Dict]:
        """
        Process the Wikipedia page and return structured chunks.
        
        Returns:
            List[Dict]: List of processed content chunks with metadata
        """
        params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": self.page_title,
            "rvslots": "main",
            "rvprop": "content"
        }
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        pages = data["query"]["pages"]
        self.wikitext = next(iter(pages.values()))["revisions"][0]["slots"]["main"]["*"]
        self.wikitext = self._clean_text(self.wikitext)
        
        # Fetch HTML content
        params = {
            "action": "parse",
            "format": "json",
            "page": self.page_title,
            "prop": "text",
            "disableeditsection": "true",
        }
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        html_content = response.json()["parse"]["text"]["*"]
        self.soup = BeautifulSoup(html_content, "html.parser")
        
        self._extract_content_chunks()
        return self.chunks

    def save_chunks(self, output_file: str) -> None:
        """
        Save processed chunks to a JSON file.
        
        Args:
            output_file (str): Path to output JSON file
        """
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=4)