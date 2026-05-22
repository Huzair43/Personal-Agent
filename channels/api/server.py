from __future__ import annotations

import uvicorn

from channels.api.app import app
from agent.config import Config


def main() -> None:
    cfg = Config.load()
    uvicorn.run(app, host=cfg.api_host, port=cfg.api_port, log_level="info")


if __name__ == "__main__":
    main()
