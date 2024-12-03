from src.generator import RAGModule
from src.utils import setup_logger
from typing import Dict, List

logger = setup_logger()

def log_result(result: dict) -> None:
    """
    Log RAG results in a formatted way.
    
    Args:
        result (dict): The response dictionary containing generated text and sources.
    """
    logger.info("\nGenerated Response:")
    logger.info("-" * 80)
    logger.info(result['response'])
    logger.info("\nSources Used:")
    logger.info("-" * 80)
    for i, source in enumerate(result['sources'], 1):
        logger.info(f"{i}. {source['title']} - {source['section']}")
        logger.info(f"   Relevance Score: {source['score']:.3f}")
    logger.info("-" * 80)

def run_bot(config_path: str, interactive: bool = False, query: str = None, conversation_history: List[Dict] = None) -> Dict:
    """
    Run the bot in interactive mode or with a single query.
    
    Args:
        config_path (str): Path to the configuration file.
        interactive (bool): Whether to run in interactive mode.
        query (str, optional): A single query to process.
        conversation_history (List[Dict], optional): The history of the conversation for context.
        
    Returns:
        Dict: Contains 'response' and 'sources' keys
    """
    try:
        rag = RAGModule(config_path)

        if interactive:
            logger.info("Starting interactive mode...")
            logger.info("Enter your questions and type 'quit' to exit.")
            while True:
                user_query = input("\nEnter your medical question: ")
                if user_query.lower() == 'quit':
                    logger.info("Exiting interactive mode.")
                    break
                result = rag.get_response(query=user_query)
                log_result(result)
                
        elif query:
            # Include conversation history for context
            logger.info(f"Processing single query: {query}")
            result = rag.get_response(query=query, conversation_history=conversation_history)
            logger.info(f"Result type: {type(result)}")
            
            # Ensure result is properly formatted
            if isinstance(result, dict):
                return {
                    "response": result.get("response", ""),
                    "sources": result.get("sources", [])
                }
            else:
                return {
                    "response": str(result),
                    "sources": []
                }
                
    except Exception as e:
        logger.error(f"Error in run_bot: {e}")
        return {
            "response": f"Error processing query: {str(e)}",
            "sources": []
        }
