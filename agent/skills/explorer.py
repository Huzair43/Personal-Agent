"""Skill to explore and list files/folders in the current directory."""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass

from agent.skills.base import AgentContext, Skill
from agent.llm.base import BaseLLMClient


@dataclass
class ExplorerSkill:
    """Explore and list files/folders in the current directory."""

    name: str = "explore"
    description: str = "Explore files and folders in current directory. Usage: /explore, /explore path, /explore -tree"

    def run(self, *, args: str, ctx: AgentContext, llm: BaseLLMClient) -> str:
        """
        Explore files and folders.
        
        Args:
            /explore - list current directory (1 level)
            /explore <path> - list a specific path
            /explore -tree - show directory tree (3 levels max)
        """
        args = (args or "").strip()
        
        if args == "-tree":
            return self._show_tree(Path.cwd(), max_depth=3)
        
        if args:
            target = Path(args)
        else:
            target = Path.cwd()
        
        # Resolve relative paths
        if not target.is_absolute():
            target = Path.cwd() / target
        
        # Verify path is in safe directory (cwd or subfolder)
        try:
            target = target.resolve()
            cwd = Path.cwd().resolve()
            target.relative_to(cwd)
        except ValueError:
            return f"ERROR: Path outside current directory: {target}"
        
        # Verify path exists
        if not target.exists():
            return f"ERROR: Path does not exist: {target}"
        
        if target.is_file():
            return self._show_file_info(target)
        
        return self._list_directory(target)

    def _list_directory(self, path: Path) -> str:
        """List directory contents."""
        try:
            items = sorted(path.iterdir())
        except PermissionError:
            return f"ERROR: Access denied: {path}"
        
        if not items:
            return f"{path.name}/ (empty)"
        
        lines = [f"{path.name}/ ({len(items)} items)\n"]
        
        # Separate directories and files
        dirs = [i for i in items if i.is_dir() and not i.name.startswith(".")]
        files = [i for i in items if i.is_file() and not i.name.startswith(".")]
        
        # Display directories
        for d in sorted(dirs)[:20]:
            lines.append(f"  {d.name}/")
        
        if len(dirs) > 20:
            lines.append(f"  ... and {len(dirs) - 20} other directories")
        
        # Display files
        for f in sorted(files)[:20]:
            size = self._format_size(f.stat().st_size)
            lines.append(f"  {f.name} ({size})")
        
        if len(files) > 20:
            lines.append(f"  ... and {len(files) - 20} other files")
        
        return "\n".join(lines)

    def _show_file_info(self, path: Path) -> str:
        """Display file information."""
        try:
            stat = path.stat()
            size = self._format_size(stat.st_size)
            lines = [
                f"{path.name}",
                f"   Path: {path}",
                f"   Size: {size}",
                f"   Extension: {path.suffix}",
            ]
            return "\n".join(lines)
        except Exception as e:
            return f"ERROR: {e}"

    def _show_tree(self, path: Path, max_depth: int = 3, depth: int = 0, prefix: str = "") -> str:
        """Display directory tree."""
        if depth > max_depth:
            return ""
        
        try:
            items = sorted(path.iterdir())
        except PermissionError:
            return f"{prefix}ERROR: Access denied\n"
        
        # Filter hidden directories and limit
        items = [i for i in items if not i.name.startswith(".")][:30]
        
        lines = []
        if depth == 0:
            lines.append(f"{path.name}/")
        
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            
            if item.is_dir():
                lines.append(f"{prefix}{connector}{item.name}/")
                if depth < max_depth:
                    extension = "    " if is_last else "|   "
                    subtree = self._show_tree(item, max_depth, depth + 1, prefix + extension)
                    if subtree:
                        lines.append(subtree.rstrip())
            else:
                size = self._format_size(item.stat().st_size)
                lines.append(f"{prefix}{connector}{item.name} ({size})")
        
        return "\n".join(lines)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format size in bytes to human readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"
