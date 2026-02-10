# B.DEV CLI v1.0.0 - Release Notes

## MAJOR UPDATE - Votre CLI ULTRA-PUISSANT!

B.DEV CLI est maintenant un outil de developpement professionnel avec plus de **150 commandes** et **12 plugins**!

---

## Nouvelles Fonctionnalites

### 1. Plugin Docker
- Gestion complete des conteneurs et images
- Support Docker Compose
- Logs, exec, stats, networks, volumes
- Commandes: status, ps, images, build, run, stop, start, restart, rm, rmi, logs, exec, compose, prune, network, volume, stats

### 2. Plugin NPM
- Gestion complete des packages Node.js
- Scripts automatiques (start, dev, build, test)
- Audit de securite
- Cache management
- Commandes: install, update, uninstall, list, outdated, audit, run, init, clean, cache, version, whoami, search, info, dedupe, link

### 3. Plugin Database
- Support PostgreSQL, MySQL, MongoDB, SQLite
- Migrations automatiques (Django, Alembic, Prisma, Drizzle)
- Backup et restore
- Commandes: status, migrate, seed, backup, restore, schema, connect, query, shell, reset, create, drop, import, export

### 4. Plugin Shell
- Shell integre avec commandes Unix/Windows
- Operations fichiers (ls, cp, mv, rm, mkdir, touch, cat)
- Recherche (grep, find)
- Commandes: exec, ls, cd, pwd, cat, echo, grep, find, cp, mv, rm, mkdir, touch, chmod, history, env, export, which, ps, ping

### 5. Plugin Templates
- Systeme de templates de projets
- 5 templates integres (FastAPI, Flask, Next.js, Express, Selenium)
- Creation de templates personnalises
- Import/Export de templates
- Commandes: list, create, use, delete, export, import, info, builtin

### 6. Plugin Scripts
- Gestion de scripts personnalises
- Support Python, Bash, PowerShell
- Historique d'execution
- Commandes: list, add, run, edit, delete, info, search, export, import

### 7. Plugin Snippets
- Bibliotheque de snippets de code
- Support tous les langages
- Categorisation
- Recherche
- Commandes: list, add, get, edit, delete, search, export, import, languages, categories

### 8. Plugins Existant (Ameliores)
- Git Tools - Commandes Git completes
- Todo List - Gestion de taches
- Project - Creation de projets
- System - Infos systeme
- Context - Gestion de contexte
- Security - MFA, Sandbox

---

## Ameliorations

### Performance
- Chargement rapide des plugins
- Historique optimise
- Auto-completion amelioree

### Compatibilite
- Mode direct (sans terminal emulator)
- Windows, macOS, Linux
- PowerShell, CMD, Bash, Zsh

### Experience Utilisateur
- Messages d'erreur ameliores
- Aide contextuelle
- Documentation complete

---

## Installation

```powershell
# Installation
.\install.ps1

# Lancer
bdev

# Mode direct (recommande Windows)
bdev-direct
```

---

## Quick Start

```bash
# Voir l'aide
help

# Docker
docker status
docker ps
docker compose up

# NPM
npm install express
npm run dev

# Database
db status
db migrate
db backup backup.sql

# Shell
shell ls
shell exec "git status"

# Templates
templates builtin
templates builtin python-fastapi my-api

# Scripts
scripts add deploy --type py
scripts run deploy

# Snippets
snippets add react-component --language javascript
snippets get react-component
```

---

## Documentation

Documentation complete disponible: `DOCUMENTATION.md`

---

## Statistiques

- **Version**: 1.0.0
- **Plugins**: 12
- **Commandes**: 150+
- **Templates integres**: 5
- **Langages supportes**: Python, JavaScript, TypeScript, Bash, PowerShell
- **Services**: Docker, NPM, Git, Databases

---

## Roadmap

- Plugin Cloud (AWS, GCP, Azure)
- Plugin CI/CD (GitHub Actions, GitLab CI)
- Plugin Monitoring (Prometheus, Grafana)
- Plugin Kubernetes
- Plugin Terraform
- Plugin Ansible
- Plugin Helm
- Plugin API Testing
- Plugin Documentation auto
- Plus de templates integres

---

## Changelog

### v1.0.0 (2026-02-10)
- **MAJOR** - Nouveaux plugins: Docker, NPM, Database, Shell, Templates, Scripts, Snippets
- **MAJOR** - 150+ commandes
- **MAJOR** - 5 templates integres
- **MAJOR** - Mode direct pour Windows
- **MAJOR** - Documentation complete
- Ameliorations de performance
- Ameliorations de compatibilite

### v0.2.0
- Installation globale
- Auto-charge au demarrage
- Support Windows complet

### v0.1.0
- Version initiale
- Plugins de base (Git, Todo, System, Project)

---

**B.DEV CLI v1.0.0 - Votre Assistant de Developpement Personnel**

Pour plus d'information: https://docs.bdev.dev
