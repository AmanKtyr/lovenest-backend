import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# Load env directly
load_dotenv(Path(__file__).resolve().parent / '.env')

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: No API key found in .env")
    exit(1)

genai.configure(api_key=api_key)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
