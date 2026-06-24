import json
from datetime import datetime, timezone
from pathlib import Path


def _seconds_to_hms(seconds: float) -> str:
    total = int(seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def save_outputs(
    output_dir: Path,
    folder_name: str,
    result: dict,
    metadata: dict,
    model_used: str,
) -> Path:
    """
    Cria a pasta de output e salva os 4 arquivos raw.

    Args:
        output_dir: Diretório base configurado via --output
        folder_name: Nome da pasta (YYYY-MM-DD_slug)
        result: Resposta verbose do Whisper (text, segments, language)
        metadata: Dict com campos da origem (ex: title, source, url, channel,
            source_path, duration_seconds, language). Propagado verbatim para
            meta.json, exceto `language` que é resolvido pelo result.
        model_used: String identificando o modelo/engine usado

    Returns:
        Caminho da pasta criada
    """
    dest = output_dir / folder_name
    dest.mkdir(parents=True, exist_ok=True)

    segments = result.get("segments", [])
    language = result.get("language") or metadata.get("language") or "unknown"

    # raw.md — texto limpo sem timestamps (fiel ao output do Whisper)
    raw_text = result.get("text", "").strip()
    (dest / "raw.md").write_text(raw_text, encoding="utf-8")

    # raw_timestamps.md — cada segmento prefixado com [HH:MM:SS] e, no modo
    # multilang, [<lang>]. A marcação de idioma só aparece quando o segmento
    # tem o campo `language` (transcribe_core preenche apenas no modo chunked
    # com re-detecção por janela), permitindo revisar visualmente trocas de
    # idioma em reuniões mistas (PT/EN/ES).
    lines = []
    for seg in segments:
        ts = _seconds_to_hms(seg.get("start", 0))
        text = seg.get("text", "").strip()
        if not text:
            continue
        seg_lang = seg.get("language")
        if seg_lang:
            lines.append(f"[{ts}] [{seg_lang}] {text}")
        else:
            lines.append(f"[{ts}] {text}")
    (dest / "raw_timestamps.md").write_text("\n".join(lines), encoding="utf-8")

    # raw_whisper.json — resposta completa do Whisper (source of truth)
    (dest / "raw_whisper.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # meta.json — propaga metadata da origem + adiciona campos da transcrição
    meta = dict(metadata)
    meta["language"] = language
    meta["transcribed_at"] = datetime.now(timezone.utc).isoformat()
    meta["model_used"] = model_used
    (dest / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return dest
