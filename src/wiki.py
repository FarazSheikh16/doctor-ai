import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
from typing import Dict, List, Union, Optional
import json
from src.constants import API_URL

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
        
        # Remove references
        text = re.sub(r'<ref.*?</ref>', '', text, flags=re.DOTALL)
        
        # Remove HTML comments
        text = re.sub(r'<!--.*?-->', '', text)
        
        # Extract text from wiki links [[link|text]] -> text or [[text]] -> text
        text = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', text)
        
        # Remove templates
        text = re.sub(r'\{\{.*?\}\}', '', text, flags=re.DOTALL)
        
        # Remove file references
        text = re.sub(r'\[\[File:.*?\]\]', '', text, flags=re.DOTALL)
        
        # Remove numbered references [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove bold/italic markers
        text = re.sub(r"'{2,}", '', text)
        
        # Remove list markers
        text = re.sub(r'^\s*[\*\#]\s*', '', text, flags=re.MULTILINE)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text

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
        # self._parse_infobox()

    def clean_wikitext(self) -> None:
        """Clean the wikitext by removing unwanted elements."""
        if not self.wikitext:
            return
        # Clean the main text
        self.wikitext = self._clean_text(self.wikitext)
        

    def _clean_wiki_value(self, value: str, field_type: str) -> Union[str, List[str]]:
        """
        Clean wiki value and format based on field type.
        
        Args:
            value (str): Raw wiki value to clean
            field_type (str): Type of field being cleaned ('synonyms' or 'symptoms')
                
        Returns:
            Union[str, List[str]]: Cleaned value, either as string or list for synonyms
        """
        cleaned_text = self._clean_text(value)
        
        return cleaned_text

    def _extract_text_chunks(self) -> None:
        """Extract text content chunks based on headings."""
        current_section = "Introduction"
        
        for element in self.soup.find_all(["h2", "p"]):
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

    def _extract_table_chunks(self) -> None:
        """Extract and process table content into chunks, replacing NaN values."""
        current_section = "Introduction"
        
        for element in self.soup.find_all(["h2", "table"]):
            if element.name == "h2":
                current_section = self._clean_text(element.get_text().strip())
            elif element.name == "table" and "wikitable" in element.get("class", []):
                try:
                    # Parse the table into a DataFrame
                    table_data = pd.read_html(str(element))[0]
                    
                    # Replace NaN values with a placeholder
                    table_data = table_data.fillna("Unknown")  # Replace NaN with "Unknown" or any placeholder
                    
                    # Convert the cleaned DataFrame to a list of dictionaries
                    table_dict = table_data.to_dict(orient="records")
                    
                    # Append to chunks with metadata
                    self.chunks.append({
                        "metadata": {
                            "page_title": self.page_title,
                            # **self.metadata,
                            "heading": current_section
                        },
                        "content": table_dict
                    })
                except ValueError:
                    continue


    def process_page(self) -> List[Dict]:
        """
        Process the Wikipedia page and return structured chunks.
        
        Returns:
            List[Dict]: List of processed content chunks with metadata
        """
        self.fetch_wikitext()
        self.clean_wikitext()
        
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
        
        self._extract_text_chunks()
        self._extract_table_chunks()
        
        return self.chunks

    def save_chunks(self, output_file: str) -> None:
        """
        Save processed chunks to a JSON file.
        
        Args:
            output_file (str): Path to output JSON file
        """
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=4)
