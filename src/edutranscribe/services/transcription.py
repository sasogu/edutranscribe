from __future__ import annotations

import time
from pathlib import Path

from ..models import QueueItem


class TranscriptionService:
  """Interfaz provisional para el backend real de ASR."""

  def transcribe(self, item: QueueItem, quality: str) -> str:
    time.sleep(0.3)
    file_name = Path(item.path).name
    return (
      f"[demo] Archivo: {file_name}\n"
      f"[demo] Calidad: {quality}\n\n"
      "Aqui ira la transcripcion real cuando conectemos faster-whisper."
    )
