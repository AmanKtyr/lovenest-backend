import os
from django.conf import settings
import google.generativeai as genai
import json

# Configure Gemini API
# Use the recommended model for text generation
MODEL_NAME = "gemini-2.0-flash-lite"

def get_model(model_name=MODEL_NAME):
    # Try Django settings first, then direct environment variable
    api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.environ.get("GEMINI_API_KEY")
    
    if not api_key or api_key == 'your_gemini_api_key_here' or len(api_key.strip()) < 10:
        print("DEBUG: Gemini API Key not found or invalid.")
        raise ValueError(f"Gemini API Key is not configured properly in .env or settings.py.")
    
    genai.configure(api_key=api_key.strip())
    print(f"DEBUG: Configured Gemini API with model: {model_name}")
    return genai.GenerativeModel(model_name)

class AIGeneratorService:
    @staticmethod
    def _generate_with_fallback(prompt, is_multimodal=False, image=None):
        """Helper to try various models in sequence to handle quota or availability issues."""
        # Verified available models for this project
        model_sequence = [
            MODEL_NAME,             # gemini-2.0-flash-lite
            "gemini-2.0-flash", 
            "gemini-flash-latest"   # Concurred working in tests
        ]
        
        last_error = None
        for m_name in model_sequence:
            try:
                model = get_model(m_name)
                if is_multimodal and image:
                    return model.generate_content([prompt, image])
                return model.generate_content(prompt)
            except Exception as e:
                last_error = e
                err_msg = str(e)
                # If it's a quota or model not found error, try the next one
                if any(x in err_msg for x in ["429", "404", "quota", "limit", "not found"]):
                    print(f"Model {m_name} failed ({err_msg}). Trying next in sequence...")
                    continue
                # If it's another kind of error (e.g. prompt blocked), we might want to stop
                raise e
        
        raise Exception(f"AI Quota Exceeded (All models failed). Last error: {last_error}")

    @staticmethod
    def generate_date_ideas(location: str, budget: str, vibe: str, preferences: str = "") -> list:
        """
        Generates personalized date ideas.
        """
        print(f"DEBUG: Generating date ideas for {location}...")
        prompt = f"""
        Act as a professional relationship coach and expert date planner.
        Generate exactly 3 unique, high-quality date ideas for a couple.
        
        Parameters:
        - Location: {location}
        - Budget level: {budget} ($, $$, or $$$)
        - Vibe/Theme: {vibe}
        - Additional Preferences: {preferences if preferences else "None"}
        
        Your response MUST be exclusively valid JSON format, matching this schema:
        [
          {{
            "title": "Short catchy title of the date",
            "description": "Detailed 2-3 sentence description of what the date entails and why it fits the vibe.",
            "estimated_cost": "Estimated cost string (e.g. '$50', 'Free')",
            "vibe": "{vibe}"
          }}
        ]
        
        Do not include any Markdown formatting blocks (e.g. ```json), just output the raw JSON array.
        """
        
        try:
            response = AIGeneratorService._generate_with_fallback(prompt)
            # Clean response text in case it contains markdown formatting
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating date ideas: {error_msg}")
            if "response.text" in error_msg or "blocked" in error_msg.lower():
                raise Exception("AI response was blocked. Try a different prompt.")
            raise Exception(f"Date AI Error: {error_msg}")

    @staticmethod
    def relationship_coach_chat(history: list, new_message: str, context: str = "") -> str:
        """
        Chatbot for relationship coaching with strict persona and space awareness.
        """
        system_instruction = f"""
        You are "Cupid", a professional, empathetic, and premium Relationship Coach.
        CORE PERSONA: Your expertise is STRICTLY limited to relationships, communication, and emotional wellness.
        STRICT BOUNDARIES: If the user asks about ANY topic outside of relationship coaching, refuse politely.
        CURRENT RELATIONSHIP CONTEXT: {context if context else "No specific context provided yet."}
        """
        
        # Trim history to last 10 messages to save tokens
        trimmed_history = history[-10:] if len(history) > 10 else history
        
        # Format for start_chat
        formatted_history = []
        for msg in trimmed_history:
            formatted_history.append({"role": msg.get("role", "user"), "parts": [msg.get("content", "")]})
            
        if not trimmed_history:
            prompt = f"{system_instruction}\n\nClient: {new_message}"
        else:
            prompt = f"(Context Reminder: {context[:200]})\nClient: {new_message}"
            
        # Use our robust fallback generator
        # Note: start_chat is a bit more complex for fallback, so we'll use generate_content for simplicity
        # with the full prompt context if needed, OR we just trust the _generate_with_fallback
        # Actually, let's just use generate_content with the full context for now to keep the fallback simple.
        
        full_prompt = f"{system_instruction}\n\n"
        for msg in formatted_history:
            role = "User" if msg['role'] == 'user' else "Cupid"
            full_prompt += f"{role}: {msg['parts'][0]}\n"
        full_prompt += f"User: {new_message}\nCupid:"

        try:
            response = AIGeneratorService._generate_with_fallback(full_prompt)
            return response.text
        except Exception as e:
            error_msg = str(e)
            print(f"Error in relationship coach: {error_msg}")
            raise Exception(f"Cupid Coach AI Error: {error_msg}")

    @staticmethod
    def generate_memory_caption(image_data) -> dict:
        """
        Uses Gemini's Vision capabilities to generate a sweet caption and summary.
        """
        prompt = "Look at this photo. Generate a short, sweet title (max 5 words) and a heartwarming 2-sentence description for a couple's memory journal. Output strictly valid JSON with keys 'title' and 'description'. Do NOT include any markdown block ticks like ```json, just the JSON string."
        
        try:
            from PIL import Image
            img = Image.open(image_data)
            
            # Use fallback (1.5-flash specifically handles vision well)
            response = AIGeneratorService._generate_with_fallback(prompt, is_multimodal=True, image=img)
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating memory caption: {error_msg}")
            raise Exception(f"Memory AI Error: {error_msg}")

    @staticmethod
    def generate_gift_ideas(gender: str, occasion: str, budget: str, interests: str, extra_info: str = "") -> list:
        """
        Generates personalized gift ideas based on partner's info.
        """
        print(f"DEBUG: Generating gift ideas for {interests}...")
        prompt = f"""
        Act as a professional gift consultant and romance expert. 
        Your task is to suggest the perfect gift for a partner with the following details:
        
        - Recipient Gender: {gender}
        - Occasion: {occasion}
        - Budget Level: {budget} (e.g., Budget-Friendly, Mid-Range, Luxury, or specific ₹ amount)
        - Interests/Hobbies: {interests}
        - Additional Context: {extra_info if extra_info else "None"}
        
        Suggest exactly 4 high-quality gift ideas that feel thoughtful and personal.
        For each gift, provide:
        1. A catchy 'title'
        2. A sweet 'description' (2 sentences explaining why this is a good fit)
        3. A 'price_estimate' (string with ₹ symbol)
        4. A 'rationale' (1 sentence explaining the emotional impact)
        5. 'category' (e.g., Experience, Physical, Romantic, Practical)
        
        Your response MUST be exclusively valid JSON format, matching this schema:
        [
          {{
            "title": "Gift Name",
            "description": "Why it's great...",
            "price_estimate": "₹...",
            "rationale": "Emotional impact...",
            "category": "..."
          }}
        ]
        
        Do not include any Markdown formatting blocks (e.g. ```json), just output the raw JSON array.
        """
        
        try:
            response = AIGeneratorService._generate_with_fallback(prompt)
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating gift ideas: {error_msg}")
            if "response.text" in error_msg or "blocked" in error_msg.lower():
                raise Exception("AI response was blocked. Please try refining your criteria.")
            raise Exception(f"Gift AI Error: {error_msg}")
