from typing import List, Dict
from qdrant_client import QdrantClient
from tqdm import tqdm
from src.utils import load_config, setup_logger

class QdrantManager:
    def __init__(self, config_path: str):
        """
        Initialize the Qdrant client and ensure the collection exists.
        
        Args:
            config_path: Path to the configuration YAML file.
        """
        self.logger = setup_logger()
        self.config = load_config(config_path).get("qdrant", {})
        self.__connect_client()
        self.client.set_model(self.config.get("dense_model"))
        self.ensure_collection_exists()
    
    def __connect_client(self):
        """
        Connecting with the Qdrant Client
        """
        self.client = QdrantClient(url=self.config.get('url'))
        print("connection established")

    def ensure_collection_exists(self):
        """
        Check if the collection exists in Qdrant. If not, create it.
        """
        try:
            if not self.client.collection_exists(self.config.get("collection_name")):
                self.logger.info(f"Collection '{self.config.get('collection_name')}' does not exist. Creating new collection.")
                self.client.create_collection(
                    collection_name=self.config.get("collection_name"),
                    vectors_config=self.client.get_fastembed_vector_params(),
                )
                self.logger.info(f"Collection '{self.config.get('collection_name')}' created successfully.")
            else:
                self.logger.info(f"Collection '{self.config.get('collection_name')}' already exists.")
        except Exception as e:
            self.logger.error(f"Error ensuring collection exists: {e}")
            raise

    def ingest_chunks(self, documents: List[Dict], metadata: List[Dict]):
        """
        Ingest document chunks into the Qdrant database using Qdrant's internal embedding generation.
        
        Args:
            documents: List of dictionaries containing document content
            metadata: List of metadata dictionaries corresponding to each document
        """
        try:
            self.logger.info(f"Ingesting {len(documents)} chunks into Qdrant collection '{self.config.get('collection_name')}'...")
            
            # Extract only the text content from documents
            document_texts = [doc["content"] if isinstance(doc, dict) else str(doc) for doc in documents]
            
            # Add documents to Qdrant with metadata
            self.client.add(
                collection_name=self.config.get("collection_name"),
                documents=document_texts,  # Pass only the text content
                metadata=metadata,
                ids=list(range(len(documents))),  # Convert range to list
            )

            self.logger.info(f"Ingested {len(documents)} chunks into Qdrant collection '{self.config.get('collection_name')}'.")
        except Exception as e:
            self.logger.error(f"Error ingesting chunks into Qdrant: {e}")
            raise
