from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from agent.llm.base import LLMMessage, LLMRole


@dataclass(frozen=True)
class GeminiClient:
    api_key: str
    model: str = "gemini-3.5-flash"
    base_url: str = "https://generativelanguage.googleapis.com"
    timeout_s: float = 60.0

    def chat(self, messages: list[LLMMessage], *, temperature: float | None = None) -> str:
        url = f"{self.base_url.rstrip('/')}/v1beta/models/{self.model}:generateContent"

        system_text, contents = _to_gemini_payload(messages)
        payload: dict = {"contents": contents}
        if system_text:
            payload["system_instruction"] = {"parts": [{"text": system_text}]}
        if temperature is not None:
            payload["generationConfig"] = {"temperature": float(temperature)}

        req = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else str(e)
            return f"[Gemini HTTP {e.code}] {detail}"
        except Exception as e:
            return f"[Gemini error] {e}"

        try:
            data = json.loads(body)
        except Exception:
            return body

        return _extract_text(data) or body


def _to_gemini_payload(messages: list[LLMMessage]) -> tuple[str, list[dict]]:
    system_parts: list[str] = []
    contents: list[dict] = []

    for m in messages:
        text = (m.content or "").strip()
        if not text:
            continue
        if m.role == LLMRole.SYSTEM:
            system_parts.append(text)
            continue

        role = "user" if m.role == LLMRole.USER else "model"
        contents.append({"role": role, "parts": [{"text": text}]})

    return ("\n\n".join(system_parts).strip(), contents)


def _extract_text(data: dict) -> str:
    candidates = data.get("candidates") or []
    for c in candidates:
        content = c.get("content") or {}
        parts = content.get("parts") or []
        texts: list[str] = []
        for p in parts:
            t = p.get("text")
            if isinstance(t, str) and t.strip():
                texts.append(t)
        if texts:
            return "\n".join(texts).strip()
    return ""

