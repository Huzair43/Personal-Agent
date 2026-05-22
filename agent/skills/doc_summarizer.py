from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent.llm.base import BaseLLMClient, LLMMessage, LLMRole
from agent.skills.base import AgentContext


@dataclass(frozen=True)
class DocSummarizerSkill:
    name: str = "doc"
    description: str = "Résume un fichier: /doc chemin/vers/fichier.md"

    def run(self, *, args: str, ctx: AgentContext, llm: BaseLLMClient) -> str:
        raw = (args or "").strip()
        if not raw:
            return "Usage: /doc <chemin/fichier> [objectif]"

        path_str, objective = _split_first(raw)
        path = Path(path_str)
        if not path.exists() or not path.is_file():
            return f"Fichier introuvable: {path_str}"

        try:
            content = _read_repo_file(path)
        except Exception as e:
            return f"Impossible de lire `{path_str}`: {e}"

        goal = objective.strip() or "résumer pour quelqu'un qui découvre le projet"
        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content=(
                    "Tu résumes un document en français, de façon concise et utile.\n"
                    "Format demandé:\n"
                    "Résumé: <2-5 phrases>\n"
                    "Points clés: <3-7 lignes>\n"
                    "Questions ouvertes: <0-3 lignes>\n"
                    "N'utilise pas de listes avec des tirets."
                ),
            ),
            LLMMessage(role=LLMRole.USER, content=f"Objectif: {goal}\nFichier: {path.as_posix()}\n\n{_wrap_doc(content)}"),
        ]
        return llm.chat(messages)


_MAX_DOC_CHARS = 80_000


def _split_first(s: str) -> tuple[str, str]:
    first, rest = (s.split(maxsplit=1) + [""])[:2]
    return first, rest


def _read_repo_file(path: Path) -> str:
    root = Path.cwd().resolve()
    resolved = (root / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(root)
    except Exception:
        raise ValueError("chemin en dehors du projet (refusé)")

    text = resolved.read_text(encoding="utf-8", errors="replace")
    if len(text) > _MAX_DOC_CHARS:
        text = text[:_MAX_DOC_CHARS] + "\n\n... (tronqué)"
    return text


def _wrap_doc(text: str) -> str:
    return "```text\n" + text.rstrip() + "\n```"

