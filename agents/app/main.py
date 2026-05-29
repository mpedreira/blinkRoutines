"""FastAPI service for DeepFace video training and detection."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from .services.deepface_service import extract_embedding, find_best_match
from .services.face_store import FaceStore
from .services.video_processing import FFmpegError, extract_frames

_LOCAL_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR = os.getenv("AGENTS_DATA_DIR", str(_LOCAL_DATA_DIR))
TMP_DIR = os.getenv("AGENTS_TMP_DIR", "/tmp/agents")
MODEL_NAME = os.getenv("DEEPFACE_MODEL_NAME", "Facenet512")
DETECTOR_BACKEND = os.getenv("DEEPFACE_DETECTOR_BACKEND", "retinaface")
DEFAULT_FPS = float(os.getenv("VIDEO_SAMPLE_FPS", "1.0"))
DEFAULT_MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "70.0"))

FACE_DB_DIR = str(Path(DATA_DIR) / "faces")
Path(TMP_DIR).mkdir(parents=True, exist_ok=True)

app = FastAPI(title="blinkRoutines Agents", version="1.0.0")
store = FaceStore(FACE_DB_DIR)


def _read_upload(video: UploadFile) -> tuple[bytes, str]:
    content = video.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Video file is empty")
    suffix = Path(video.filename or "input.mp4").suffix or ".mp4"
    return content, suffix


def _read_image_upload(image: UploadFile) -> tuple[bytes, str]:
    content = image.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Image file is empty")
    if image.content_type and not image.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Uploaded file must be an image")
    suffix = Path(image.filename or "input.jpg").suffix or ".jpg"
    return content, suffix


def _extract_embeddings_from_video_bytes(video_bytes: bytes, suffix: str, fps: float) -> list[dict]:
    with tempfile.TemporaryDirectory(dir=TMP_DIR) as temp_dir:
        video_path = Path(temp_dir) / f"input{suffix}"
        video_path.write_bytes(video_bytes)

        frame_dir = Path(temp_dir) / "frames"
        try:
            frames = extract_frames(str(video_path), fps=fps, output_dir=str(frame_dir))
        except FFmpegError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        embeddings: list[dict] = []
        for frame_path in frames:
            try:
                embedding = extract_embedding(
                    image_path=frame_path,
                    model_name=MODEL_NAME,
                    detector_backend=DETECTOR_BACKEND,
                )
            except Exception as exc:  # pragma: no cover - runtime model/backend failures
                raise HTTPException(
                    status_code=500,
                    detail=f"DeepFace processing failed: {exc}",
                ) from exc
            if embedding is None:
                continue
            embeddings.append({"frame": Path(frame_path).name, "embedding": embedding})
        return embeddings


def _extract_embedding_from_image_bytes(image_bytes: bytes, suffix: str) -> list[float] | None:
    with tempfile.TemporaryDirectory(dir=TMP_DIR) as temp_dir:
        image_path = Path(temp_dir) / f"input{suffix}"
        image_path.write_bytes(image_bytes)
        try:
            return extract_embedding(
                image_path=str(image_path),
                model_name=MODEL_NAME,
                detector_backend=DETECTOR_BACKEND,
            )
        except Exception as exc:  # pragma: no cover - runtime model/backend failures
            raise HTTPException(
                status_code=500,
                detail=f"DeepFace processing failed: {exc}",
            ) from exc


@app.get("/health")
def health() -> dict:
    """Health endpoint for docker-compose and probes."""
    return {
        "ok": True,
        "model": MODEL_NAME,
        "detector_backend": DETECTOR_BACKEND,
        "faces_db": FACE_DB_DIR,
    }


@app.get("/api/v2/list_faces")
def list_faces() -> dict:
    """List known people currently stored in the local face database."""
    people = store.list_people()
    return {"status_code": 200, "is_ok": True, "response": people}


@app.post("/api/v2/register_face/{person_name}")
def register_face(
    person_name: str,
    video: UploadFile = File(...),
    sample_fps: float = Form(DEFAULT_FPS),
) -> dict:
    """Train/register a person using frames extracted from an uploaded video."""
    if sample_fps <= 0:
        raise HTTPException(status_code=400, detail="sample_fps must be > 0")

    video_bytes, suffix = _read_upload(video)
    embeddings = _extract_embeddings_from_video_bytes(video_bytes, suffix, sample_fps)

    vectors = [item["embedding"] for item in embeddings]
    if not vectors:
        raise HTTPException(
            status_code=422,
            detail="No faces could be extracted from provided video",
        )

    total = store.append_embeddings(person_name, vectors)
    return {
        "status_code": 200,
        "is_ok": True,
        "response": {
            "person_name": person_name,
            "frames_used": len(vectors),
            "total_embeddings": total,
        },
    }


@app.post("/api/v2/detect_person")
def detect_person(
    video: UploadFile = File(...),
    sample_fps: float = Form(DEFAULT_FPS),
    min_confidence: float = Form(DEFAULT_MIN_CONFIDENCE),
) -> dict:
    """Detect known people in an uploaded video using stored embeddings."""
    if sample_fps <= 0:
        raise HTTPException(status_code=400, detail="sample_fps must be > 0")
    if min_confidence < 0 or min_confidence > 100:
        raise HTTPException(status_code=400, detail="min_confidence must be between 0 and 100")

    known_embeddings = store.load_all()
    if not known_embeddings:
        raise HTTPException(status_code=404, detail="No registered faces available")

    video_bytes, suffix = _read_upload(video)
    embeddings = _extract_embeddings_from_video_bytes(video_bytes, suffix, sample_fps)

    detections = []
    for index, item in enumerate(embeddings):
        match = find_best_match(
            embedding=item["embedding"],
            known_embeddings=known_embeddings,
            min_confidence=min_confidence,
        )
        if not match:
            continue
        frame_time_seconds = round(index / sample_fps, 2)
        detections.append(
            {
                "frame": item["frame"],
                "frame_time_seconds": frame_time_seconds,
                "person_name": match.person_name,
                "confidence": round(match.confidence, 2),
                "distance": round(match.distance, 6),
            }
        )

    return {
        "status_code": 200,
        "is_ok": True,
        "response": {
            "frames_analyzed": len(embeddings),
            "detections": detections,
        },
    }


@app.post("/api/v2/register_face_image/{person_name}")
def register_face_image(
    person_name: str,
    image: UploadFile = File(...),
) -> dict:
    """Train/register a person using a single uploaded image."""
    image_bytes, suffix = _read_image_upload(image)
    embedding = _extract_embedding_from_image_bytes(image_bytes, suffix)
    if embedding is None:
        raise HTTPException(
            status_code=422,
            detail="No face could be extracted from provided image",
        )

    total = store.append_embeddings(person_name, [embedding])
    return {
        "status_code": 200,
        "is_ok": True,
        "response": {
            "person_name": person_name,
            "frames_used": 1,
            "total_embeddings": total,
        },
    }


@app.post("/api/v2/detect_person_image")
def detect_person_image(
    image: UploadFile = File(...),
    min_confidence: float = Form(DEFAULT_MIN_CONFIDENCE),
) -> dict:
    """Detect known people in a single uploaded image."""
    if min_confidence < 0 or min_confidence > 100:
        raise HTTPException(status_code=400, detail="min_confidence must be between 0 and 100")

    known_embeddings = store.load_all()
    if not known_embeddings:
        raise HTTPException(status_code=404, detail="No registered faces available")

    image_bytes, suffix = _read_image_upload(image)
    embedding = _extract_embedding_from_image_bytes(image_bytes, suffix)

    detections = []
    if embedding is not None:
        match = find_best_match(
            embedding=embedding,
            known_embeddings=known_embeddings,
            min_confidence=min_confidence,
        )
        if match:
            detections.append(
                {
                    "frame": "image",
                    "frame_time_seconds": 0.0,
                    "person_name": match.person_name,
                    "confidence": round(match.confidence, 2),
                    "distance": round(match.distance, 6),
                }
            )

    return {
        "status_code": 200,
        "is_ok": True,
        "response": {
            "frames_analyzed": 1,
            "detections": detections,
        },
    }
