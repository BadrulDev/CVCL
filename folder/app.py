import os
from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv, set_key

from google import genai
from google.genai import types
from google.genai.errors import APIError
from openai import OpenAI
from anthropic import Anthropic

import tools
import secrets

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(env_path)

base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, "..", "templates")

app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))

tools_list = [tools.make_pdf_document]

system_prompt = (
    "You are an autonomous AI document publisher. When a user requests a report: "
    "1. Perform research to produce structured content. "
    "2. Call `make_pdf_document` to compile the PDF. "
    "3. Confirm the file generation."
)


def get_active_credentials():
    """Reads active provider and API key from session or .env."""
    load_dotenv(env_path, override=True)
    
    provider = session.get("provider") or os.getenv("ACTIVE_PROVIDER", "gemini")
    key_var_name = f"{provider.upper()}_API_KEY"
    
    key = session.get("api_key") or os.getenv(key_var_name)
    
    if key and key.strip():
        return provider, key.strip()
    return provider, None

@app.route("/", methods=["GET"])
def index():
    provider, api_key = get_active_credentials()
    has_key = bool(api_key)
    masked_key = api_key[-3:] if has_key else ""
    return render_template(
        "index.html", 
        has_api_key=has_key, 
        masked_key=masked_key, 
        active_provider=provider.upper()
    )


@app.route("/save-key", methods=["POST"])
def save_key():
    provider = request.form.get("provider", "gemini")
    key = request.form.get("api_key", "").strip()
    
    if key:
        session["provider"] = provider
        session["api_key"] = key
        
        # Save provider and key dynamically to .env
        if not os.path.exists(env_path):
            open(env_path, 'w').close()
            
        set_key(env_path, "ACTIVE_PROVIDER", provider)
        set_key(env_path, f"{provider.upper()}_API_KEY", key)
        os.environ[f"{provider.upper()}_API_KEY"] = key
        
    return redirect(url_for("index"))

@app.route("/clear-key", methods=["GET"])
def clear_key():
    provider = session.get("provider") or os.getenv("ACTIVE_PROVIDER", "gemini")
    key_var = f"{provider.upper()}_API_KEY"
    
    # 1. Clear Flask Session
    session.pop("api_key", None)
    session.pop("provider", None)
    
    # 2. Remove keys from runtime environment
    if key_var in os.environ:
        del os.environ[key_var]
    if "ACTIVE_PROVIDER" in os.environ:
        del os.environ["ACTIVE_PROVIDER"]
        
    # 3. Clear keys from .env file so it won't auto-reload on refresh
    if os.path.exists(env_path):
        set_key(env_path, "ACTIVE_PROVIDER", "")
        set_key(env_path, key_var, "")
        
    return redirect(url_for("index"))

@app.route("/generate", methods=["POST"])
def generate():
    provider, api_key = get_active_credentials()
    topic = request.form.get("topic")
    
    if not api_key:
        return redirect(url_for("index"))

    try:
        if provider == "gemini":
            client = genai.Client(api_key=api_key)
            chat = client.chats.create(
                model="gemini-3.6-flash",
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=tools_list,
                    temperature=0.3
                )
            )
            response = chat.send_message(f"Create a report on: '{topic}'")
            result_text = response.text

        elif provider == "openai":
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Create a report on: '{topic}'"}]
            )
            result_text = response.choices[0].message.content

        elif provider == "anthropic":
            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[{"role": "user", "content": f"Create a report on: '{topic}'"}]
            )
            result_text = response.content[0].text

        masked_key = api_key[-3:]
        return render_template(
            "index.html", 
            has_api_key=True, 
            masked_key=masked_key, 
            active_provider=provider.upper(), 
            result=result_text
        )

    except Exception as e:
        masked_key = api_key[-3:]
        return render_template(
            "index.html", 
            has_api_key=True, 
            masked_key=masked_key, 
            active_provider=provider.upper(), 
            result=f"Error: {str(e)}"
        )

if __name__ == "__main__":
    app.run(debug=True, port=5000)