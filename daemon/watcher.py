from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class WatchEvent:
    path: str
    mtime: float


def watch_dir(path: str, *, interval_s: float = 1.0, on_change: Callable[[WatchEvent], None]) -> None:
    root = Path(path)
    last: dict[str, float] = {}
    while True:
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            try:
                mtime = p.stat().st_mtime
            except OSError:
                continue
            key = str(p)
            prev = last.get(key)
            if prev is None:
                last[key] = mtime
                continue
            if mtime != prev:
                last[key] = mtime
                on_change(WatchEvent(path=key, mtime=mtime))
        time.sleep(interval_s)


def main() -> None:
    target = os.getenv("WATCH_DIR", ".")

    def _print(ev: WatchEvent) -> None:
        print(f"changed: {ev.path}")

    watch_dir(target, on_change=_print)


if __name__ == "__main__":
    main()

