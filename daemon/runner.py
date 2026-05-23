from __future__ import annotations

import os
import threading
import time

from agent.env_loader import load_env_file
from agent.logging_setup import setup_logging


def main() -> None:
    load_env_file(".env", override=True)
    setup_logging(log_level=os.getenv("LOG_LEVEL", "INFO"))
    
    # Start scheduler in background for all channels
    scheduler_handle = None
    try:
        from daemon.scheduler import start_scheduler
        scheduler_handle = start_scheduler()
        
        def _stop_on_exit() -> None:
            try:
                while True:
                    time.sleep(1.0)
            finally:
                if scheduler_handle:
                    scheduler_handle.stop()
        
        t = threading.Thread(target=_stop_on_exit, daemon=False)
        t.start()
    except Exception as e:
        print(f"Warning: Could not start scheduler: {e}")
    
    channel = (os.getenv("CHANNEL") or "cli").lower()
    if channel == "cli":
        from channels.cli.main import main as run
    elif channel == "api":
        from channels.api.server import main as run
    elif channel == "telegram":
        from channels.telegram.bot import main as run
    elif channel == "scheduler":
        from daemon.scheduler import main as run
    elif channel == "all":
        from channels.api.server import main as run
    elif channel == "all-cli":
        from channels.cli.main import main as run
    else:
        raise SystemExit("Unknown CHANNEL: cli | api | telegram | scheduler | all | all-cli")

    run()


if __name__ == "__main__":
    main()
