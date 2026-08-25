import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

import tools

load_dotenv()

# Initialize Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Provide the PDF generator function as a tool
tools_list = [tools.make_pdf_document]

# Define system instruction
system_prompt = (
    "You are an autonomous AI document publisher. When a user requests a document or report on a topic: "
    "1. Perform research/generation to produce comprehensive, well-structured text with clear paragraphs. "
    "2. Call the `make_pdf_document` tool to compile the PDF. "
    "3. Report back to the user with the file path once complete."
)

chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=tools_list,
        temperature=0.3
    )
)

# Configuration for Free Tier monitoring
DAILY_REQUEST_LIMIT = 1500  # Default Free Tier RPD for Gemini gemini-3.6-flash

def render_usage_bar(current_request_count: int, total_limit: int = DAILY_REQUEST_LIMIT) -> str:
    """Generates a text-based progress bar for API consumption."""
    percentage = min((current_request_count / total_limit) * 100, 100)
    bar_length = 20
    filled_length = int(bar_length * current_request_count // total_limit)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    return f"[{bar}] {percentage:.2f}% ({current_request_count}/{total_limit} RPD)"

# Simulate tracking current request count (you can persist this value in a database or file)
current_requests = 1  

topic = "The Impact of Quantum Computing on Cybersecurity in 2026"

try:
    response = chat.send_message(
        f"Please create a concise report PDF on the topic: '{topic}'. Name the file 'quantum_security.pdf'."
    )
    
    # Render response and usage statistics
    print(response.text)
    print("\n" + "=" * 40)
    print(f"API Usage: {render_usage_bar(current_requests)}")
    
    # Display prompt token details if available
    if response.usage_metadata:
        print(f"Tokens Used - Input: {response.usage_metadata.prompt_token_count} | Output: {response.usage_metadata.candidates_token_count}")
    print("=" * 40)

except APIError as e:
    # 429 Status code triggers when rate/quota limit is exceeded
    if e.code == 429:
        print("\n" + "!" * 50)
        print("⚠️ ALERT: GEMINI API LIMIT REACHED (429 RESOURCE EXHAUSTED)")
        print("Details: You have exceeded your RPM (Requests Per Minute) or RPD (Requests Per Day).")
        print(f"Error Message: {e.message}")
        print("!" * 50)
    else:
        print(f"\nGoogle GenAI API Error occurred: {e}")

except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")