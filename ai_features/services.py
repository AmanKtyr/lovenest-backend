import os
from django.conf import settings
import google.generativeai as genai
import json

# Configure Gemini API
# Use the recommended model for text generation
MODEL_NAME = "gemini-2.0-flash-lite"

def get_model():
    # Try Django settings first, then direct environment variable
    api_key = getattr(settings, 'GEMINI_API_KEY', None) or os.environ.get("GEMINI_API_KEY")
    
    if not api_key or api_key == 'your_gemini_api_key_here' or len(api_key.strip()) < 10:
        raise ValueError(f"Gemini API Key is not configured properly in .env or settings.py. (Value found: {'SET' if api_key else 'NONE'})")
    
    genai.configure(api_key=api_key.strip())
    return genai.GenerativeModel(MODEL_NAME)

class AIGeneratorService:
    @staticmethod
    def generate_date_ideas(location: str, budget: str, vibe: str, preferences: str = "") -> list:
        """
        Generates personalized date ideas.
        Returns a list of dictionaries with structure:
        [{ "title": str, "description": str, "estimated_cost": str, "vibe": str }]
        """
        model = get_model()
        
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
            response = model.generate_content(prompt)
            # Clean response text in case it contains markdown formatting
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating date ideas: {error_msg}")
            # If it's a safety block or empty response
            if "response.text" in error_msg or "blocked" in error_msg.lower():
                raise Exception("AI response was blocked or empty. Try a different prompt.")
            raise Exception(f"AI Error: {error_msg}")

    @staticmethod
    def relationship_coach_chat(history: list, new_message: str, context: str = "") -> str:
        """
        Chatbot for relationship coaching with strict persona and space awareness.
        history: [{"role": "user"|"model", "parts": ["text"]}]
        context: String containing dashboard info (todos, dates, etc.)
        """
        model = get_model()
        
        system_instruction = f"""
        You are "Cupid", a professional, empathetic, and premium Relationship Coach.
        
        CORE PERSONA:
        - Your expertise is STRICTLY limited to relationships, communication, emotional wellness, and shared life planning.
        - You are warm, non-judgmental, and practical.
        - You use the provided relationship context to give highly personalized and relevant advice.
        
        STRICT BOUNDARIES:
        - If the user asks about ANY topic outside of relationship coaching (e.g., programming/coding, general knowledge, math, science, politics, etc.), you must politely refuse.
        - REJECTION MESSAGE: "As your Relationship Coach, my heart and focus are entirely on your bond. I'm here to help with your love journey, communication, and shared dreams. For [User Topic], a specialist in that field would serve you better. Now, how can I help strengthen your connection today?"
        
        CURRENT RELATIONSHIP CONTEXT:
        {context if context else "No specific context provided yet."}
        
        INSTRUCTIONS:
        1. Always prioritize the well-being of the relationship.
        2. Keep advice concise but meaningful.
        3. If you see upcoming occasions or pending todos in the context, feel free to reference them if relevant to the user's question.
        4. Never break character.
        """
        
        formatted_history = []
        for msg in history:
            formatted_history.append({"role": msg.get("role", "user"), "parts": [msg.get("content", "")]})
            
        try:
            # We use the system_instruction as the first message if history is empty
            # or we can pass it as a preamble. Prepending to the message is safer for all SDK versions.
            
            chat = model.start_chat(history=formatted_history)
            
            if not history:
                prompt = f"{system_instruction}\n\nClient: {new_message}"
            else:
                # Even for subsequent messages, we remind of the context and persona briefly
                prompt = f"(Context Reminder: {context[:500]})\nClient: {new_message}"
                
            response = chat.send_message(prompt)
            return response.text
        except Exception as e:
            error_msg = str(e)
            print(f"Error in relationship coach: {error_msg}")
            raise Exception(f"Cupid Coach AI Error: {error_msg}")

    @staticmethod
    def generate_memory_caption(image_data) -> dict:
        """
        Uses Gemini's Vision capabilities to generate a sweet caption and summary for a couple's photo.
        Returns {"title": str, "description": str}
        """
        # We need the free gemini-1.5-flash which supports multimodal
        model = get_model()
        prompt = "Look at this photo. Generate a short, sweet title (max 5 words) and a heartwarming 2-sentence description for a couple's memory journal. Output strictly valid JSON with keys 'title' and 'description'. Do NOT include any markdown block ticks like ```json, just the JSON string."
        
        try:
            from PIL import Image
            
            # Open the in-memory file
            img = Image.open(image_data)
            
            response = model.generate_content([prompt, img])
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
        Returns a list of dictionaries with gift details.
        """
        model = get_model()
        
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
            response = model.generate_content(prompt)
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating gift ideas: {error_msg}")
            if "response.text" in error_msg or "blocked" in error_msg.lower():
                raise Exception("AI response was blocked. Please try refining your criteria.")
            raise Exception(f"Gift AI Error: {error_msg}")
