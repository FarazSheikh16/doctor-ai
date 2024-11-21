from src.wiki import WikipediaPageProcessor
from src.qdrant_handler import QdrantManager
from src.constants import config_path, cancer_types
from src.utils import setup_logger

logger = setup_logger()

def ingest_multiple_wikipedia_pages_to_qdrant(page_titles: list, config_path: str):
    # Step 1: Initialize the QdrantManager with the configuration
    qdrant_manager = QdrantManager(config_path)
    logger.info("Qdrant Connection Establihsed")

    # Step 2: Prepare lists to hold all documents and metadata across all pages
    all_documents = []
    all_metadata = []

    # Step 3: Loop through each page title and process it
    for page_title in page_titles:
        logger.info(f"Processing page: {page_title}")
        processor = WikipediaPageProcessor(page_title)
        chunks = processor.process_page()  # This returns a list of chunks with metadata

        # Step 4: Prepare the documents and metadata for ingestion
        for chunk in chunks:
            content = chunk["content"]
            meta = chunk["metadata"]
            
            # Append the content and metadata to the global lists
            all_documents.append(content)  
            all_metadata.append(meta)  

    # Step 5: Ingest all documents and metadata into Qdrant
    qdrant_manager.ingest_chunks(all_documents, all_metadata)
    logger.info("Ingestion completed for all pages.")

# Usage:
page_titles = cancer_types
ingest_multiple_wikipedia_pages_to_qdrant(page_titles, config_path)
