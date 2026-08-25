import os
from flask import Flask, render_template, request
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

import tools

load_dotenv()

base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, "..", "templates")

app = Flask(__name__, template_folder=template_dir)

# Initialize Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

tools_list = [tools.make_pdf_document]

system_prompt = (
    "You are an autonomous AI document publisher. When a user requests a report: "
    "1. Perform research to produce structured content. "
    "2. Call `make_pdf_document` to compile the PDF. "
    "3. Confirm the file generation."
)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    topic = request.form.get("topic")
    
    chat = client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=tools_list,
            temperature=0.3
        )
    )

    DAILY_REQUEST_LIMIT = 1500  # Default Free Tier RPD for Gemini gemini-3.6-flash
        
    # Prompt Gemini with user-submitted topic
    response = chat.send_message(
        f"Please create a concise report PDF on the topic: '{topic}'."
    )
    
    return render_template("index.html", result=response.text)

if __name__ == "__main__":
    app.run(debug=True, port=5000)