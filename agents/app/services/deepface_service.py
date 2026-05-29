"""DeepFace wrappers for embedding extraction and matching."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass
class FaceMatch:
    """Single face match result."""

    person_name: str
    confidence: float
    distance: float


def _cosine_distance(vec1: list[float], vec2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sqrt(sum(a * a for a in vec1))
    norm2 = sqrt(sum(b * b for b in vec2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 1.0
    cosine_similarity = dot / (norm1 * norm2)
    return max(0.0, min(2.0, 1.0 - cosine_similarity))


def extract_embedding(
    image_path: str,
    model_name: str,
    detector_backend: str,
) -> list[float] | None:
    """Extract one embedding from an image path using DeepFace."""
    # Import lazily so module import remains lightweight until needed.
    from deepface import DeepFace  # pylint: disable=import-outside-toplevel

    representations = DeepFace.represent(
        img_path=image_path,
        model_name=model_name,
        detector_backend=detector_backend,
        enforce_detection=False,
    )
    if not representations:
        return None
    embedding = representations[0].get("embedding")
    if not embedding:
        return None
    return [float(value) for value in embedding]


def find_best_match(
    embedding: list[float],
    known_embeddings: dict[str, list[list[float]]],
    min_confidence: float,
) -> FaceMatch | None:
    """Find closest known person based on cosine distance."""
    best: FaceMatch | None = None
    for person_name, people_embeddings in known_embeddings.items():
        for candidate in people_embeddings:
            distance = _cosine_distance(embedding, candidate)
            confidence = max(0.0, min(100.0, (1.0 - distance) * 100.0))
            if confidence < min_confidence:
                continue
            if best is None or distance < best.distance:
                best = FaceMatch(
                    person_name=person_name,
                    confidence=confidence,
                    distance=distance,
                )
    return best
