"""Worker standalone de transcrição via WhisperX (faster-whisper/CTranslate2).

Roda num interpretador SEPARADO do venv do projeto: whisperx exige Python
>=3.10,<3.14 (torch não publica wheels cp314) e o venv do toolkit está em
3.14+. O transcriber invoca este arquivo via
`uv run --no-project --python 3.12 --with whisperx`, que resolve um ambiente
efêmero cacheado pelo uv — por isso este script NÃO pode importar nada do
toolkit nem depender do venv do projeto.

Por que WhisperX e não mlx-whisper: o backend CTranslate2 (faster-whisper)
com quantização int8 + VAD pyannote (pré-segmenta o áudio em trechos de fala
e decodifica em batch, pulando silêncio) é rápido em CPU — competitivo com a
GPU do mlx em Apple Silicon — e o VAD elimina na origem as alucinações de
silêncio que o engine mlx combate com kwargs de decodificação.

Com --word-timestamps, roda uma segunda passada de alinhamento forçado
(wav2vec2 por idioma): as bordas de cada palavra são MEDIDAS contra a forma
de onda, não inferidas pela atenção do decoder — timestamps de palavra muito
mais precisos que os do Whisper puro. Sem a flag, o alinhamento é pulado
(mais rápido) e os segments saem direto do faster-whisper.

Escreve em --output um JSON com o mesmo shape que o formatter consome:
{text, segments: [{id, start, end, text, words?}], language}.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BATCH_SIZE = 8


def _device() -> tuple[str, str]:
    """CTranslate2 não tem caminho Metal: em Apple Silicon roda CPU/int8
    (pedir 'mps' falha no load em vez de cair pra CPU)."""
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


def _fill_word_bounds(words: list[dict], seg_start: float, seg_end: float) -> list[dict]:
    """Palavras fora do dicionário de alinhamento ("2014.", "R$13,60") voltam
    sem start/end. Herdam a borda do vizinho em vez de serem dropadas, pra
    nenhuma palavra sumir do transcript."""
    out = []
    for w in words:
        text = (w.get("word") or "").strip()
        if not text:
            continue
        entry = {"word": text, "start": w.get("start"), "end": w.get("end")}
        if w.get("score") is not None:
            entry["score"] = w["score"]
        out.append(entry)
    for i, w in enumerate(out):
        if w["start"] is None:
            w["start"] = next(
                (out[j]["end"] for j in range(i - 1, -1, -1) if out[j]["end"] is not None),
                seg_start,
            )
        if w["end"] is None:
            w["end"] = next(
                (out[j]["start"] for j in range(i + 1, len(out)) if out[j]["start"] is not None),
                seg_end,
            )
        w["start"] = float(w["start"])
        w["end"] = float(max(w["end"], w["start"]))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Transcreve um áudio com WhisperX e emite JSON verbose")
    ap.add_argument("audio", type=Path)
    ap.add_argument("--output", type=Path, required=True, help="Arquivo JSON de saída")
    ap.add_argument("--model", default="large-v3-turbo")
    ap.add_argument("--language", default=None, help="ISO-639-1 (pt, en, es). Omitir = auto-detect")
    ap.add_argument("--word-timestamps", action="store_true")
    args = ap.parse_args()

    if not args.audio.exists():
        sys.exit(f"áudio não encontrado: {args.audio}")

    try:
        import whisperx
    except ImportError:
        sys.exit(
            "whisperx não disponível no ambiente do worker — este script deve "
            "rodar via `uv run --no-project --python 3.12 --with whisperx`."
        )

    device, compute_type = _device()
    print(f"  [whisperx] {device}/{compute_type}, modelo {args.model}", flush=True)

    audio = whisperx.load_audio(str(args.audio))
    model = whisperx.load_model(
        args.model, device, compute_type=compute_type, language=args.language
    )
    result = model.transcribe(audio, batch_size=BATCH_SIZE, language=args.language)
    language = result.get("language") or args.language
    print(f"  [whisperx] idioma: {language or '?'}", flush=True)

    segments = result.get("segments", [])

    if args.word_timestamps and segments:
        # Alinhamento forçado: só quando pedido — é uma segunda passada
        # (wav2vec2) e o modelo de alinhamento é por idioma.
        try:
            align_model, metadata = whisperx.load_align_model(
                language_code=language, device=device
            )
            aligned = whisperx.align(
                segments, align_model, metadata, audio, device,
                return_char_alignments=False,
            )
            segments = aligned.get("segments", segments)
            print("  [whisperx] alinhamento forçado ok", flush=True)
        except Exception as e:
            # Sem modelo wav2vec2 pro idioma: os tempos de segment do Whisper
            # continuam valendo, mas não há words — avisa em vez de fingir.
            print(
                f"  [whisperx] AVISO: alinhamento indisponível pra '{language}' "
                f"({e}); segments sem words",
                file=sys.stderr,
                flush=True,
            )

    out_segments = []
    text_parts: list[str] = []
    for i, seg in enumerate(segments):
        text = (seg.get("text") or "").strip()
        start = float(seg.get("start") or 0.0)
        end = float(seg.get("end") or start)
        entry: dict = {"id": i, "start": start, "end": end, "text": text}
        if args.word_timestamps and seg.get("words"):
            entry["words"] = _fill_word_bounds(seg["words"], start, end)
        out_segments.append(entry)
        if text:
            text_parts.append(text)

    payload = {
        "text": " ".join(text_parts).strip(),
        "segments": out_segments,
        "language": language,
    }
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  [whisperx] {len(out_segments)} segments", flush=True)


if __name__ == "__main__":
    main()
