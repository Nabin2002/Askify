import base64
import os
from mistralai import Mistral

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
        api_key = ""  # Secure it via environment variable in production
        client = Mistral(api_key=api_key)

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
