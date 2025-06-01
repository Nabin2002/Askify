#create_chunks.py
import spacy

# Load spaCy model (do this only once)
nlp = spacy.load("en_core_web_sm")

# Sentence tokenizer using spaCy
def sent_tokenize_spacy(text):
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


def sentence_based_chunking(text, max_words=200):
    sentences = sent_tokenize_spacy(text)
    chunks = []
    current_chunk = []

    for sentence in sentences:
        if len(" ".join(current_chunk + [sentence]).split()) <= max_words:
            current_chunk.append(sentence)
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks