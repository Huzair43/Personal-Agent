from __future__ import annotations

import subprocess
from dataclasses import dataclass

from agent.skills.base import AgentContext
from agent.llm.base import BaseLLMClient


@dataclass(frozen=True)
class GitHelperSkill:
    name: str = "git"
    description: str = "Aide Git (status, log). Ex: /git status"

    def run(self, *, args: str, ctx: AgentContext, llm: BaseLLMClient) -> str:
        parts = (args or "").strip().split()
        if not parts:
            return "Usage: /git status | /git log"

        sub = parts[0]
        if sub not in {"status", "log"}:
            return "Sous-commande supportée: status, log"

        cmd = ["git", sub]
        if sub == "log":
            cmd += ["--oneline", "-n", "20"]

        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        except FileNotFoundError:
            return "Git n'est pas disponible dans l'environnement."
        except subprocess.CalledProcessError as e:
            return f"Erreur git:\n{e.output}"

        return out.strip() or "(aucune sortie)"

