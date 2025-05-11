# content_processor.py
import re

def clean_extracted_text(extracted_text: str) -> str:
    """
    Cleans OCR-extracted text to make it ready for NLP/question generation.

    Args:
        extracted_text (str): The raw text extracted from PDF/OCR.

    Returns:
        str: Cleaned and structured text.
    """
    # Step 1: Normalize whitespace
    text = re.sub(r'\n+', '\n', extracted_text).strip()

    # Step 2: Fix broken lines (join lines that likely belong together)
    lines = text.split('\n')
    joined_lines = []

    for i in range(len(lines)):
        line = lines[i].strip()

        # If this line doesn't end in punctuation and next line exists
        if i < len(lines) - 1 and not line.endswith(('.', '?', '!', ':')) and lines[i+1].strip() and not lines[i+1].strip()[0].isdigit():
            line += ' ' + lines[i+1].strip()
            lines[i+1] = ''  # avoid re-processing
        if line:
            joined_lines.append(line)

    # Step 3: Normalize quotes and dashes
    text = '\n'.join(joined_lines)
    text = text.replace("“", '"').replace("”", '"').replace("’", "'").replace("–", "-")

    return text
