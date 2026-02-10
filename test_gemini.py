import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"API Key found: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")
    
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        return

    try:
        genai.configure(api_key=api_key)
        # Try gemini-flash-latest
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello, this is a test.")
        print(f"Response: {response.text}")
        print("SUCCESS: Gemini API is working correctly with gemini-1.5-flash.")
    except Exception as e:
        print(f"ERROR: Gemini API call failed: {e}")

if __name__ == "__main__":
    test_gemini()
