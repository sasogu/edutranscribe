from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class QueueItem:
  path: Path
  status: str = "Pendiente"
  text: str = ""


@dataclass(frozen=True, slots=True)
class QualityPreset:
  key: str
  label: str
  description: str


QUALITY_PRESETS = (
  QualityPreset(
    key="fast",
    label="Rapido",
    description="Menor precision, mejor respuesta y menos consumo.",
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
