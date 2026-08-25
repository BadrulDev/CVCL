import os
from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv, set_key
from google import genai
from google.genai import types
from google.genai.errors import APIError

import tools

# Load .env file from the root directory
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(env_path)

base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, "..", "templates")

app = Flask(__name__, template_folder=template_dir)
app.secret_key = "super_secret_session_key_change_in_prod"

tools_list = [tools.make_pdf_document]

system_prompt = (
    "You are an autonomous AI document publisher. When a user requests a report: "
    "1. Perform research to produce structured content. "
    "2. Call `make_pdf_document` to compile the PDF. "
    "3. Confirm the file generation."
)

def get_active_api_key():
    """
    Priority:
    1. Check root .env file / os.environ
    2. Check Flask user session (if user manually entered it via web form)
    """
    # Always refresh from .env file first
    load_dotenv(env_path, override=True)
    env_key = os.getenv("GEMINI_API_KEY")
    
    if env_key and env_key.strip():
        return env_key.strip()
    
    session_key = session.get("api_key")
    if session_key and session_key.strip():
        return session_key.strip()
        
    return None

@app.route("/", methods=["GET"])
def index():
    api_key = get_active_api_key()
    has_key = bool(api_key)
    masked_key = api_key[-2:] if has_key else ""
    return render_template("index.html", has_api_key=has_key, masked_key=masked_key)

@app.route("/save-key", methods=["POST"])
def save_key():
    key = request.form.get("api_key", "").strip()
    if key:
        # Create .env if missing and write the key
        if not os.path.exists(env_path):
            open(env_path, 'w').close()
        set_key(env_path, "GEMINI_API_KEY", key)
        os.environ["GEMINI_API_KEY"] = key
        session["api_key"] = key
    return redirect(url_for("index"))

@app.route("/clear-key", methods=["GET"])
def clear_key():
    # Optional: clears session and removes from runtime env
    session.pop("api_key", None)
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]
    return redirect(url_for("index"))

@app.route("/generate", methods=["POST"])
def generate():
    api_key = get_active_api_key()
    
    if not api_key:
        return redirect(url_for("index"))

    topic = request.form.get("topic")
    
    try:
        client = genai.Client(api_key=api_key)
        
        chat = client.chats.create(
            model="gemini-3.6-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=tools_list,
                temperature=0.3
            )
        )
        
        response = chat.send_message(
            f"Please create a concise report PDF on the topic: '{topic}'."
        )
        
        masked_key = api_key[-2:]
        return render_template("index.html", has_api_key=True, masked_key=masked_key, result=response.text)

    except APIError as e:
        masked_key = api_key[-2:]
        return render_template("index.html", has_api_key=True, masked_key=masked_key, result=f"API Error: {e.message}")

if __name__ == "__main__":
    app.run(debug=True, port=5000)