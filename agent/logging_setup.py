from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(*, log_level: str = "INFO", log_dir: str = ".agent_logs") -> None:
    level = getattr(logging, (log_level or "INFO").upper(), logging.INFO)
    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(level)

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    log_path = os.getenv("LOG_FILE") or str(Path(log_dir) / "app.log")
    p = Path(log_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler(str(p), maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(fmt)
    root.addHandler(fh)

