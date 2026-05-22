from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass

from agent.llm.base import LLMMessage, LLMRole, BaseLLMClient
from agent.skills.base import AgentContext


@dataclass(frozen=True)
class CodeReviewSkill:
    name: str = "review"
    description: str = "Revue rapide: texte ou fichier. Ex: /review agent/core.py"

    def run(self, *, args: str, ctx: AgentContext, llm: BaseLLMClient) -> str:
        if not args.strip():
            return "Usage: /review <texte> | /review <chemin/fichier.py>"

        title, content = _resolve_review_input(args)
        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content=(
                    "Tu fais une revue de code concise en français.\n"
                    "Structure: 1) Problèmes 2) Suggestions 3) Questions.\n"
                    "Si le contexte manque, demande des précisions."
                ),
            ),
            LLMMessage(role=LLMRole.USER, content=f"{title}\n\n{content}"),
        ]
        return llm.chat(messages)


_MAX_FILE_CHARS = 40_000


def _resolve_review_input(args: str) -> tuple[str, str]:
    """
    If `args` points to a file in the repo, read it.
    Otherwise, treat args as free-form text.
    """
    raw = (args or "").strip()
    first, *_rest = raw.split(maxsplit=1)
    path = Path(first)
    if path.exists() and path.is_file():
        try:
            text = _read_repo_file(path)
        except Exception as e:
            return ("Revue (fichier):", f"Impossible de lire `{first}`: {e}")
        return (f"Fichier: {path.as_posix()}", _wrap_code(text))
    return ("Revue (texte):", raw)


def _read_repo_file(path: Path) -> str:
    root = Path.cwd().resolve()
    resolved = (root / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(root)
    except Exception:
        raise ValueError("chemin en dehors du projet (refusé)")

    text = resolved.read_text(encoding="utf-8", errors="replace")
    if len(text) > _MAX_FILE_CHARS:
        text = text[:_MAX_FILE_CHARS] + "\n\n... (tronqué)"
    return text


def _wrap_code(text: str) -> str:
    return "```text\n" + text.rstrip() + "\n```"
