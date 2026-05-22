from __future__ import annotations

import json
import unicodedata
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

    def items(self, *, limit: int = 50) -> list[SemanticItem]:
        out: list[SemanticItem] = []
        for k in sorted(self._cache.keys()):
            out.append(SemanticItem(key=k, value=str(self._cache[k])))
            if len(out) >= limit:
                break
        return out

    def search(self, query: str, *, limit: int = 5) -> list[SemanticItem]:
        q = _norm(query)
        hits: list[SemanticItem] = []
        for k, v in self._cache.items():
            if q and (_norm(k).find(q) != -1 or _norm(v).find(q) != -1):
                hits.append(SemanticItem(key=k, value=v))
        return hits[:limit]

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            self._cache = json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            self._cache = {}


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))
