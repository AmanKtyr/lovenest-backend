import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent / '.env')

api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("Starting deep model search...")
working_model = None

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Checking: {m.name}...", end=" ", flush=True)
            try:
                model = genai.GenerativeModel(m.name)
                response = model.generate_content("Hi", generation_config={"max_output_tokens": 5})
                if response.text:
                    print("WORKING!")
                    working_model = m.name
                    break
            except Exception as e:
                err = str(e).lower()
                if "quota" in err:
                    print("QUOTA EXCEEDED")
                elif "404" in err:
                    print("NOT FOUND")
                else:
                    print(f"FAILED ({err[:30]}...)")
except Exception as e:
    print(f"Error listing: {e}")

if working_model:
    print(f"\nFINAL CHOICE: {working_model}")
else:
    print("\nNO WORKING MODELS FOUND WITH QUOTA")
