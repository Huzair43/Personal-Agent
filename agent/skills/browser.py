"""Skill to browse and read file contents in the current directory."""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass

from agent.skills.base import AgentContext, Skill
from agent.llm.base import BaseLLMClient


@dataclass
class BrowseSkill:
    """Browse and read files in the current directory."""

    name: str = "browse"
    description: str = "Read and browse files. Usage: /browse file.txt, /browse *.py, /browse -search text"

    def run(self, *, args: str, ctx: AgentContext, llm: BaseLLMClient) -> str:
        """
        Browse and read files.
        
        Args:
            /browse <file> - read a specific file
            /browse *.py - list all .py files
            /browse -search <text> - search for text in files
        """
        args = (args or "").strip()
        
        if not args:
            return "Usage: /browse <file>, /browse *.ext, /browse -search <text>"
        
        if args.startswith("-search "):
            search_term = args[8:].strip()
            return self._search_in_files(search_term)
        
        if "*" in args or "?" in args:
            return self._list_by_pattern(args)
        
        # Otherwise it's a file
        return self._read_file(args)

    def _read_file(self, filename: str) -> str:
        """Read a specific file."""
        filepath = Path(filename)
        
        # Relative path
        if not filepath.is_absolute():
            filepath = Path.cwd() / filepath
        
        # Security: verify we're in cwd
        try:
            filepath = filepath.resolve()
            cwd = Path.cwd().resolve()
            filepath.relative_to(cwd)
        except ValueError:
            return f"ERROR: Path outside current directory: {filepath}"
        
        if not filepath.exists():
            return f"ERROR: File does not exist: {filepath}"
        
        if not filepath.is_file():
            return f"ERROR: Not a file: {filepath}"
        
        # Binary extensions to ignore
        binary_exts = {".pyc", ".so", ".dll", ".exe", ".o", ".a", ".zip", ".tar", ".gz"}
        if filepath.suffix.lower() in binary_exts:
            return f"ERROR: Binary file not readable: {filepath}"
        
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
            
            # Limit response size
            max_chars = 4000
            if len(content) > max_chars:
                lines = content.splitlines()
                content = "\n".join(lines[:100])
                content += f"\n\n[... file truncated ({len(lines)} total lines) ...]"
            
            return f"{filepath.name}\n\n{content}"
        except Exception as e:
            return f"ERROR: Read failed: {e}"

    def _list_by_pattern(self, pattern: str) -> str:
        """List files matching pattern."""
        try:
            matches = sorted(Path.cwd().glob(pattern))
            
            if not matches:
                return f"ERROR: No files match '{pattern}'"
            
            lines = [f"Files matching '{pattern}' ({len(matches)} found):\n"]
            
            for i, match in enumerate(matches[:30]):
                if match.is_file():
                    size = self._format_size(match.stat().st_size)
                    lines.append(f"  {match.name} ({size})")
                elif match.is_dir():
                    lines.append(f"  {match.name}/ (directory)")
            
            if len(matches) > 30:
                lines.append(f"  ... and {len(matches) - 30} others")
            
            return "\n".join(lines)
        except Exception as e:
            return f"ERROR: {e}"

    def _search_in_files(self, search_term: str) -> str:
        """Search for text in files."""
        if not search_term or len(search_term) < 2:
            return "ERROR: Search term too short (min 2 characters)"
        
        results = []
        
        # Search in text files
        for filepath in Path.cwd().rglob("*"):
            if not filepath.is_file():
                continue
            
            # Skip binary and hidden files
            if filepath.name.startswith(".") or filepath.suffix in {".pyc", ".so", ".dll"}:
                continue
            
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                
                if search_term.lower() in content.lower():
                    # Compter les occurrences
                    count = content.lower().count(search_term.lower())
                    rel_path = filepath.relative_to(Path.cwd())
                    results.append((rel_path, count))
            except Exception:
                pass
        
        if not results:
            return f"No files contain '{search_term}'"
        
        # Sort by number of occurrences
        results.sort(key=lambda x: x[1], reverse=True)
        
        lines = [f"Search '{search_term}' ({len(results)} files found):\n"]
        
        for filepath, count in results[:20]:
            lines.append(f"  {filepath} ({count} occurrence{'s' if count > 1 else ''})")
        
        if len(results) > 20:
            lines.append(f"  ... and {len(results) - 20} others")
        
        return "\n".join(lines)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format size in bytes."""
        for unit in ["B", "KB", "MB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}GB"
