# Structure du projet

Ce dépôt contient un squelette d’agent local, organisé par responsabilités (LLM, mémoire, skills, channels, daemon).

## Arborescence

```
personal-agent/
  agent/
    core.py
    config.py
    llm/
      base.py
      gemini_client.py
    memory/
      episodic.py
      semantic.py
    skills/
      base.py
      tasks_planner.py
      code_review.py
      doc_summarizer.py
      git_helper.py
      remember.py
      recall.py
      habits.py
      llm_info.py
      stats.py
      explorer.py
      browser.py
      cd.py

  channels/
    cli/
      main.py
    api/
      server.py
      app.py
    telegram/
      bot.py

  daemon/
    runner.py
    watcher.py
    scheduler.py
    ingest.py
    habits.py

  config.json
  .gitignore
  STRUCTURE.md
  CACHE_INCREMENTAL.md
  NAVIGATION_SKILLS.md
```

## Détails par dossier (résumé)

### `agent/`
Coeur du projet.

1. `agent/core.py` : point d’entrée logique (orchestration). Route les messages, gère `/help` et les commandes `/plan`, `/review`, `/doc`, `/git`, `/remember`, `/recall`, et appelle le client LLM.
2. `agent/config.py` : configuration (env vars + `config.json`) : hôte/modèle Ollama, mémoire, API, etc.

### `agent/llm/`
Abstraction LLM.

1. `agent/llm/base.py` : structures de messages (`LLMMessage`, rôles) et contrat minimal du client (`BaseLLMClient.chat(...)`).
2. `agent/llm/gemini_client.py` : client HTTP Gemini (`models/gemini-3.5-flash:generateContent`), clé via `GEMINI_API_KEY`.

### `agent/memory/`
Mémoire persistée sur disque (simple, sans dépendances externes).

1. `agent/memory/episodic.py` : historique court des interactions (JSONL).
2. `agent/memory/semantic.py` : stockage clé/valeur (JSON) + recherche naïve (substring).

Note: `agent/core.py` injecte automatiquement un petit contexte depuis ces mémoires avant d’appeler Ollama (historique récent + rappels).

### `agent/skills/`
Commandes “outils” déclenchées via `/commande ...`.

1. `agent/skills/base.py` : interface d’un skill (`name`, `description`, `run(...)`) + `AgentContext`.
2. `agent/skills/tasks_planner.py` : `/plan` (génère un plan court via le LLM).
3. `agent/skills/code_review.py` : `/review` (revue à partir d’un texte OU d’un fichier du repo).
4. `agent/skills/doc_summarizer.py` : `/doc` (résume un fichier du repo: Markdown, texte, etc.).
5. `agent/skills/git_helper.py` : `/git status|log` (commande Git minimale).
6. `agent/skills/remember.py` : `/remember cle=valeur` (écrit dans la mémoire sémantique).
7. `agent/skills/recall.py` : `/recall mot` (recherche dans la mémoire sémantique, sans appel LLM).
8. `agent/skills/habits.py` : `/habits` (affiche des stats depuis la base SQLite).
9. `agent/skills/llm_info.py` : `/llm` (affiche le provider et modele LLM).
10. `agent/skills/stats.py` : `/stats` (etat tracking).
11. `agent/skills/explorer.py` : `/explore` (explore et liste fichiers/dossiers avec arborescence).
12. `agent/skills/browser.py` : `/browse` (lit et parcourt les fichiers, cherche du texte).
13. `agent/skills/cd.py` : `/cd` (change de repertoire courant).

### `channels/`
Canaux d’entrées/sorties.

1. `channels/cli/main.py` : interface CLI (REPL).
2. `channels/api/server.py` : lance uvicorn pour l API.
3. `channels/api/app.py` : application FastAPI (routes `GET /health`, `POST /chat`).
4. `channels/telegram/bot.py` : bot Telegram (polling) qui route vers `AgentCore`.

### `daemon/`
Lancement et tâches de fond.

