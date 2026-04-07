# EduTranscribe

Aplicacion de escritorio local para transcripcion de audio y video con `PySide6`.

## Objetivo

- Mantener una UX simple de arrastrar y soltar
- Ejecutar la transcripcion localmente
- Preparar la integracion con `faster-whisper`
- Soportar macOS y Linux desde la misma base

## Estado

Scaffold inicial con:

- ventana principal
- cola de archivos
- selector de calidad
- panel de salida
- servicio de transcripcion simulado

## Arranque

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
edutranscribe
```

## Estructura

```text
.
├── pyproject.toml
├── README.md
└── src/edutranscribe
```

Este directorio ya no depende de vivir embebido en otro proyecto.

## Siguiente paso tecnico

Sustituir el servicio simulado por un backend con `faster-whisper` y `ffmpeg`.
