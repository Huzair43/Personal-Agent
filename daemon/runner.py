from __future__ import annotations

import os
import threading
import time

from agent.env_loader import load_env_file
from agent.logging_setup import setup_logging


def main() -> None:
    load_env_file(".env", override=True)
    setup_logging(log_level=os.getenv("LOG_LEVEL", "INFO"))
    channel = (os.getenv("CHANNEL") or "cli").lower()
    if channel == "cli":
        from channels.cli.main import main as run
    elif channel == "api":
        if (os.getenv("ENABLE_SCHEDULER_IN_API") or "0") == "1":
            try:
                from daemon.scheduler import start_scheduler

                handle = start_scheduler()

                def _stop_on_exit() -> None:
                    try:
                        while True:
                            time.sleep(1.0)
                    finally:
                        handle.stop()

                t = threading.Thread(target=_stop_on_exit, daemon=True)
                t.start()
            except Exception:
                pass
        from channels.api.server import main as run
    elif channel == "telegram":
        from channels.telegram.bot import main as run
    elif channel == "scheduler":
        from daemon.scheduler import main as run
    elif channel == "all":
        try:
            from daemon.scheduler import start_scheduler

            handle = start_scheduler()

            def _stop_on_exit() -> None:
                try:
                    while True:
                        time.sleep(1.0)
                finally:
                    handle.stop()

            t = threading.Thread(target=_stop_on_exit, daemon=True)
            t.start()
        except Exception:
            pass
        from channels.api.server import main as run
    elif channel == "all-cli":
        try:
            from daemon.scheduler import start_scheduler

            handle = start_scheduler()

            def _stop_on_exit() -> None:
                try:
                    while True:
                        time.sleep(1.0)
                finally:
                    handle.stop()

            t = threading.Thread(target=_stop_on_exit, daemon=True)
            t.start()
        except Exception:
            pass
        from channels.cli.main import main as run
    else:
        raise SystemExit("CHANNEL inconnu: cli | api | telegram | scheduler | all | all-cli")

    run()


if __name__ == "__main__":
    main()
