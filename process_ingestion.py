from src.ingestion.extract_pdf import extract_text_from_pdf
from src.ingestion.metadata import generate_metadata_chunks_with_section_and_topic
from src.ingestion.vectorization import get_embeddings
from src.ingestion.ingestion import ingest_data_into_qdrant

def process_ingestion(pdf_path):
    
    text_chunks = extract_text_from_pdf(pdf_path)
    
    metadata_chunks = generate_metadata_chunks_with_section_and_topic(text_chunks)
    
    embeddings = get_embeddings(metadata_chunks)
    
    ingest_data_into_qdrant(embeddings)
    
    print("Ingestion completed successfully!")

process_ingestion('dataset/Harrison’s Principles of Internal Medicine, 21st Edition (Vol.1 & Vol.2).pdf')