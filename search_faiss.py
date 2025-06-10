from sentence_transformers import SentenceTransformer
from mistral_response import embedder
import numpy as np

embedder = SentenceTransformer('all-MiniLM-L6-v2')

def search_similar_chunks(query_text, index, chunks, k=1):
    """
    Convert query to embedding, search FAISS, return top-k chunks.
    """
    query_embedding = embedder.encode([query_text]).astype('float32')
    D, I = index.search(query_embedding, k)
    retrieved = [chunks[i] for i in I[0]]
    return retrieved