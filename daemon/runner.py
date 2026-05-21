from __future__ import annotations

import os


def main() -> None:
    channel = (os.getenv("CHANNEL") or "cli").lower()
    if channel == "cli":
        from channels.cli.main import main as run
    elif channel == "api":
        from channels.api.server import main as run
    elif channel == "telegram":
        from channels.telegram.bot import main as run
    else:
        raise SystemExit("CHANNEL inconnu: cli | api | telegram")

    run()


if __name__ == "__main__":
    main()

