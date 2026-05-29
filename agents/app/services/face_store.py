"""Persistence layer for face embeddings."""

from __future__ import annotations

import json
from pathlib import Path


class FaceStore:
    """Simple JSON-based persistence for per-person embeddings."""

    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _person_path(self, person_name: str) -> Path:
        safe_name = person_name.strip().replace(" ", "_")
        return self.base_dir / f"{safe_name}.json"

    def save_embeddings(self, person_name: str, embeddings: list[list[float]]) -> None:
        path = self._person_path(person_name)
        payload = {
            "person_name": person_name,
            "embeddings": embeddings,
        }
        path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")

    def append_embeddings(self, person_name: str, embeddings: list[list[float]]) -> int:
        path = self._person_path(person_name)
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
        else:
            payload = {"person_name": person_name, "embeddings": []}
        payload["embeddings"].extend(embeddings)
        path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
        return len(payload["embeddings"])

    def list_people(self) -> list[str]:
        return sorted(path.stem for path in self.base_dir.glob("*.json"))

    def load_all(self) -> dict[str, list[list[float]]]:
        people: dict[str, list[list[float]]] = {}
        for path in self.base_dir.glob("*.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            people[payload.get("person_name", path.stem)] = payload.get("embeddings", [])
        return people
