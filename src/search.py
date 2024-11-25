from src.qdrant_handler import QdrantManager
from src.utils import setup_logger
from src.constants import CONFIG_PATH
logger = setup_logger()

def search_documents(query_text: str, filter_conditions: dict = None, limit: int = 5):
    """
    Search for documents in Qdrant based on a query text.
    
    Args:
        query_text (str): The text to search for.
        filter_conditions (dict, optional): Filter conditions for metadata.
        limit (int, optional): Maximum number of results to return.
    
    Returns:
        list: List of search results with metadata, text content, and scores.
    """
    try:
        qdrant_manager = QdrantManager(CONFIG_PATH)
        logger.info("Qdrant Connection Established")
        
        results = qdrant_manager.search(
            text=query_text,
            filter_conditions=filter_conditions,
            limit=limit
        )
        logger.info(f"Found {len(results)} results for query: {query_text}")
        return results
    except Exception as e:
        logger.error(f"Error during search: {e}")
        raise

def log_search_results(results, query_type="Search"):
    """
    Helper function to log search results in a formatted way.
    
    Args:
        results: List of search results.
        query_type: String indicating the type of search (default or filtered).
    """
    logger.info(f"\n{query_type} Results:")
    for i, result in enumerate(results, 1):
        logger.info(f"\nResult {i} (Score: {result['score']:.3f}):")
        logger.info(f"Document Title: {result['metadata'].get('page_title', 'N/A')}")
        logger.info(f"Section: {result['metadata'].get('heading', 'N/A')}")
        logger.info(f"Content: {result['text'][:300]}...")
        logger.info("=" * 80)
