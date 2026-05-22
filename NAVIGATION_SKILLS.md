# Navigation Skills - Explorer & Browse

## Overview

The agent can now explore and browse files in the current directory safely.

## Available Commands

### `/explore` - Explore folder structure

```bash
/explore                # Display current directory (1 level)
/explore agent          # Explore a specific folder
/explore -tree          # Display full directory tree (3 levels max)
```

**Examples:**
```
> /explore
personal-agent/ (16 items)
  agent/
  channels/
  daemon/
  config.json (246.0B)
  README.md (2.2KB)
  ...

> /explore -tree
personal-agent/
├── agent/
│   ├── __init__.py (0.0B)
│   ├── llm/
│   ├── skills/
│   ...
```

**Practical uses:**
- View project structure
- Check which files exist
- Navigate quickly

---

### `/browse` - Read and browse files

```bash
/browse <file>          # Read a specific file
/browse *.ext           # List all files with this extension
/browse -search <text>  # Search for text in files
```

**Examples:**
```
> /browse config.json
config.json
{
  "ollama_host": "http://127.0.0.1:11434",
  "ollama_model": "phi4-mini",
  ...
}

> /browse *.py
Fichiers correspondant a '*.py' (42 found):
  core.py (6.2KB)
  config.py (3.0KB)
  ...

> /browse -search TODO
Recherche 'TODO' (5 files found):
  agent/core.py (2 occurrences)
  skills/tasks_planner.py (1 occurrence)
  ...
```

**Practical uses:**
- Read file content
- Search for code/content
- List files of a type

---

## Security

- Paths are verified: Cannot exit the current directory
- Binary files ignored (.pyc, .dll, etc.)
- Hidden files filtered (.env, .git/, etc.)
- Safe text reading with utf-8 encoding

- Performance limits: Files truncated after 4000 characters, Max 30 results per listing, Search limited to 20 files

---

## Integration with other skills

The agent can combine multiple skills for powerful workflows:

```bash
# Example: Explore, then analyze
> /explore agent/skills
# (shows available skills)

> /browse agent/skills/tasks_planner.py
# (read code)

> /review agent/skills/tasks_planner.py
# (code review)
```

---

## Configuration

Paths are always relative to the execution directory:

```bash
# If you launch from /home/user/project/:
python -m channels.cli.main

# Then /explore explores /home/user/project/
```

To change context, simply change directory before launching the agent.

---

## Intentional Limitations

| Limitation | Reason |
|-----------|--------|
| No file modification | Security (prevent accidental changes) |
| Files truncated after 4KB | Limited LLM context |
| Max 3 levels in -tree | Performance |
| Binary files ignored | Avoid garbage |

To modify files, use your editor directly. The agent focuses on reading and analysis.
