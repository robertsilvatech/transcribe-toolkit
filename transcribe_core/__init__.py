"""Shared transcription/formatting/slugify logic used by ingestor modules.

This module is intentionally agnostic of input source (YouTube, local files, etc).
Ingestor modules (`yt_transcribe`, `local_transcribe`) import from here; this
module MUST NOT import from any ingestor.
"""

from .formatter import save_outputs
from .slugify import slugify
from .transcriber import transcribe

__all__ = ["transcribe", "save_outputs", "slugify"]
