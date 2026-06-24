import anthropic
import openai
from settings import load_settings
from providers import PROVIDER_BY_ID, DEFAULT_PROVIDER_ID

def build_prompt(code: str, language: str) -> str:
    if language == "zh":
        return f"""你是一個幫助非工程師理解程式碼的助手。
請用繁體中文，以簡單易懂的方式解釋以下程式碼：
1. 這段 code 在做什麼（一句話總結）
2. 它的邏輯是怎麼運作的（步驟說明）
3. 如果有關鍵概念，用生活化的比喻解釋

程式碼：
{code}

請用自然語言回答，不要用技術術語，假設讀者完全不懂程式。"""
    else:
        return f"""You are an assistant helping non-engineers understand code.
Please explain the following code in simple English:
1. What this code does (one sentence summary)
2. How the logic works (step by step)
3. Use everyday analogies for any key concepts

Code:
{code}

Use natural language. Assume the reader has zero coding knowledge."""

_HTTP_TIMEOUT = 25  # seconds

def _call_anthropic(api_key: str, model: str, prompt: str) -> str:
    client = anthropic.Anthropic(api_key=api_key, timeout=_HTTP_TIMEOUT)
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text

def _call_openai(api_key: str, model: str, prompt: str, base_url: str | None = None,
                 extra_headers: dict | None = None) -> str:
    kwargs = {"api_key": api_key, "timeout": _HTTP_TIMEOUT}
    if base_url:
        kwargs["base_url"] = base_url
    if extra_headers:
        kwargs["default_headers"] = extra_headers
    client = openai.OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )
    return response.choices[0].message.content

def explain_code(code: str) -> str:
    settings = load_settings()
    provider_id = settings.get("provider", DEFAULT_PROVIDER_ID)
    api_key = "".join(settings.get("api_key", "").split())  # strip all whitespace defensively
    language = settings.get("language", "en")

    provider = PROVIDER_BY_ID.get(provider_id)
    if not provider:
        return ("⚠️ Unsupported provider" if language == "en"
                else "⚠️ 不支援的 Provider")

    if provider.get("requires_key", True) and not api_key:
        return ("⚠️ Please enter your API Key in Settings first"
                if language == "en"
                else "⚠️ 請先在設定中填入 API Key")

    prompt = build_prompt(code, language)

    try:
        ptype = provider["type"]
        model = settings.get("model") or provider["model"]

        if ptype == "anthropic":
            return _call_anthropic(api_key, model, prompt)

        if ptype == "openai":
            return _call_openai(api_key, model, prompt)

        if ptype == "openai_compatible":
            key = api_key or "ollama"
            return _call_openai(
                key,
                model,
                prompt,
                base_url=provider["base_url"],
                extra_headers=provider.get("extra_headers"),
            )

        return ("⚠️ Unsupported provider" if language == "en"
                else "⚠️ 不支援的 Provider")

    except Exception as e:
        return (f"❌ Error: {e}" if language == "en"
                else f"❌ 發生錯誤：{e}")
