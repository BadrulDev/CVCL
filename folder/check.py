import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("Available models for your API key:\n" + "-" * 40)

# List all models
for m in client.models.list():
    # Filter for models that support content generation
    if hasattr(m, 'supported_actions') and "generateContent" in m.supported_actions:
        print(f"Name: {m.name}")
    elif hasattr(m, 'supported_generation_methods') and "generateContent" in m.supported_generation_methods:
        print(f"Name: {m.name}")
    else:
        # Fallback: print model name directly
        print(f"Name: {m.name}")