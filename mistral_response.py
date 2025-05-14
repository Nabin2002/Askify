import base64
import os
from mistralai import Mistral
from dotenv import load_dotenv  # Import dotenv
import time
import concurrent.futures
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import textstat
from content_processor import clean_extracted_text
from create_chunks import sentence_based_chunking
import spacy
# Load spaCy model
nlp = spacy.load("en_core_web_sm")


# Load environment variables from .env file
load_dotenv()


def extract_text_with_ocr(pdf_path):
    """Extract text from a PDF using Mistral OCR."""
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
        api_key = os.getenv("MISTRAL_API_KEY")  # Retrieve API key from environment variable
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
        return f"Error during OCR processing: {e}"




def sent_tokenize_spacy(text):
    doc = nlp(text)
    return [sent.text for sent in doc.sents]

# Load models
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def embed_chunks_batched(chunks, batch_size=32):
    embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        batch_embeds = embedder.encode(batch, convert_to_numpy=True)
        embeddings.extend(batch_embeds)
    return np.array(embeddings).astype('float32')


# Step 6: Embed questions and store in FAISS
def store_in_faiss_parallel(chunks, save_path=None):
    print("[Info] Embedding chunks in batch...")
    embeddings = embed_chunks_batched(chunks)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    if save_path:
        faiss.write_index(index, save_path)
        print(f"[Info] Index saved to {save_path}")

    print(f"[Info] Stored {len(embeddings)} vectors in FAISS.")
    return index, embeddings


# Step 4: Run the simplified pipeline
def run_pipeline(pdf_path):
    """Run the simplified pipeline: extract text, chunk, embed, and store in FAISS."""
    print("[1] Extracting text from PDF...")
    text = extract_text_with_ocr(pdf_path)
    if text.startswith("Error"):
        print(text)
        return


    #print("[2] Cleaning extracted text...")
    #text = clean_extracted_text(text)

    print("[3] Chunking text...")
    chunks = sentence_based_chunking(text, max_words=200)
    print(f"Total chunks created: {len(chunks)}")

    print("[4] Embedding chunks and storing in FAISS...")
    index, embeddings = store_in_faiss_parallel(chunks)
    print("[✅] Text successfully stored in FAISS vector database.")

    # Return the FAISS index and embeddings for inspection
    return index, embeddings, chunks