# flashcard_generator.py
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
FLASHCARD_MODEL_NAME = "models/gemini-1.5-flash-latest"

def generate_flashcards(summary_text, max_output_tokens=1500):
    """
    Generates flashcards with a key concept on the front and supporting details on the back.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set for flashcard generation.")
        return []

    model = genai.GenerativeModel(FLASHCARD_MODEL_NAME)

    prompt = f"""
    Based on the following document summary, identify the most important key concepts or facts.
    For each key concept, generate a concise statement for the front of a flashcard and a short,
    detailed explanation (which can be a few bullet points or a paragraph) for the back of the flashcard.
    The output must be a JSON array of objects, where each object has a "concept" and "details" key.

    Example Output Format:
    [
      {{
        "concept": "Internet of Things (IoT)",
        "details": "Connects everyday objects to the internet. Allows data exchange between physical devices. Core idea of smart environments."
      }},
      {{
        "concept": "Key IoT Components",
        "details": "- Sensors: Collect data\n- Actuators: Control physical actions\n- Network Connectivity: Enables communication"
      }},
      {{
        "concept": "IoT Security Concerns",
        "details": "Requires careful attention to:\n- Data privacy\n- Device integrity\n- Network vulnerabilities"
      }}
    ]

    Document Summary:
    {summary_text}

    JSON Flashcards:
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3, 
                max_output_tokens=max_output_tokens,
                response_mime_type="application/json" 
            ),
            # safety_settings=genai.types.SafetySetting(...) 
        )

        generated_json_text = response.text.strip()
        print(f"--- Raw Gemini Flashcard JSON Output (start) ---")
        print(generated_json_text)
        print(f"--- Raw Gemini Flashcard JSON Output (end) ---")

        flashcards_data = json.loads(generated_json_text)

        validated_flashcards = []
        if isinstance(flashcards_data, list):
            for item in flashcards_data:
                if isinstance(item, dict) and "concept" in item and "details" in item:
                    validated_flashcards.append(item)
                else:
                    print(f"Warning: Invalid flashcard item found (missing 'concept' or 'details'): {item}")
        else:
            print(f"Warning: Gemini response is not a list for flashcards. Type: {type(flashcards_data)}")
            return []

        return validated_flashcards

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from Gemini API: {e}")
        print(f"Raw output that caused error:\n{generated_json_text}")
        return []
    except Exception as e:
        print(f"Error during Gemini API flashcard generation: {e}")
        return []

# Locally testing the flashcard generation function
if __name__ == '__main__':
    sample_summary = """
    The Internet of Things (IoT) connects everyday objects to the internet, allowing data exchange. Key components include sensors for data collection, actuators for control, and robust network connectivity. IoT devices commonly integrate with cloud computing for data processing and storage. Major cloud providers like Amazon (AWS IoT) and Microsoft (Azure IoT) offer dedicated IoT platforms. Security remains a critical concern in IoT deployments, requiring careful attention to data privacy and device integrity. IoT has applications across smart homes, industrial automation, and healthcare, promising increased efficiency and new services.
    """
    
    # Test generation
    flashcards = generate_flashcards(sample_summary)
    if flashcards:
        print("\nGenerated Flashcards:")
        for i, card in enumerate(flashcards):
            print(f"Card {i+1}: Concept: {card.get('concept', 'N/A')}")
            print(f"           Details: {card.get('details', 'N/A')}")
    else:
        print("No flashcards generated.")