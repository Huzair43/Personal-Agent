from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from agent.core import AgentCore


class _Handler(BaseHTTPRequestHandler):
    agent = AgentCore.default()

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/health":
            self._send(404, {"error": "not_found"})
            return

        a = self.agent
        self._send(
            200,
            {
                "status": "ok",
                "ollama_host": a.config.ollama_host,
                "ollama_model": a.config.ollama_model,
            },
        )

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/chat":
            self._send(404, {"error": "not_found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8", errors="replace")
            data = json.loads(raw or "{}")
            text = str(data.get("text", "")).strip()
            user_id = str(data.get("user_id", "api")).strip() or "api"
        except Exception:
            self._send(400, {"error": "bad_request"})
            return

        if not text:
            self._send(400, {"error": "missing_text"})
            return

        reply = self.agent.handle_message(text, user_id=user_id)
        self._send(200, {"response": reply, "user_id": user_id})

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return


def main() -> None:
    agent = AgentCore.default()
    host, port = agent.config.api_host, agent.config.api_port
    _Handler.agent = agent
    server = HTTPServer((host, port), _Handler)
    print(f"API server sur http://{host}:{port} (GET /health, POST /chat)")
    server.serve_forever()


if __name__ == "__main__":
    main()
