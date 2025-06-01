# mistral_response.py 
import base64
import os
import pickle
import faiss
import numpy as np
import spacy
from mistralai import Mistral 
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


from create_chunks import sentence_based_chunking

# --- Global setup (load once) ---
load_dotenv() 
nlp = spacy.load("en_core_web_sm") 
embedder = SentenceTransformer('all-MiniLM-L6-v2') 


FAISS_INDEX_DIR = 'faiss_indexes'
os.makedirs(FAISS_INDEX_DIR, exist_ok=True)

GLOBAL_DOCUMENT_STORE_PATH = os.path.join(FAISS_INDEX_DIR, 'global_document_store.pkl')
GLOBAL_FAISS_INDEX_PATH = os.path.join(FAISS_INDEX_DIR, 'global_faiss_index.bin')

# --- OCR Function ---
def extract_text_with_ocr(pdf_path):
    """Extract text from a PDF using Mistral (Kistral) OCR."""
    try:
        # Step 1: Encode PDF to base64
        with open(pdf_path, "rb") as pdf_file:
            base64_pdf = base64.b64encode(pdf_file.read()).decode('utf-8')
    except FileNotFoundError:
        return f"Error: The file {pdf_path} was not found."
    except Exception as e:
        return f"Error reading file: {e}"

    try:
        # Step 2: Call Mistral OCR
        api_key = os.getenv("MISTRAL_API_KEY")
        client = Mistral(api_key=api_key) 
        if not api_key:
            return "Error: MISTRAL_API_KEY is not set in the environment variables."
            
        
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest", 
            document={
                "type": "document_url", 
                "document_url": f"data:application/pdf;base64,{base64_pdf}"
            }
        )
        # Step 3: Combine text from all pages
        extracted_text = "\n\n".join([page.markdown for page in ocr_response.pages])
        return extracted_text

    except Exception as e:
        
        raise Exception(f"Error during OCR processing: {e}")

# --- Embedding Function ---
def embed_chunks_batched(chunks, batch_size=32):
    """Generates embeddings for a list of text chunks in batches."""
    embeddings = []
    if not chunks:
        return np.array([]).astype('float32')
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        batch_embeds = embedder.encode(batch, convert_to_numpy=True)
        embeddings.extend(batch_embeds)
    return np.array(embeddings).astype('float32')

# --- FAISS Management Functions ---
def load_global_faiss_index():
    """Loads the global FAISS index and document store from disk."""
    index = None
    doc_store = {} 
    
    if os.path.exists(GLOBAL_FAISS_INDEX_PATH) and os.path.exists(GLOBAL_DOCUMENT_STORE_PATH):
        try:
            index = faiss.read_index(GLOBAL_FAISS_INDEX_PATH)
            with open(GLOBAL_DOCUMENT_STORE_PATH, 'rb') as f:
                doc_store = pickle.load(f)
            print("Global FAISS index and document store loaded successfully.")
        except Exception as e:
            print(f"Error loading global FAISS index or document store: {e}. Starting fresh.")
            index = None 
            doc_store = {}
    

    if index is None:
        print("No existing FAISS index found or failed to load. Initializing new index.")
        
        dummy_embedding = embedder.encode(["test"], convert_to_numpy=True)[0]
        dimension = len(dummy_embedding)
        index = faiss.IndexFlatL2(dimension)
        
    
    return index, doc_store

def save_global_faiss_index(index, doc_store):
    """Saves the global FAISS index and document store to disk."""
    try:
        faiss.write_index(index, GLOBAL_FAISS_INDEX_PATH)
        with open(GLOBAL_DOCUMENT_STORE_PATH, 'wb') as f:
            pickle.dump(doc_store, f)
        print(f"Global FAISS index saved to {GLOBAL_FAISS_INDEX_PATH}")
        print(f"Global document store saved to {GLOBAL_DOCUMENT_STORE_PATH}")
    except Exception as e:
        print(f"Error saving global FAISS index or document store: {e}")

def add_chunks_to_global_faiss(chunks, document_id, original_filename):
    """
    Adds a list of text chunks to the global FAISS index and document store.
    Returns the updated global index and document store.
    """
    global_index, global_doc_store = load_global_faiss_index()

    new_embeddings = embed_chunks_batched(chunks)
    
    if new_embeddings.size == 0: 
        print("No new embeddings generated for chunks. Skipping FAISS add.")
        return global_index, global_doc_store

    
    start_id = global_index.ntotal

    
    global_index.add(new_embeddings)

    
    for i, chunk in enumerate(chunks):
        global_faiss_id = start_id + i
        global_doc_store[global_faiss_id] = {
            'chunk_text': chunk,
            'doc_id': document_id,
            'source_filename': original_filename
        }
    
    save_global_faiss_index(global_index, global_doc_store)
    print(f"Added {len(chunks)} chunks to global FAISS index for document {document_id}.")
    return global_index, global_doc_store

def search_global_faiss_index(query_text, k=5):
    """
    Performs a similarity search on the global FAISS index for the given query.
    Returns the top k most relevant text chunks.
    """
    global_index, global_doc_store = load_global_faiss_index()

    if global_index is None or global_index.ntotal == 0 or not global_doc_store:
        print("Global FAISS index or document store not loaded/empty. Cannot perform search.")
        return []

    query_embedding = embedder.encode([query_text], convert_to_numpy=True).astype('float32')
    
    # D: distances, I: indices of the retrieved vectors in the FAISS index
    D, I = global_index.search(query_embedding, k)
    
    retrieved_chunks_info = []
    # I[0] contains the indices for the first (and only) query
    for idx in I[0]:
        if idx != -1 and idx in global_doc_store: 
            retrieved_chunks_info.append(global_doc_store[idx]["chunk_text"])
    return retrieved_chunks_info