from __future__ import annotations

import logging

from agent.core import AgentCore


def main() -> None:
    agent = AgentCore.default()
    if not agent.config.telegram_token:
        raise SystemExit("TELEGRAM_TOKEN manquant (env var).")

    try:
        from telegram import Update
        from telegram.ext import Application, ContextTypes, MessageHandler, filters
    except Exception as e:
        raise SystemExit(
            "Dépendance manquante.\n"
            "Installe `python-telegram-bot` puis relance.\n"
            f"Détail: {e}"
        )

    log = logging.getLogger("telegram")

    async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: ARG001
        if update.message is None:
            return
        text = (update.message.text or "").strip()
        if not text:
            return

        try:
            reply = agent.handle_message(text, user_id="local")
        except Exception as exc:
            log.exception("telegram handler error")
            reply = f"Error: {exc}"

        await update.message.reply_text(reply)

    application = Application.builder().token(agent.config.telegram_token).build()
    application.add_handler(MessageHandler(filters.TEXT | filters.COMMAND, on_message))

    print("Telegram bot actif. Ctrl+C pour arrêter.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
