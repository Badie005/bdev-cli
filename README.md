# B.DEV CLI v1.0.0

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**B.DEV CLI** - Votre Assistant de Developpement Personnel

Un CLI **ultra-puissant** avec plus de **150 commandes** et **12 plugins**!

---

## [OK] Installation Complete!

B.DEV est deja installe sur votre systeme. Pour l'utiliser:

```powershell
# Lancer B.DEV
bdev

# Ou en mode direct (recommande Windows)
bdev-direct

# Voir la version
bdev --version
```

---

## Nouveautes v1.0.0

### Nouveaux Plugins

1. **Docker** - Gestion complete des conteneurs
2. **NPM** - Gestion packages Node.js
3. **Database** - Migrations, backup, restore
4. **Shell** - Commandes systeme integrees
5. **Templates** - 5 templates integres
6. **Scripts** - Scripts personnalises
7. **Snippets** - Bibliotheque de code

### Plugins Existant (Ameliores)

8. **Git Tools** - Commandes Git completes
9. **Todo List** - Gestion de taches
10. **Project** - Creation de projets
11. **System** - Infos systeme
12. **Context** - Gestion de contexte

---

## Quick Start

```bash
# Aide
help

# Docker
docker status
docker ps
docker run -p 8080:80 nginx

# NPM
npm install express
npm run dev

# Database
db status
db migrate

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

## Commandes Disponibles

### Docker
```
docker status, ps, images, build, run, stop, start,
docker restart, rm, rmi, logs, exec, compose, prune,
docker network, volume, stats
```

### NPM
```
npm install, update, uninstall, list, outdated,
npm audit, run, start, dev, build, test, init,
npm clean, cache, version, whoami, search, info, dedupe, link
```

### Database
```
db status, migrate, seed, backup, restore, schema,
db connect, query, shell, reset, create, drop, import, export
```

### Shell
```
shell exec, ls, cd, pwd, cat, echo, grep, find,
shell cp, mv, rm, mkdir, touch, chmod, history,
shell env, export, which, ps, ping
```

### Templates
```
templates list, create, use, delete, export, import,
templates info, builtin
```

### Scripts
```
scripts list, add, run, edit, delete, info,
scripts search, export, import
```

### Snippets
```
snippets list, add, get, edit, delete, search,
snippets export, import, languages, categories
```

---

## Templates Integres

| Template | Description |
|----------|-------------|
| `python-fastapi` | Application FastAPI |
| `python-flask` | Application Flask |
| `nextjs` | Application Next.js |
| `node-express` | Serveur Express |
| `python-selenium` | Selenium automation |

---

## Statistiques

- **Version**: 1.0.0
- **Plugins**: 12
- **Commandes**: 150+
- **Templates**: 5 integres
- **Langages**: Python, JavaScript, TypeScript, Bash, PowerShell
- **Services**: Docker, NPM, Git, Databases

---

## Documentation

- **[Documentation Complete](DOCUMENTATION.md)** - Toutes les commandes
- **[Release Notes](RELEASE-NOTES.md)** - Changements
- **[Quick Start](QUICKSTART.md)** - Guide rapide

---

## Fonctionnalites Avancees

- [OK] Historique persistant des commandes
- [OK] Auto-completion
- [OK] Mode direct (Windows compatible)
- [OK] Mode REPL (feature complete)
- [OK] Gestion de securite (MFA, Sandbox)
- [OK] Configuration personnalisee
- [OK] Contexte de projet
- [OK] Scripts personnalises
- [OK] Snippets de code
- [OK] Templates de projets

---

## Troubleshooting

### "bdev not found"
```powershell
# Charger dans session actuelle
& "C:\Users\B.LAPTOP\Dev\Projects\bdev-cli\use-bdev-now.ps1"
```

### REPL ne fonctionne pas
```powershell
# Utiliser le mode direct
bdev-direct
```

### Besoin d'aide
```powershell
# Aide generale
bdev --help

# Aide dans le REPL
help
```

---

## Roadmap

- [ ] Plugin Cloud (AWS, GCP, Azure)
- [ ] Plugin CI/CD (GitHub Actions, GitLab CI)
- [ ] Plugin Monitoring (Prometheus, Grafana)
- [ ] Plugin Kubernetes
- [ ] Plugin Terraform
- [ ] Plugin Ansible
- [ ] Plugin Helm
- [ ] Plugin API Testing
- [ ] Documentation auto
- [ ] Plus de templates

---

## Contributeurs

- **B.DEV** - Createur principal

## License

MIT License

---

**B.DEV CLI v1.0.0** - Votre Assistant de Developpement Personnel

Pour plus d'information: https://docs.bdev.dev

**[OK] Amusez-vous bien!**
