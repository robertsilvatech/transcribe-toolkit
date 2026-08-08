import os
from pathlib import Path

MAX_TEXT_CHARS = 300_000

PROMPT_PATH = Path(__file__).resolve().parent / "prompt.md"


def _load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _get_api_key(api_key_env: str) -> str:
    key = os.environ.get(api_key_env)
    if not key:
        raise EnvironmentError(
            f"{api_key_env} não encontrada. "
            f"Defina a variável de ambiente ou adicione ao arquivo .env."
        )
    return key


def _generate_openai(text: str, model: str, system_prompt: str, api_key: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise RuntimeError("Resposta vazia da API OpenAI.")
    return content


def _generate_anthropic(text: str, model: str, system_prompt: str, api_key: str) -> str:
    from anthropic import Anthropic

    max_tokens = 64000
    client = Anthropic(api_key=api_key)
    # Nota: sem `temperature` — modelos Claude Sonnet 5+ rejeitam valores
    # não-default de temperature/top_p/top_k com erro 400.
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[
            {"role": "user", "content": text},
        ],
    ) as stream:
        response = stream.get_final_message()
    if response.stop_reason == "max_tokens":
        raise RuntimeError(
            f"Material truncado: API atingiu max_tokens={max_tokens:,} "
            f"com input de {len(text):,} caracteres. "
            "Aula provavelmente longa demais pra uma chamada única."
        )
    # Com thinking adaptativo (default no Sonnet 5+), content[0] pode ser um
    # ThinkingBlock — pega o primeiro bloco de texto.
    content = next((b.text for b in response.content if b.type == "text"), "")
    if not content or not content.strip():
        raise RuntimeError("Resposta vazia da API Anthropic.")
    return content


def _strip_markdown_fence(content: str) -> str:
    """Remove um fence ```markdown externo, se o modelo embrulhar o documento
    inteiro nele (instrução antiga do prompt; modelos às vezes ainda fazem).
    """
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines[0].startswith("```") and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip() + "\n"
    return content


def generate_study_material(
    text: str,
    provider: str,
    model: str,
    api_key_env: str,
) -> str:
    if not text.strip():
        raise ValueError("Transcrição vazia.")

    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"Texto tem {len(text):,} caracteres (limite: {MAX_TEXT_CHARS:,}). "
            "Texto pode ser grande demais pra geração em uma chamada."
        )

    api_key = _get_api_key(api_key_env)
    system_prompt = _load_system_prompt()

    if provider == "openai":
        content = _generate_openai(text, model, system_prompt, api_key)
    elif provider == "anthropic":
        content = _generate_anthropic(text, model, system_prompt, api_key)
    else:
        raise ValueError(f"Provider desconhecido: {provider}. Use 'openai' ou 'anthropic'.")

    return _strip_markdown_fence(content)
