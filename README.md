# EduTranscribe

Aplicacion de escritorio local para transcripcion de audio y video con `PySide6` y `faster-whisper`.

## Caracteristicas

- Arrastrar y soltar audio o video en una cola local
- Transcripcion offline con `faster-whisper`
- Selector de calidad: `Rapido`, `Equilibrado`, `Maxima calidad`
- Selector de idioma: `Espanol`, `Auto`, `Ingles`
- Barra de progreso y consola visual del proceso
- Copiado rapido del resultado al portapapeles
- Cancelacion de la transcripcion en curso
- Exportacion a `.txt`, `.md`, `.srt` y `.vtt`

## Estado actual

La app ya incluye:

- ventana principal
- cola de archivos
- control de idioma
- progreso en tiempo real
- transcripcion real con `faster-whisper`
- exportacion de resultados y subtitulos

## Requisitos

- Python 3.11+
- `ffmpeg` disponible en el sistema

## Instalacion

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

## Uso

```bash
source .venv/bin/activate
edutranscribe
```

La primera transcripcion descargara el modelo necesario segun la calidad elegida.
Si el backend no puede abrir audio o video, instala `ffmpeg` en el sistema.

## Flujo de uso

1. Anade uno o varios archivos a la cola.
2. Elige calidad e idioma.
3. Pulsa `Transcribir seleccion`.
4. Revisa el progreso y la consola visual.
5. Copia el texto o exportalo a `.txt`, `.md`, `.srt` o `.vtt`.

## Backend ASR

- `Rapido`: `Systran/faster-whisper-small`
- `Equilibrado`: `Systran/faster-whisper-small`
- `Maxima calidad`: `Systran/faster-whisper-medium`

El servicio usa carga perezosa y reutiliza cada modelo una vez inicializado.

## Exportacion

- `.txt`: texto plano
- `.md`: transcripcion con metadatos y segmentos
- `.srt`: subtitulos SubRip
- `.vtt`: subtitulos WebVTT

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta [LICENSE](LICENSE).
