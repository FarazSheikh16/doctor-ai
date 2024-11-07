from sentence_transformers import SentenceTransformer

def get_embeddings(text_chunks):
    model = SentenceTransformer('all-MiniLM-L6-v2')  
    texts = [chunk["content"] for chunk in text_chunks]
    embeddings = model.encode(texts, convert_to_tensor=True)
    
    for i, chunk in enumerate(text_chunks):
        chunk["embedding"] = embeddings[i].cpu().numpy()
    
    return text_chunks
