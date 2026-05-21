from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Config:
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "phi4-mini"

    memory_dir: str = ".agent_memory"
    log_level: str = "INFO"

    api_host: str = "127.0.0.1"
    api_port: int = 8080

    telegram_token: str | None = None

    @staticmethod
    def from_env() -> "Config":
        return Config(
            ollama_host=os.getenv("OLLAMA_HOST", Config.ollama_host),
            ollama_model=os.getenv("OLLAMA_MODEL", Config.ollama_model),
            memory_dir=os.getenv("AGENT_MEMORY_DIR", Config.memory_dir),
            log_level=os.getenv("LOG_LEVEL", Config.log_level),
            api_host=os.getenv("API_HOST", Config.api_host),
            api_port=int(os.getenv("API_PORT", str(Config.api_port))),
            telegram_token=os.getenv("TELEGRAM_TOKEN") or None,
        )

    @staticmethod
    def from_file(path: str | os.PathLike[str]) -> "Config":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return Config(**_coerce_config_dict(raw))

    @staticmethod
    def load(default_path: str = "config.json") -> "Config":
        """
        Priority:
        1) config.json (if present)
        2) environment variables
        3) class defaults
        """
        cfg = Config.from_env()
        p = Path(default_path)
        if p.is_file():
            try:
                file_cfg = Config.from_file(p)
            except Exception:
                return cfg
            return _merge(cfg, file_cfg)
        return cfg


def _merge(base: Config, override: Config) -> Config:
    return Config(
        ollama_host=override.ollama_host or base.ollama_host,
        ollama_model=override.ollama_model or base.ollama_model,
        memory_dir=override.memory_dir or base.memory_dir,
        log_level=override.log_level or base.log_level,
        api_host=override.api_host or base.api_host,
        api_port=override.api_port or base.api_port,
        telegram_token=override.telegram_token or base.telegram_token,
    )


def _coerce_config_dict(d: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = dict(d)
    if "api_port" in out:
        out["api_port"] = int(out["api_port"])
    return out
