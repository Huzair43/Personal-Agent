from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent.env_loader import load_env_file


@dataclass(frozen=True)
class Config:
    llm_provider: str = "gemini"
    gemini_model: str = "gemini-3.5-flash"
    gemini_api_key: str | None = None

    memory_dir: str = ".agent_memory"
    log_level: str = "INFO"

    api_host: str = "127.0.0.1"
    api_port: int = 8080

    telegram_token: str | None = None
    db_path: str | None = None

    @staticmethod
    def from_env() -> "Config":
        return Config(
            llm_provider=os.getenv("LLM_PROVIDER") or "",
            gemini_model=os.getenv("GEMINI_MODEL") or "",
            gemini_api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or None,
            memory_dir=os.getenv("AGENT_MEMORY_DIR") or "",
            log_level=os.getenv("LOG_LEVEL") or "",
            api_host=os.getenv("API_HOST") or "",
            api_port=int(os.getenv("API_PORT")) if os.getenv("API_PORT") else 0,
            telegram_token=os.getenv("TELEGRAM_TOKEN") or None,
            db_path=os.getenv("AGENT_DB_PATH") or None,
        )

    @staticmethod
    def from_file(path: str | os.PathLike[str]) -> "Config":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return Config(**_coerce_config_dict(raw))

    @staticmethod
    def load(default_path: str = "config.json") -> "Config":
        """
        Priority:
        1) environment variables
        2) config.json (if present)
        3) class defaults
        """
        load_env_file(".env")
        base = Config()
        p = Path(default_path)
        if p.is_file():
            try:
                file_cfg = Config.from_file(p)
                base = _merge(base, file_cfg)
            except Exception:
                pass
        env_cfg = Config.from_env()
        return _merge(base, env_cfg)


def _merge(base: Config, override: Config) -> Config:
    return Config(
        llm_provider=override.llm_provider or base.llm_provider,
        gemini_model=override.gemini_model or base.gemini_model,
        gemini_api_key=override.gemini_api_key or base.gemini_api_key,
        memory_dir=override.memory_dir or base.memory_dir,
        log_level=override.log_level or base.log_level,
        api_host=override.api_host or base.api_host,
        api_port=override.api_port or base.api_port,
        telegram_token=override.telegram_token or base.telegram_token,
        db_path=override.db_path or base.db_path,
    )


def _coerce_config_dict(d: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = dict(d)
    if "api_port" in out:
        out["api_port"] = int(out["api_port"])
    return out
