from __future__ import annotations

from pathlib import Path


_LOADED = False


def load_env_file(path: str = ".env", *, override: bool = False) -> bool:
    """
    Loads environment variables from a .env file if python-dotenv is available.
    Returns True if a .env file was loaded, else False.
    """
    global _LOADED
    if _LOADED:
        return False

    p = Path(path)
    if not p.is_file():
        _LOADED = True
        return False

    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        _LOADED = True
        return False

    loaded = bool(load_dotenv(dotenv_path=str(p), override=bool(override)))
    _LOADED = True
    return loaded
