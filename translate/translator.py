import os

MAX_TEXT_CHARS = 300_000

SYSTEM_PROMPT = """You are a professional translator. Translate the following text to {target_lang}.

Rules:
- Maintain the original tone and style (conversational, technical, etc.)
- Keep technical jargon that is commonly used in the original language in the tech community (e.g., "API", "framework", "deploy", "prompt")
- Produce natural, fluent text — not a literal word-by-word translation
- Do NOT add explanations, notes, or commentary — only output the translated text
- Preserve paragraph breaks and formatting
- Break the translated text into natural paragraphs separated by blank lines"""


def _get_api_key(api_key_env: str) -> str:
    key = os.environ.get(api_key_env)
    if not key:
        raise EnvironmentError(
            f"{api_key_env} não encontrada. "
            f"Defina a variável de ambiente ou adicione ao arquivo .env."
        )
    return key


def _translate_openai(text: str, model: str, target_lang: str, api_key: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(target_lang=target_lang)},
            {"role": "user", "content": text},
        ],
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise RuntimeError("Resposta vazia da API OpenAI.")
    return content


def _translate_anthropic(text: str, model: str, target_lang: str, api_key: str) -> str:
    from anthropic import Anthropic

    max_tokens = 64000
    client = Anthropic(api_key=api_key)
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        temperature=0,
        system=SYSTEM_PROMPT.format(target_lang=target_lang),
        messages=[
            {"role": "user", "content": text},
        ],
    ) as stream:
        response = stream.get_final_message()
    if response.stop_reason == "max_tokens":
        raise RuntimeError(
            f"Tradução truncada: API atingiu max_tokens={max_tokens:,} "
            f"com input de {len(text):,} caracteres. "
            "Vídeo provavelmente excede ~3h e precisa ser quebrado em pedaços menores."
        )
    content = response.content[0].text
    if not content or not content.strip():
        raise RuntimeError("Resposta vazia da API Anthropic.")
    return content


def translate_text(
    text: str,
    provider: str,
    model: str,
    target_lang: str,
    api_key_env: str,
) -> str:
    if not target_lang or not target_lang.strip():
        raise ValueError("Idioma alvo (target_lang) é obrigatório.")

    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"Texto tem {len(text):,} caracteres (limite: {MAX_TEXT_CHARS:,}). "
            "Texto pode ser grande demais para tradução em uma chamada."
        )

    api_key = _get_api_key(api_key_env)

    if provider == "openai":
        return _translate_openai(text, model, target_lang, api_key)
    elif provider == "anthropic":
        return _translate_anthropic(text, model, target_lang, api_key)
    else:
        raise ValueError(f"Provider desconhecido: {provider}. Use 'openai' ou 'anthropic'.")