1. `daemon/runner.py` : lance un channel selon `CHANNEL=cli|api|telegram`.
2. `daemon/watcher.py` : watcher simple (polling) pour détecter des changements de fichiers.
3. `daemon/scheduler.py` : scheduler (jobs périodiques) + watcher temps réel pour ingestion.
4. `daemon/ingest.py` : ingestion incrémentale de `episodic.jsonl` vers SQLite.
5. `daemon/habits.py` : calcul de stats quotidiennes et profil semaine.

## Fichiers à la racine

1. `config.json` : configuration par défaut (ex: `gemini_api_key`).
2. `.gitignore` : ignore la mémoire locale (`.agent_memory/`) et fichiers Python temporaires.
3. `STRUCTURE.md` : ce document.

## Lancer

1. CLI : `python -m channels.cli.main`
2. API : `python -m channels.api.server`
3. Runner : (PowerShell) `$env:CHANNEL="cli"; python -m daemon.runner`

## Exemples de commandes (CLI)

1. `/help`
2. `/plan écrire des tests pour ce projet`
3. `/review agent/core.py`
4. `/doc STRUCTURE.md`
5. `/git status`
6. `/remember prenom=Huzair`
7. `/recall prenom`
8. `/habits week`

## Référence du code (par fichier)

### `agent/config.py`
Objectif: fournir une configuration stable et simple.

1. `Config` (dataclass)
   1. Champs: `ollama_host`, `ollama_model`, `memory_dir`, `log_level`, `api_host`, `api_port`, `telegram_token`
2. Méthodes
   1. `Config.from_env()` lit les variables d’environnement (`OLLAMA_HOST`, `OLLAMA_MODEL`, `AGENT_MEMORY_DIR`, `LOG_LEVEL`, `API_HOST`, `API_PORT`, `TELEGRAM_TOKEN`)
   2. `Config.from_file(path)` lit un JSON
   3. `Config.load(default_path="config.json")` charge `config.json` si présent, sinon l’environnement (et retombe sur les valeurs par défaut)

### `agent/core.py`
Objectif: orchestration et routage.

1. `AgentCore.default()`
   1. Charge `Config`
   2. Construit `OllamaClient`, `EpisodicMemory`, `SemanticMemory`
   3. Enregistre les skills: `plan`, `review`, `doc`, `git`, `remember`, `recall`
2. `AgentCore.handle_message(text, user_id="local")`
   1. Si `/help` retourne la liste des commandes
   2. Si message commence par `/`, exécute le skill correspondant
   3. Sinon construit un prompt via `_default_prompt(...)` puis appelle `llm.chat(...)`
   4. Journalise chaque interaction dans `EpisodicMemory.add_event(...)`
3. `_default_prompt(user_text, user_id=...)`
   1. Ajoute un message system “règles”
   2. Ajoute un message system “mémoire” (si disponible)
   3. Ajoute le message user
4. `_memory_context(user_id=..., query=...)`
   1. Contexte récent: derniers échanges du même `user_id` via `episodic_memory.tail(...)`
   2. Rappels: recherche substring via `semantic_memory.search(query)`

### `agent/llm/base.py`
Objectif: définir un contrat minimal LLM.

1. `LLMRole` (Enum): `system`, `user`, `assistant`
2. `LLMMessage` (dataclass): `role`, `content`
3. `BaseLLMClient` (Protocol): `chat(messages, temperature=None) -> str`

### `agent/llm/ollama_client.py`
Objectif: implémenter `chat()` avec Ollama sans dépendances externes.

1. `OllamaClient(host, model, timeout_s=60)`
2. `chat(messages, temperature=None)`
   1. `POST {host}/api/chat` avec `stream=false`
   2. Retourne le champ `message.content` si présent
   3. En cas de 404 “model not found”, affiche un message d’aide + liste `list_models()`
3. `list_models()`
   1. `GET {host}/api/tags`
   2. Retourne une liste de noms de modèles (best-effort)

### `agent/memory/episodic.py`
Objectif: garder une trace simple des conversations.

1. `EpisodicEvent(ts, user_id, user_text, agent_text)`
2. `EpisodicMemory.from_dir(memory_dir)`
3. `add_event(...)` écrit un JSON par ligne dans `episodic.jsonl`
4. `tail(n=20)` relit le fichier et retourne les derniers événements

