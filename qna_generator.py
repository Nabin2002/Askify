# qna_generator.py
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
QNA_MODEL_NAME = "models/gemini-1.5-flash-latest"

def generate_questions_answers(text, num_qa_pairs=3, max_new_tokens=1000):
    """
    Generates questions and answers from the document content using Google Gemini API.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set for Q&A generation.")
        return []

    model = genai.GenerativeModel(QNA_MODEL_NAME)

    prompt = f"""
    Based on the following document content, generate {num_qa_pairs} distinct question-answer pairs that cover key information.
    The questions should be clear and the answers should be concise and directly derived from the text.
    Format your response *strictly* as a JSON array of objects, where each object has "question" and "answer" keys.

    Example JSON structure:
    [
      {{"question": "What is the capital of France?", "answer": "Paris"}}
    ]

    Document Content:
    {text}

    JSON Output:
    """
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=max_new_tokens,
                response_mime_type="application/json"
            )
        )
        
        generated_text = response.text.strip()
        
        try:
            qa_data = json.loads(generated_text)
            if isinstance(qa_data, list):
                return qa_data[:num_qa_pairs]
            elif isinstance(qa_data, dict) and "qa_pairs" in qa_data:
                return qa_data["qa_pairs"][:num_qa_pairs]
            else:
                raise ValueError("Unexpected JSON structure for Q&A.")
        except json.JSONDecodeError as e:
            print(f"Gemini API returned invalid JSON for Q&A: {generated_text[:500]}... Error: {e}")
            start_idx = generated_text.find('[')
            end_idx = generated_text.rfind(']')
            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                try:
                    extracted_json_str = generated_text[start_idx : end_idx + 1]
                    qa_data = json.loads(extracted_json_str)
                    if isinstance(qa_data, list):
                        return qa_data[:num_qa_pairs]
                    elif isinstance(qa_data, dict) and "qa_pairs" in qa_data:
                        return qa_data["qa_pairs"][:num_qa_pairs]
                    else:
                        print("Failed to extract valid list from malformed JSON.")
                        return []
                except Exception as ex:
                    print(f"Failed to extract JSON from malformed response: {ex}")
            return []
    except Exception as e:
        print(f"Error during Gemini API Q&A generation: {e}")
        return []
    

def answer_question_from_context(question, context, max_new_tokens=500):
    """
    Answers a specific question based *only* on the provided context using Google Gemini API.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set for Q&A generation.")
        return "Error: API key not configured."

    model = genai.GenerativeModel(QNA_MODEL_NAME) 

    prompt = f"""
    Based *only* on the following context, answer the question accurately and concisely.
    If the answer cannot be found in the context, state that clearly and do not make up information.

    Context:
    {context}

    Question: {question}

    Answer:
    """
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1, # Keeping temperature low for factual answers
                max_output_tokens=max_new_tokens
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error during Gemini API answer generation from context: {e}")
        return "An error occurred while generating the answer."