import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent / '.env')

api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

test_models = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash-latest",
    "gemini-pro",
    "gemini-flash-latest",
    "gemini-2.0-flash",
]

print("Testing models for connectivity and quota...")
for model_name in test_models:
    print(f"\n--- Testing: {model_name} ---")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hi, say 'OK' if you work.", generation_config={"max_output_tokens": 10})
        print(f"Result: {response.text.strip()}")
    except Exception as e:
        print(f"Error: {e}")
