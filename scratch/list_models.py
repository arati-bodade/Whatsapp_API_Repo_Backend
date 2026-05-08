import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load .env from backend directory
load_dotenv('c:/Users/susha/Desktop/git clone/whatsapp-platform-api-backend/.env')

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("No GEMINI_API_KEY found in .env")
else:
    try:
        genai.configure(api_key=api_key)
        print("Listing available Gemini models...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Model: {m.name}")
    except Exception as e:
        print(f"Error: {e}")
