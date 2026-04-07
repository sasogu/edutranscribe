from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class QueueItem:
  path: Path
  status: str = "Pendiente"
  text: str = ""
  detected_language: str = ""
  detected_language_probability: float = 0.0
  model_name: str = ""
  segments: list["TranscriptSegment"] | None = None


@dataclass(frozen=True, slots=True)
class TranscriptSegment:
  start: float
  end: float
  text: str


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
  text: str
  model_name: str
  language: str
  language_probability: float
  segments: tuple[TranscriptSegment, ...]


@dataclass(frozen=True, slots=True)
class QualityPreset:
  key: str
  label: str
  description: str


@dataclass(frozen=True, slots=True)
class LanguagePreset:
  key: str
  label: str
  description: str


QUALITY_PRESETS = (
  QualityPreset(
    key="fast",
    label="Rapido",
    description="Menor precision, mejor respuesta y menos consumo. Adecuado para borradores.",
  ),
  QualityPreset(
    key="balanced",
    label="Equilibrado",
    description="Compromiso razonable para la mayoria de equipos.",
  ),
  QualityPreset(
    key="best",
    label="Maxima calidad",
    description="Pensado para usar Whisper grande y tardar mas.",
  ),
)


LANGUAGE_PRESETS = (
  LanguagePreset(
    key="es",
    label="Espanol",
    description="Fuerza la transcripcion en castellano y evita falsas detecciones.",
  ),
  LanguagePreset(
    key="auto",
    label="Auto",
    description="Detecta el idioma automaticamente. Puede fallar con audio ambiguo.",
  ),
  LanguagePreset(
    key="en",
    label="Ingles",
    description="Fuerza la transcripcion en ingles.",
  ),
)
