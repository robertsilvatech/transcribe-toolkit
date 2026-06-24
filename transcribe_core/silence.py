"""Detecção e remoção de silêncios longos usando ffmpeg.

Caso real: gravações de reunião onde ninguém parou a gravação. Ex: KT
de 1h30 num MP4 de 4h — as 2h30 finais são sala vazia. O áudio puro alimentado
no Whisper causa duas dores:

1. Hallucinations recorrentes ("Legenda Adriana Zanotto") em janelas silenciosas.
2. Custo de decode desperdiçado em milhares de janelas vazias.

Estratégia: usa o filtro `silencedetect` do ffmpeg pra mapear regiões silenciosas
acima de `min_silence_seconds`, identifica quais tocam o início ou o fim do
arquivo, e refatora com `-ss`/`-to` cortando só essas duas pontas. Silêncios no
meio do áudio são preservados pra não bagunçar os timestamps dos segmentos
intermediários (eles permanecem alinhados ao tempo original quando o
`leading_offset` é somado ao Whisper output).
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


# Tolerância pra considerar que um silêncio "encosta" no início ou fim do
# arquivo. Inclui margens de detecção do silencedetect (subframe drift) e
# eventuais zeros de padding.
_EDGE_TOLERANCE_SECONDS = 1.0


@dataclass(frozen=True)
class SilenceTrimResult:
    """Resultado de uma operação de trim de silêncio.

    Attributes:
        audio_path: Caminho do áudio resultante (pode ser o original se nada
            precisou ser cortado).
        leading_offset_seconds: Segundos cortados do início. Deve ser somado a
            todos os timestamps do Whisper pra mapear de volta ao tempo
            original do vídeo.
        original_duration_seconds: Duração total do áudio antes do trim.
        trimmed_duration_seconds: Duração do áudio depois do trim.
    """

    audio_path: Path
    leading_offset_seconds: float
    original_duration_seconds: float
    trimmed_duration_seconds: float

    @property
    def was_trimmed(self) -> bool:
        return self.audio_path != Path(self.audio_path) or (
            self.original_duration_seconds - self.trimmed_duration_seconds
            > _EDGE_TOLERANCE_SECONDS
        )


def _audio_duration_seconds(audio_path: Path) -> float:
    """Duração total do arquivo de áudio (segundos), via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nokey=1:noprint_wrappers=1",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def detect_silences(
    audio_path: Path,
    min_seconds: float,
    threshold_db: float = -40.0,
) -> list[tuple[float, float]]:
    """Roda `ffmpeg silencedetect` e retorna lista de (start, end) em segundos
    para cada região silenciosa com duração >= `min_seconds` e amplitude
    <= `threshold_db`. As mensagens do filtro vão pro stderr do ffmpeg.
    """
    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(audio_path),
            "-af",
            f"silencedetect=n={threshold_db}dB:d={min_seconds}",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
    )

    silences: list[tuple[float, float]] = []
    cur_start: float | None = None
    for line in proc.stderr.splitlines():
        m_start = re.search(r"silence_start:\s*([\d.]+)", line)
        if m_start:
            cur_start = float(m_start.group(1))
            continue
        m_end = re.search(r"silence_end:\s*([\d.]+)", line)
        if m_end and cur_start is not None:
            silences.append((cur_start, float(m_end.group(1))))
            cur_start = None
    return silences


def trim_leading_trailing_silence(
    audio_path: Path,
    min_silence_seconds: float,
    threshold_db: float = -40.0,
) -> SilenceTrimResult:
    """Corta silêncio inicial e/ou final acima de `min_silence_seconds`.

    Silêncios intermediários são preservados pra não embaralhar timestamps. Se
    nenhum trim for necessário (ou nenhum silêncio nas bordas), retorna o
    `audio_path` original sem reescrever nada.

    O arquivo cortado vai pro diretório temporário do sistema pra evitar
    poluir a pasta da fonte (OneDrive, Downloads, etc).
    """
    original_duration = _audio_duration_seconds(audio_path)
    silences = detect_silences(audio_path, min_silence_seconds, threshold_db)

    leading = 0.0
    trailing_cut_at = original_duration

    for start, end in silences:
        # silêncio "no início" — encosta em t=0 (com tolerância)
        if start <= _EDGE_TOLERANCE_SECONDS and end > leading:
            leading = end
        # silêncio "no fim" — termina em (ou perto de) total_duration
        if (
            end >= original_duration - _EDGE_TOLERANCE_SECONDS
            and start < trailing_cut_at
        ):
            trailing_cut_at = start

    cut_anything = (
        leading > _EDGE_TOLERANCE_SECONDS
        or trailing_cut_at < original_duration - _EDGE_TOLERANCE_SECONDS
    )
    if not cut_anything:
        return SilenceTrimResult(
            audio_path=audio_path,
            leading_offset_seconds=0.0,
            original_duration_seconds=original_duration,
            trimmed_duration_seconds=original_duration,
        )

    tmp_dir = Path(tempfile.gettempdir())
    output = tmp_dir / f"{audio_path.stem}.trimmed{audio_path.suffix}"

    # `-ss`/`-to` ANTES de `-i` faz input seek (rápido). Com `-c copy` evita
    # re-encoding — para mp3 a precisão é frame-level (~26ms), aceitável aqui.
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{leading:.3f}",
            "-to",
            f"{trailing_cut_at:.3f}",
            "-i",
            str(audio_path),
            "-c",
            "copy",
            str(output),
        ],
        check=True,
    )

    return SilenceTrimResult(
        audio_path=output,
        leading_offset_seconds=leading,
        original_duration_seconds=original_duration,
        trimmed_duration_seconds=trailing_cut_at - leading,
    )


def shift_segments(result: dict, offset_seconds: float) -> None:
    """Soma `offset_seconds` aos campos `start`/`end` de todos os segmentos
    (in-place). Usado depois de transcrever áudio com leading silence cortado
    pra que os timestamps batam com o vídeo original.
    """
    if offset_seconds == 0:
        return
    for seg in result.get("segments", []):
        if "start" in seg:
            seg["start"] = seg["start"] + offset_seconds
        if "end" in seg:
            seg["end"] = seg["end"] + offset_seconds
