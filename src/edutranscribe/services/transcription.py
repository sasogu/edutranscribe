from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from shutil import which

from ..models import QueueItem, TranscriptionResult, TranscriptSegment


@dataclass(frozen=True, slots=True)
class ModelConfig:
  model_size: str
  compute_type: str
  beam_size: int
  vad_filter: bool = True
  language: str | None = None


QUALITY_CONFIGS: dict[str, ModelConfig] = {
  "fast": ModelConfig(
    model_size="Systran/faster-whisper-small",
    compute_type="int8",
    beam_size=1,
  ),
  "balanced": ModelConfig(
    model_size="Systran/faster-whisper-small",
    compute_type="int8",
    beam_size=3,
  ),
  "best": ModelConfig(
    model_size="Systran/faster-whisper-medium",
    compute_type="float32",
    beam_size=5,
  ),
}


class TranscriptionService:
  def __init__(self) -> None:
    self._models: dict[str, object] = {}

  def _get_model(self, quality: str):
    try:
      config = QUALITY_CONFIGS[quality]
    except KeyError as exc:
      raise ValueError(f"Calidad no soportada: {quality}") from exc

    cached_model = self._models.get(quality)
    if cached_model is not None:
      return cached_model, config

    try:
      from faster_whisper import WhisperModel
    except ImportError as exc:
      raise RuntimeError(
        "Falta la dependencia 'faster-whisper'. Ejecuta 'pip install -e .' o "
        "'pip install faster-whisper'."
      ) from exc

    try:
      model = WhisperModel(
        config.model_size,
        device="auto",
        compute_type=config.compute_type,
      )
    except Exception as exc:
      raise RuntimeError(
        "No se pudo inicializar el modelo de transcripcion. Verifica la descarga "
        "del modelo y que el entorno tenga dependencias nativas compatibles."
      ) from exc

    self._models[quality] = model
    return model, config

  def transcribe(
    self,
    item: QueueItem,
    quality: str,
    language: str | None = None,
    progress_callback=None,
    status_callback=None,
    is_cancelled=None,
  ) -> TranscriptionResult:
    path = Path(item.path).expanduser().resolve()
    if not path.exists() or not path.is_file():
      raise FileNotFoundError(f"Archivo no encontrado: {path}")

    self._raise_if_cancelled(is_cancelled)
    if status_callback is not None:
      status_callback("Preparando archivo")

    model, config = self._get_model(quality)
    self._raise_if_cancelled(is_cancelled)
    if status_callback is not None:
      status_callback(f"Modelo listo: {config.model_size}")

    try:
      segments, info = model.transcribe(
        str(path),
        beam_size=config.beam_size,
        vad_filter=config.vad_filter,
        language=language if language is not None else config.language,
      )
    except FileNotFoundError as exc:
      if which("ffmpeg") is None:
        raise RuntimeError(
          "No se pudo abrir el archivo multimedia. Instala 'ffmpeg' y vuelve a intentarlo."
        ) from exc
      raise
    except Exception as exc:
      raise RuntimeError(f"Error al transcribir '{path.name}': {exc}") from exc

    if status_callback is not None:
      status_callback("Procesando segmentos")

    duration = max(float(getattr(info, "duration", 0.0) or 0.0), 0.0)
    text_parts: list[str] = []
    collected_segments: list[TranscriptSegment] = []
    last_percent = -1
    for segment in segments:
      self._raise_if_cancelled(is_cancelled)

      text = segment.text.strip()
      if text:
        text_parts.append(text)
        collected_segments.append(
          TranscriptSegment(
            start=float(segment.start),
            end=float(segment.end),
            text=text,
          )
        )

      if progress_callback is not None and duration > 0:
        percent = min(int((segment.end / duration) * 100), 100)
        if percent != last_percent:
          progress_callback(percent, f"Segmento {segment.start:.1f}s -> {segment.end:.1f}s")
          last_percent = percent

    if not text_parts:
      raise RuntimeError("La transcripcion no produjo texto util.")

    if progress_callback is not None and last_percent < 100:
      progress_callback(100, "Segmentos completados")

    if status_callback is not None:
      status_callback("Generando salida final")

    header = [
      f"Archivo: {path.name}",
      f"Modelo: {config.model_size}",
      f"Idioma detectado: {info.language}",
      f"Probabilidad idioma: {info.language_probability:.2f}",
      "",
    ]
    return TranscriptionResult(
      text="\n".join(header + text_parts),
      model_name=config.model_size,
      language=str(info.language),
      language_probability=float(info.language_probability),
      segments=tuple(collected_segments),
    )

  @staticmethod
  def _raise_if_cancelled(is_cancelled) -> None:
    if is_cancelled is not None and is_cancelled():
      raise RuntimeError("Transcripcion cancelada por el usuario.")
