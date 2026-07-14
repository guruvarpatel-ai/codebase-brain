import os
from dotenv import load_dotenv


def get_config():
    """Load from local .env first, then global ~/.codebase-brain/config.env"""
    local_env = os.path.join(os.getcwd(), '.env')
    if os.path.exists(local_env):
        load_dotenv(local_env, override=True)

    # check if local .env actually had Brain's keys
    has_key = os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY")

    if not has_key:
        # local .env didn't have Brain's config — fall back to global
        global_config = os.path.expanduser("~/.codebase-brain/config.env")
        if os.path.exists(global_config):
            load_dotenv(global_config, override=True)

    return {
        'provider': os.getenv("LLM_PROVIDER", "groq").lower(),
        'api_key': os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY"),
        'model': os.getenv("LLM_MODEL") or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    }


def call_llm(prompt, max_tokens=500):
    config = get_config()
    provider = config['provider']
    api_key = config['api_key']
    model = config['model']

    if provider == "groq":
        return _call_groq(api_key, model, prompt, max_tokens)
    elif provider == "openai":
        return _call_openai(api_key, model, prompt, max_tokens)
    elif provider == "anthropic":
        return _call_anthropic(api_key, model, prompt, max_tokens)
    elif provider == "google":
        return _call_google(api_key, model, prompt, max_tokens)
    elif provider == "ollama":
        return _call_ollama(model, prompt, max_tokens)
    else:
        return _call_groq(api_key, model, prompt, max_tokens)


def _call_groq(api_key, model, prompt, max_tokens):
    from groq import Groq
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0
    )
    return response.choices[0].message.content


def _call_openai(api_key, model, prompt, max_tokens):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0
    )
    return response.choices[0].message.content


def _call_anthropic(api_key, model, prompt, max_tokens):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def _call_google(api_key, model, prompt, max_tokens):
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    gemini = genai.GenerativeModel(model)
    response = gemini.generate_content(prompt)
    return response.text


def _call_ollama(model, prompt, max_tokens):
    import requests
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False}
    )
    return response.json().get("response", "")