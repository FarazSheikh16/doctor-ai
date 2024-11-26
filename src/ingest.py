from src.wiki import WikipediaPageProcessor
from src.qdrant_handler import QdrantManager
from src.utils import setup_logger
from src.constants import CONFIG_PATH

logger = setup_logger()

def ingest_multiple_wikipedia_pages_to_qdrant(page_titles: list, config_path: str) -> None:
    """
    Ingests multiple Wikipedia pages into Qdrant.
    
    Args:
        page_titles (list): List of Wikipedia page titles.
        config_path (str): Path to the configuration file.
    """
    qdrant_manager = QdrantManager(CONFIG_PATH)
    logger.info("Qdrant Connection Established")

    all_documents = []
    all_metadata = []

    for page_title in page_titles:
        logger.info(f"Processing page: {page_title}")
        processor = WikipediaPageProcessor(page_title)
        chunks = processor.process_page()

        for chunk in chunks:
            all_documents.append(chunk["content"])
            all_metadata.append(chunk["metadata"])

    qdrant_manager.ingest(all_documents, all_metadata)
    logger.info("Ingestion completed for all pages.")
