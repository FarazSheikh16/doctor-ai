from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

def ingest_data_into_qdrant(embeddings):
    client = QdrantClient("http://localhost:6333")  
    
    # Create collection with vectors
    client.recreate_collection(
        collection_name="medical_text",
        vectors_config=VectorParams(size=len(embeddings[0]["embedding"]), distance=Distance.COSINE)
    )
    
    for i, data in enumerate(embeddings):
        client.upsert(
            collection_name="medical_text",
            points=[
                PointStruct(
                    id=i,
                    vector=data["embedding"],
                    payload={
                        "page_num": data["page_num"],
                        "content": data["content"],
                        "section_name": data["section_name"],
                        "topic_name": data["topic_name"]
                    }
                )
            ]
        )
