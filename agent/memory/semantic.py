from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SemanticItem:
    key: str
    value: str


class SemanticMemory:
    def __init__(self, path: Path):
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, str] = {}
        self._load()

    @staticmethod
    def from_dir(memory_dir: str) -> "SemanticMemory":
        return SemanticMemory(Path(memory_dir) / "semantic.json")

    def put(self, key: str, value: str) -> None:
        self._cache[key] = value
        self._path.write_text(json.dumps(self._cache, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, key: str) -> str | None:
        return self._cache.get(key)

    def search(self, query: str, *, limit: int = 5) -> list[SemanticItem]:
        q = (query or "").lower()
        hits: list[SemanticItem] = []
        for k, v in self._cache.items():
            if q in k.lower() or q in v.lower():
                hits.append(SemanticItem(key=k, value=v))
        return hits[:limit]

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            self._cache = json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            self._cache = {}

