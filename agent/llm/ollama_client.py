from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from agent.llm.base import LLMMessage


@dataclass(frozen=True)
class OllamaClient:
    host: str
    model: str
    timeout_s: float = 60.0

    def chat(self, messages: list[LLMMessage], *, temperature: float | None = None) -> str:
        url = self.host.rstrip("/") + "/api/chat"
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
        }
        if temperature is not None:
            payload["options"] = {"temperature": float(temperature)}

        req = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else str(e)
            if e.code == 404 and "model" in detail.lower() and "not found" in detail.lower():
                models = self.list_models()
                hint = ""
                if models:
                    hint = "Modèles installés: " + ", ".join(models)
                else:
                    hint = "Astuce: lance `ollama list` pour voir les modèles installés."
                return (
                    f"[Ollama] Modèle introuvable: '{self.model}'.\n"
                    f"{hint}\n"
                    "Fix: définis `OLLAMA_MODEL` (ex: `OLLAMA_MODEL=gemma4:latest`) ou mets un `config.json`."
                )
            return f"[Ollama HTTP {e.code}] {detail}"
        except Exception as e:
            return f"[Ollama error] {e}"

        try:
            data = json.loads(body)
        except Exception:
            return body

        msg = data.get("message") or {}
        content = msg.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        return body

    def list_models(self) -> list[str]:
        """
        Best-effort list of local Ollama models via /api/tags.
        """
        url = self.host.rstrip("/") + "/api/tags"
        req = urllib.request.Request(url=url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            data = json.loads(body)
            models = data.get("models") or []
            out: list[str] = []
            for m in models:
                name = m.get("name")
                if isinstance(name, str) and name:
                    out.append(name)
            return out
        except Exception:
            return []
