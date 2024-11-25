from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.ingest import ingest_multiple_wikipedia_pages_to_qdrant
from src.search import search_documents
from src.bot import run_bot
from src.constants import CONFIG_PATH, CANCER_TYPES
from src.utils import setup_logger

logger = setup_logger()

app = FastAPI(title="Medical Information API", description="API for Medical Information System", version="1.0")

# Data Models
class SearchQuery(BaseModel):
    query: str
    filter_conditions: dict = None
    limit: int = 5

class BotQuery(BaseModel):
    query: str
    num_results: int = 10

@app.get("/")
def root():
    """Root endpoint for testing API availability."""
    logger.info("Root endpoint accessed.")
    return {"message": "Medical Information API is running."}

@app.post("/ingest")
def ingest_data():
    """Endpoint to ingest Wikipedia pages into Qdrant."""
    try:
        logger.info("Ingestion endpoint called.")
        ingest_multiple_wikipedia_pages_to_qdrant(CANCER_TYPES, CONFIG_PATH)
        return {"message": "Ingestion completed successfully."}
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail="Ingestion failed.")

@app.post("/search")
def search_data(search_query: SearchQuery):
    """Endpoint to search documents in Qdrant."""
    try:
        logger.info(f"Search endpoint called with query: {search_query.query}")
        results = search_documents(
            query_text=search_query.query,
            filter_conditions=search_query.filter_conditions,
            limit=search_query.limit
        )
        return {"results": results}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed.")

@app.post("/generate")
def generate_response(bot_query: BotQuery):
    """Endpoint to generate a response using the bot."""
    try:
        logger.info(f"Bot generation endpoint called with query: {bot_query.query}")
        rag = run_bot(config_path=CONFIG_PATH, interactive=False, query=bot_query.query)
        return {"response": rag["response"], "sources": rag["sources"]}
    except Exception as e:
        logger.error(f"Bot generation failed: {e}")
        raise HTTPException(status_code=500, detail="Response generation failed.")
