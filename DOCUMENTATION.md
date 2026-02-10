# B.DEV CLI - Documentation Complète

Version: 0.2.0

## Nouveautés

B.DEV CLI est maintenant un CLI **ultra-puissant** avec plus de **12 plugins** et des centaines de commandes!

---

## Plugins Disponibles

### 1. Core Commands
| Command | Description |
|---------|-------------|
| `help` | Liste toutes les commandes |
| `exit` / `quit` | Quitte le REPL |
| `clear` | Efface l'ecran |
| `version` | Affiche la version |
| `config` | Configuration |
| `security` | Securite |

### 2. Git Tools (`git_*`)
| Command | Description |
|---------|-------------|
| `git_status` | Statut Git |
| `git_log [n]` | Derniers commits |
| `git_add <file>` | Stage fichiers |
| `git_commit <msg>` | Commit |
| `git_diff [file]` | Changements |
| `git_branch [name]` | Branches |
| `git_checkout <branch>` | Switch branch |
| `git_stash [save|pop|list]` | Stash |
| `git_pull` | Pull |
| `git_push` | Push |
| `git_remote` | Remotes |

### 3. Todo List (`todo`)
| Command | Description |
|---------|-------------|
| `todo` | Liste des taches |
| `todo add <text>` | Ajouter tache |
| `todo done <n>` | Completer tache |
| `todo clear` | Effacer completes |

### 4. System (`sysinfo`)
| Command | Description |
|---------|-------------|
| `sysinfo` | Infos systeme |
| `doctor` | Diagnostics |
| `context show` | Contexte actuel |
| `context set <k> <v>` | Definir contexte |

### 5. Project (`init`)
| Command | Description |
|---------|-------------|
| `init <name> <type>` | Creer projet |

### 6. Docker (`docker`)
| Command | Description |
|---------|-------------|
| `docker status` | Statut Docker |
| `docker ps [all]` | Liste conteneurs |
| `docker images` | Liste images |
| `docker build <path> [tag]` | Build image |
| `docker run <image> [cmd]` | Run conteneur |
| `docker stop <id...>` | Stop conteneurs |
| `docker start <id...>` | Start conteneurs |
| `docker restart <id...>` | Restart |
| `docker rm <id...>` | Remove conteneurs |
| `docker rmi <id...>` | Remove images |
| `docker logs <id> [--follow]` | Logs |
| `docker exec <id> <cmd>` | Exec dans conteneur |
| `docker compose <up|down|...>` | Docker Compose |
| `docker prune` | Nettoyer |
| `docker network [ls|create|rm]` | Networks |
| `docker volume [ls|create|rm]` | Volumes |
| `docker stats [id]` | Stats ressources |

### 7. NPM (`npm`)
| Command | Description |
|---------|-------------|
| `npm install [pkg]` | Installer packages |
| `npm update [pkg]` | Mettre a jour |
| `npm uninstall <pkg>` | Desinstaller |
| `npm list` | Liste installes |
| `npm outdated` | Packages obsoltes |
| `npm audit [--fix]` | Audit securite |
| `npm run <script>` | Run script |
| `npm start` | Run start script |
| `npm dev` | Run dev script |
| `npm build` | Run build script |
| `npm test` | Run tests |
| `npm init [name]` | Init package.json |
| `npm clean` | Clean & reinstall |
| `npm cache [clean|verify]` | Cache |
| `npm version` | Versions |
| `npm whoami` | Username npm |
| `npm search <query>` | Search packages |
| `npm info <pkg>` | Info package |
| `npm dedupe` | Deduplicate |
| `npm link [pkg]` | Link packages |

### 8. Database (`db`)
| Command | Description |
|---------|-------------|
| `db status` | Statut BDD |
| `db migrate` | Migrations |
| `db seed` | Seeding |
| `db backup [file]` | Backup |
| `db restore <file>` | Restore |
| `db schema` | Schema |
| `db connect` | Connect shell |
| `db query 'SQL'` | Executer SQL |
| `db shell` | Shell BDD |
| `db reset` | Reset BDD |
| `db create <name>` | Creer BDD |
| `db drop <name>` | Drop BDD |
| `db import <file>` | Importer |
| `db export <table> [file]` | Exporter |

