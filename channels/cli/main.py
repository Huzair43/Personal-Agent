from __future__ import annotations

from agent.core import AgentCore


def main() -> None:
    agent = AgentCore.default()
    print("Agent ready. Type /help. Exit: Ctrl+C")
    try:
        while True:
            text = input("> ").strip()
            if text.lower() in {"exit", "quit"}:
                break
            print(agent.handle_message(text, user_id="local"))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

