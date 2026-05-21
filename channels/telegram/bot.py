from __future__ import annotations

from agent.core import AgentCore


def main() -> None:
    agent = AgentCore.default()
    if not agent.config.telegram_token:
        raise SystemExit("TELEGRAM_TOKEN manquant (env var).")

    raise SystemExit(
        "Bot Telegram non implémenté sans dépendances externes.\n"
        "Recommandé: installer `python-telegram-bot` puis on branche le handler ici."
    )


if __name__ == "__main__":
    main()

