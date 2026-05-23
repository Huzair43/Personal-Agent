""" Skill to navigate and list files/folders in the current directory.p"""
from __future__ import annotations
import os

import os
from pathlib import Path
from dataclasses import dataclass

from agent.skills.base import AgentContext, Skill
from agent.llm.base import BaseLLMClient
@dataclass
class CdSkill:
        
    name: str = "cd"
    description: str = "Change directory. Usage: /cd /path/to/directory"

    def run(self, *, args: str, ctx, llm):
        target = Path(args).resolve()

        if not target.exists():
            return f"ERROR: Path does not exist: {target}"

        if not target.is_dir():
            return f"ERROR: Path is not a directory: {target}"

        os.chdir(target)
        return f"Changed directory to: {target}"