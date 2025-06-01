# summary_generator.py
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
SUMMARY_API_URL = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}

def query_huggingface_api(api_url, payload):
    if not HF_API_TOKEN:
        return {"error": "HF_API_TOKEN is not set."}
    try:
        response = requests.post(api_url, headers=HEADERS, json=payload)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Hugging Face API Request Error: {response.status_code} {response.text} for url: {api_url}. Error: {e}")
        return {"error": f"API request failed: {response.status_code} {response.text}"}
    except json.JSONDecodeError as e:
        print(f"Hugging Face API JSON Decode Error: {e}. Raw response: {response.text}")
        return {"error": f"API returned invalid JSON: {e}"}

def chunk_text(text, max_chunk_size=1000, overlap=100):
    """
    Splits text into chunks of roughly max_chunk_size characters,
    with an optional overlap to maintain context.
    """
    if not text:
        return []
    
    chunks = []
    current_pos = 0
    
    while current_pos < len(text):
        chunk = text[current_pos : current_pos + max_chunk_size]
        chunks.append(chunk)
        current_pos += max_chunk_size - overlap
        if current_pos < 0: 
            current_pos = 0 
    return chunks

def generate_summary(text, max_length=150, min_length=30):
    """Generates a summary of the given text using Hugging Face Inference API."""
    if not HF_API_TOKEN:
        return "Summarization service not available: Hugging Face API Token missing."

    
    text_chunks = chunk_text(text, max_chunk_size=700, overlap=50) 

    summaries = []
    for i, chunk in enumerate(text_chunks):
        payload = {
            "inputs": chunk,
            "parameters": {
                "max_length": max_length,
                "min_length": min_length
            }
        }
        
        print(f"Summarizing chunk {i+1}/{len(text_chunks)} (length: {len(chunk)} chars)...")
        response_data = query_huggingface_api(SUMMARY_API_URL, payload)

        if "error" in response_data:
            print(f"Error summarizing chunk {i+1}: {response_data['error']}")
            summaries.append(f"[Error summarizing chunk {i+1}]")
        elif isinstance(response_data, list) and response_data:
            summary_chunk = response_data[0].get('summary_text', '')
            if summary_chunk:
                summaries.append(summary_chunk)
        else:
            print(f"Unexpected response for chunk {i+1}: {response_data}")
            summaries.append(f"[Unexpected response for chunk {i+1}]")

    
    full_summary = " ".join(summaries).strip()
    
    if not full_summary or full_summary.startswith("[Error summarizing"):
        return "Could not generate a complete summary due to API errors or no content."
    return full_summary