### `agent/memory/semantic.py`
Objectif: stocker des informations “clé/valeur” et retrouver vite.

1. `SemanticMemory.from_dir(memory_dir)` charge `semantic.json`
2. `put(key, value)` écrit le JSON
3. `get(key)` lit depuis le cache mémoire
4. `search(query, limit=5)` retourne les paires où `query` apparaît dans la clé ou la valeur

### `agent/skills/base.py`
Objectif: standardiser les skills.

1. `AgentContext(user_id, config)`
2. `Skill` (Protocol)
   1. Attributs: `name`, `description`
   2. Méthode: `run(args, ctx, llm) -> str`

### `agent/skills/tasks_planner.py`
Commande: `/plan`

1. Envoie au LLM une consigne “plan court en étapes”
2. Retourne la réponse brute du modèle

### `agent/skills/code_review.py`
Commande: `/review`

1. Accepte du texte libre ou un chemin de fichier (si le fichier existe)
2. Refuse les chemins en dehors du projet
3. Tronque si trop long, puis demande une revue structurée au LLM

### `agent/skills/doc_summarizer.py`
Commande: `/doc`

1. Lit un fichier du repo, optionnellement avec un objectif (`/doc README.md expliquer le projet`)
2. Refuse les chemins en dehors du projet
3. Tronque si trop long, puis demande un résumé structuré au LLM

### `agent/skills/git_helper.py`
Commande: `/git`

1. Supporte `status` et `log` (20 commits) via `subprocess`
2. Retourne la sortie Git ou une erreur lisible

### `agent/skills/remember.py`
Commande: `/remember`

1. Parse `cle=valeur`
2. Stocke via `SemanticMemory.put(key, value)`

### `agent/skills/recall.py`
Commande: `/recall`

1. Recherche via `SemanticMemory.search(query)`
2. Retourne les résultats sans appeler le LLM

### `agent/skills/habits.py`
Commande: `/habits`

1. Lit les événements depuis SQLite
2. Affiche des stats du jour ou de la semaine

### `channels/cli/main.py`
Objectif: interface interactive.

1. Boucle `input("> ")`
2. Envoie le texte vers `AgentCore.handle_message(...)`
3. Quitte sur `Ctrl+C` ou `exit/quit`

### `channels/api/server.py`
Objectif: exposer une API HTTP minimale.

1. Lance uvicorn et charge l application FastAPI

### `channels/api/app.py`
Objectif: routes HTTP.

1. `GET /health` retourne un statut et la config LLM (host/modèle)
2. `POST /chat` attend `{"text":"...","user_id":"..."}` (user_id optionnel)
3. Retourne `{"response":"...","user_id":"..."}`

### `channels/telegram/bot.py`
Objectif: canal Telegram.

1. Vérifie `TELEGRAM_TOKEN`
2. Démarre un bot Telegram (polling)
3. Pour chaque message texte ou commande, appelle `AgentCore.handle_message(...)`

### `daemon/runner.py`
Objectif: point d’entrée unique.

1. Lit `CHANNEL` dans l’environnement
2. Lance `channels.cli.main`, `channels.api.server` ou `channels.telegram.bot`

### `daemon/watcher.py`
Objectif: watcher simple sans dépendance.

1. `watch_dir(path, interval_s=1.0, on_change=...)` parcourt récursivement et détecte les changements par `mtime`
2. `main()` watch `WATCH_DIR` (par défaut `.`) et affiche les changements

### `daemon/ingest.py`
Objectif: ingestion incrémentale vers SQLite.

1. `EpisodicIngestor` lit uniquement les nouvelles lignes de `episodic.jsonl` via un offset en bytes
2. Insère chaque événement dans `events` (SQLite)

### `daemon/habits.py`
Objectif: calcul d habitudes.

1. `compute_daily_habits(...)` calcule messages, heures actives et commandes du jour
2. `compute_week_profile(...)` calcule un profil sur 7 jours

### `daemon/scheduler.py`
Objectif: exécuter des jobs et réagir en temps réel.

1. Démarre un scheduler APScheduler
2. Surveille `episodic.jsonl` via watchdog et déclenche l ingestion
3. Mets à jour des stats périodiquement dans SQLite
