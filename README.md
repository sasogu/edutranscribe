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
- transcripcion real con `faster-whisper`

## Arranque

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
edutranscribe
```

La primera transcripcion descargara el modelo necesario segun la calidad elegida.
Si el backend no puede abrir audio o video, instala `ffmpeg` en el sistema.

## Estructura

```text
.
├── pyproject.toml
├── README.md
└── src/edutranscribe
```

Este directorio ya no depende de vivir embebido en otro proyecto.

## Backend ASR

- `Rapido`: `Systran/faster-distil-whisper-small.en`
- `Equilibrado`: `Systran/faster-whisper-small`
- `Maxima calidad`: `Systran/faster-whisper-medium`

El servicio usa carga perezosa y reutiliza cada modelo una vez inicializado.
