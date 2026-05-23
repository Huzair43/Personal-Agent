# Personal Agent

Projet Python minimal, organisé par modules, avec une interface CLI et une API HTTP.

## Prérequis

1. Python 3.11 ou plus récent
2. GEMINI_API_KEY (clé API Google Gemini)

## Installation

1. Cloner le dépôt
2. Optionnel, créer un environnement virtuel
3. Installer les dépendances si tu en ajoutes plus tard

Commande PowerShell

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration

Deux options

1. Modifier `config.json`
2. Utiliser les variables d environnement via un fichier `.env`

Exemple

1. Copier `.env.example` vers `.env`
2. Mettre `GEMINI_API_KEY=votre-clé-api-google`
3. Optionnel, personnaliser `GEMINI_MODEL=gemini-3.5-flash` (par défaut)

## Lancer

CLI

```
python -m channels.cli.main
```

API

```
python -m channels.api.server
```

Runner

```
$env:CHANNEL="cli"
python -m daemon.runner
```

Scheduler

```
$env:CHANNEL="scheduler"
python -m daemon.runner
```

Telegram

```
$env:CHANNEL="telegram"
python -m daemon.runner
```

All in one

```
$env:CHANNEL="all"
python -m daemon.runner
```

All in one with CLI

```
$env:CHANNEL="all-cli"
python -m daemon.runner
```

## API

1. GET `/health`
2. POST `/chat` avec un JSON contenant `text` et optionnellement `user_id`

Exemple curl

```
curl http://127.0.0.1:8080/health
curl -X POST http://127.0.0.1:8080/chat -H "Content-Type: application/json" -d "{\"text\":\"salut\",\"user_id\":\"demo\"}"
```

## Notes

1. Le canal API utilise FastAPI et uvicorn.
2. Le scheduler peut être lancé seul via `CHANNEL=scheduler` ou automatiquement en arrière plan quand `CHANNEL=api` (modifiable avec `ENABLE_SCHEDULER_IN_API=0`).
3. `CHANNEL=all` lance API et scheduler dans un seul process.
4. `CHANNEL=all-cli` lance CLI et scheduler dans un seul process.
5. `CHANNEL=telegram` lance le bot Telegram (polling).

## Commandes CLI

1. `/help`
2. `/plan <sujet>`
3. `/review <texte ou chemin/fichier>`
4. `/doc <chemin/fichier> [objectif]`
5. `/git status` ou `/git log`
6. `/remember cle=valeur`
7. `/recall mot`
8. `/habits today` ou `/habits week`

## Documentation

Voir `STRUCTURE.md` pour les détails de l organisation du code.
