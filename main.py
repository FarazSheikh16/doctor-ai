import argparse
from src.ingest import ingest_multiple_wikipedia_pages_to_qdrant
from src.search import search_documents, log_search_results
from src.bot import run_bot
from src.constants import CONFIG_PATH, CANCER_TYPES
from src.utils import setup_logger

logger = setup_logger()

def main():
    parser = argparse.ArgumentParser(description='Medical Information System')
    parser.add_argument('--ingest', action='store_true', help='Ingest Wikipedia data into Qdrant.')
    parser.add_argument('--search', type=str, help='Search for a query in Qdrant.')
    parser.add_argument('--interactive', action='store_true', help='Run the bot interactively.')
    parser.add_argument('--query', type=str, help='Run a single query in the bot.')

    args = parser.parse_args()

    if args.ingest:
        logger.info("Starting ingestion process...")
        ingest_multiple_wikipedia_pages_to_qdrant(CANCER_TYPES, CONFIG_PATH)
    elif args.search:
        logger.info(f"Performing search for query: {args.search}")
        results = search_documents(query_text=args.search)
        log_search_results(results)
    elif args.interactive or args.query:
        run_bot(config_path=CONFIG_PATH, interactive=args.interactive, query=args.query)
    else:
        logger.error("Please specify an action: --ingest, --search, --interactive, or --query.")

if __name__ == "__main__":
    main()
