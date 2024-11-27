from typing import List, Dict,Optional
import hashlib
import numpy as np
from tqdm import tqdm
from qdrant_client import QdrantClient, models
from qdrant_client.models import VectorParams, Distance, PointStruct
from fastembed import TextEmbedding
from src.utils import load_config, setup_logger

class QdrantManager:
    def __init__(self, config_path: str):
        """
        Initialize the Qdrant client and embedding model.
        
        Args:
            config_path: Path to the configuration YAML file.
        """
        self.logger = setup_logger()
        self.config = load_config(config_path).get("qdrant", {})
        self.collection_name = self.config.get("collection_name")
        self._init_embedding_model()
        self.__connect()
        self.get_or_create_collection()

    def _init_embedding_model(self) -> None:
        """
        Initialize the embedding model.
        """
        try:
            self._model = TextEmbedding(model_name=self.config.get("dense_model"))
            self.logger.info("Initialized embedding model: sentence-transformers/all-MiniLM-L6-v2")
        except Exception as e:
            self.logger.error(f"Failed to initialize embedding model: {e}")
            raise RuntimeError("Could not initialize embedding model")

    def _generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for text content.
        
        Args:
            text: Text content to embed
            
        Returns:
            np.ndarray: Embedding vector
        """
        try:
            embedding = list(self._model.embed(text))[0]
            return embedding
        except Exception as e:
            self.logger.error(f"Embedding generation error: {e}")
            raise

    def __connect(self) -> None:
        """
        Connecting with the Qdrant Client with error handling
        """
        try:
            self.client = QdrantClient(url=self.config.get('url'))
            self.logger.info("Successfully connected to Qdrant client")
        except Exception as e:
            self.logger.error(f"Error connecting to Qdrant client: {e}")
            raise

    def _generate_chunk_hash(self, content: str, metadata: Dict) -> str:
        """
        Generate a unique hash for a chunk to prevent duplicates.
        """
        hash_content = str(content) + str(metadata)
        return hashlib.md5(hash_content.encode('utf-8')).hexdigest()

    def get_or_create_collection(self) -> None:
        """
        Check if the collection exists in Qdrant. If not, create it.
        """
        try:
            if not self.client.collection_exists(self.collection_name):
                self.logger.info(f"Collection '{self.collection_name}' does not exist. Creating new collection.")
                
                # Get vector size from a sample embedding
                sample_embedding = self._generate_embedding("sample text")
                vector_size = len(sample_embedding)
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                self.logger.info(f"Collection '{self.collection_name}' created successfully.")
            else:
                self.logger.info(f"Collection '{self.collection_name}' already exists.")
        except Exception as e:
            self.logger.error(f"Error ensuring collection exists: {e}")
            raise

    def ingest(self, documents: List[Dict], metadata: List[Dict]):
        """
        Ingest document chunks into the Qdrant database using upsert.
        
        Args:
            documents: List of dictionaries containing document content
            metadata: List of metadata dictionaries corresponding to each document
        """
        try:
            self.logger.info(f"Ingesting {len(documents)} chunks into Qdrant collection '{self.collection_name}'...")
            
            points = []
            for doc, meta in tqdm(zip(documents, metadata), total=len(documents)):
                try:
                    # Extract content and generate hash
                    content = doc["content"] if isinstance(doc, dict) else str(doc)
                    chunk_hash = self._generate_chunk_hash(content, meta)
                    
                    # Generate embedding using our embedding model
                    vector = self._generate_embedding(content)
                    
                    # Create point
                    point = PointStruct(
                        id=chunk_hash,
                        vector=vector.tolist(),  # Convert numpy array to list
                        payload={
                            "text": content,
                            "metadata": meta
                        }
                    )
                    points.append(point)
                    
                except Exception as e:
                    self.logger.error(f"Error processing chunk: {e}")
                    continue

            # Batch upsert points
            if points:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                self.logger.info(f"Successfully ingested {len(points)} chunks into Qdrant collection '{self.collection_name}'.")
            else:
                self.logger.warning("No valid points to ingest.")

        except Exception as e:
            self.logger.error(f"Error ingesting chunks into Qdrant: {e}")
            raise

    def search(self, text: str, filter_conditions: Optional[Dict] = None, limit: int = 5) -> list:
        """
        Search for similar documents with optional filtering.
        
        Args:
            text: Query text
            filter_conditions: Optional dictionary of filter conditions
            limit: Number of results to return
            
        Returns:
            List[Dict]: List of dictionaries containing metadata, text content, and score
        """
        try:
            # Generate embedding for search query
            query_vector = self._generate_embedding(text)

            # Convert filter conditions to Qdrant filter if provided
            query_filter = None
            if filter_conditions:
                filter_must = []
                for key, value in filter_conditions.items():
                    filter_must.append(
                        models.FieldCondition(
                            key=f"metadata.{key}",
                            match=models.MatchValue(value=value)
                        )
                    )
                query_filter = models.Filter(must=filter_must)

            # Perform search
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector.tolist(),
                query_filter=query_filter,
                limit=limit,
                with_payload=True, 
                score_threshold=0.0  
            )

            # Extract metadata, text content, and score
            results = []
            for hit in search_result:
                result = {
                    'metadata': hit.payload.get('metadata', {}),
                    'text': hit.payload.get('text', ''),
                    'score': hit.score
                }
                results.append(result)
                
            return results

        except Exception as e:
            self.logger.error(f"Error performing search: {e}")
            raise