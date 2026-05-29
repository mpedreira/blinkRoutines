# blinkRoutines Agents

Servicio FastAPI para deteccion y entrenamiento facial desde video usando DeepFace + ffmpeg.

## Endpoints

- `GET /health`
- `GET /api/v2/list_faces`
- `POST /api/v2/register_face/{person_name}`
  - multipart/form-data: `video` (archivo)
  - opcional: `sample_fps` (float)
- `POST /api/v2/register_face_image/{person_name}`
  - multipart/form-data: `image` (archivo)
- `POST /api/v2/detect_person`
  - multipart/form-data: `video` (archivo)
  - opcional: `sample_fps` (float)
  - opcional: `min_confidence` (0-100)
- `POST /api/v2/detect_person_image`
  - multipart/form-data: `image` (archivo)
  - opcional: `min_confidence` (0-100)

## Ejecutar con Docker

```bash
cd agents
docker compose up --build
```

Servicio disponible en `http://localhost:8010`.

## Persistencia

Los embeddings se guardan en `agents/data/faces/*.json` (volumen montado en `/data`).