### 9. Shell (`shell`)
| Command | Description |
|---------|-------------|
| `shell exec <cmd>` | Executer commande |
| `shell ls [path]` | Liste fichiers |
| `shell cd <path>` | Changer repertoire |
| `shell pwd` | Repertoire actuel |
| `shell cat <file>` | Afficher fichier |
| `shell grep <pat> <file>` | Chercher |
| `shell find <name>` | Trouver fichiers |
| `shell cp <src> <dst>` | Copier |
| `shell mv <src> <dst>` | Deplacer |
| `shell rm <path>` | Supprimer |
| `shell mkdir <dir>` | Creer dossier |
| `shell touch <file>` | Creer fichier |
| `shell env [var]` | Variables env |
| `shell which <cmd>` | Trouver commande |
| `shell ps` | Processus |
| `shell ping <host>` | Ping |

### 10. Templates (`templates`)
| Command | Description |
|---------|-------------|
| `templates list` | Lister templates |
| `templates create <name> [desc]` | Creer template |
| `templates use <template> <name>` | Utiliser template |
| `templates delete <template>` | Supprimer |
| `templates export <template>` | Exporter |
| `templates import <zip>` | Importer |
| `templates info <template>` | Info template |
| `templates builtin` | Templates integres |
| `templates builtin <name> <project>` | Creer depuis builtin |

**Templates integres:**
- `python-fastapi` - Application FastAPI
- `python-flask` - Application Flask
- `nextjs` - Application Next.js
- `node-express` - Serveur Express
- `python-selenium` - Selenium automation

### 11. Scripts (`scripts`)
| Command | Description |
|---------|-------------|
| `scripts list [category]` | Lister scripts |
| `scripts add <name> [desc]` | Ajouter script |
| `scripts run <name> [args]` | Executer script |
| `scripts edit <name>` | Editer script |
| `scripts delete <name>` | Supprimer |
| `scripts info <name>` | Info script |
| `scripts search <query>` | Chercher |
| `scripts export [file]` | Exporter |
| `scripts import <file>` | Importer |

**Types de scripts:**
- Python (`.py`)
- Bash (`.sh`)
- PowerShell (`.ps1`)

### 12. Snippets (`snippets`)
| Command | Description |
|---------|-------------|
| `snippets list [lang]` | Lister snippets |
| `snippets add <name> [desc]` | Ajouter snippet |
| `snippets get <name>` | Afficher snippet |
| `snippets edit <name>` | Editer |
| `snippets delete <name>` | Supprimer |
| `snippets search <query>` | Chercher |
| `snippets export [file]` | Exporter |
| `snippets import <file>` | Importer |
| `snippets languages` | Langages dispo |
| `snippets categories` | Categories |

---

## Exemples d'Utilisation

### Docker
```
docker status
docker ps
docker run -p 8080:80 nginx
docker logs my-container --follow
docker compose up
```

### NPM
```
npm install express
npm outdated
npm audit --fix
npm run dev
```

### Database
```
db status
db migrate
db backup backup.sql
db restore backup.sql
```

### Shell
```
shell ls
shell cat README.md
shell exec "git log --oneline"
shell ps
```

### Templates
```
templates builtin
templates builtin python-fastapi my-api
templates create
templates use my-template new-project
```

### Scripts
```
scripts add deploy --category devops --type py
scripts run deploy
scripts edit deploy
```

### Snippets
```
snippets add react-component --language javascript
snippets get react-component
snippets search component
```

---

## Fonctionnalites Avancees

### 1. Historique des Commandes
- Historique persistant dans `~/.bdev/repl_history`
- Auto-completion
- Suggestions depuis l'historique

### 2. Configuration
```
config editor code
config plugins_enabled true
```

### 3. Securite
```
security status
security mfa setup
security sandbox enable
```

### 4. Contexte
```
context show
context set project my-api
context set environment dev
```

---

## Statistiques

- **12 Plugins** integres
- **150+ Commandes** disponibles
- **5 Templates** integres
- Support Python, JavaScript, TypeScript, Bash, PowerShell
- Compatible Docker, NPM, Git, Databases

---

## Installation

```powershell
# Installer
.\install.ps1

# Lancer
bdev

# Ou depuis n'importe ou
B.DEV
```

---

## Documentation

Pour plus d'information:
- `help` dans le REPL
- `--help` pour chaque commande
- Documentation sur https://docs.bdev.dev

---

**B.DEV CLI - Votre Assistant de Developpement Personnel**
