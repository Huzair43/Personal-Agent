from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent.core import AgentCore


app = FastAPI(title="Personal Agent API")
_agent = AgentCore.default()


class ChatRequest(BaseModel):
    text: str
    user_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    user_id: str


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "ollama_host": _agent.config.ollama_host,
        "ollama_model": _agent.config.ollama_model,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="missing_text")
    user_id = (req.user_id or "api").strip() or "api"
    reply = _agent.handle_message(text, user_id=user_id)
    return ChatResponse(response=reply, user_id=user_id)

