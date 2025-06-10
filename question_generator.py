# question_generator.py
import os
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

# Set your Groq API key
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_questions_from_chunk(chunk, question_type, difficulty):
    prompt = f"""
    Generate {question_type} questions with {difficulty} difficulty from the following text:

    {chunk}

    Output only the questions.
    """

    response = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()
