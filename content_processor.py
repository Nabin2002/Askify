import re

def clean_extracted_text(text: str) -> str:
    """
    Cleans extracted OCR text to remove noise and prepare for chunking.
    """

    # Step 1: Remove page numbers and artifacts
    text = re.sub(r'\f', '', text)  # Remove form feed characters (page breaks)
    text = re.sub(r'Page\s*\d+(\s*of\s*\d+)?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d{1,3}\b', lambda m: '' if len(m.group(0)) <= 2 else m.group(0), text)
    text = re.sub(r'[\|\*_]{2,}', '', text)  # Remove long repeated characters like ___ or ||||

    # Step 2: Remove lines that are all caps and very short (likely headers/footers)
    text = "\n".join([
        line for line in text.split("\n")
        if not (line.strip().isupper() and len(line.strip().split()) <= 5)
    ])

    # Step 3: Remove TOC-like entries (e.g., "1. Introduction .................. 5")
    text = re.sub(r'\.{5,}\s*\d+', '', text)

    # Step 4: Normalize whitespace and remove empty lines
    text = re.sub(r'\n{2,}', '\n\n', text)  # Preserve paragraph breaks
    text = re.sub(r'[ \t]+', ' ', text)     # Normalize spaces
    text = text.strip()

    return text
