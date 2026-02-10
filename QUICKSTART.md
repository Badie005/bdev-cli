# B.DEV CLI - Quick Start Guide

Welcome to B.DEV CLI - your personal development assistant!

## Installation Complete

You've successfully installed B.DEV CLI. Here's how to use it:

## First Steps

### 1. Test Your Installation

```cmd
bdev --version
```

You should see: `bdev-cli version 0.2.0`

### 2. Start Using B.DEV

```cmd
bdev
```

This will start the interactive REPL (Read-Eval-Print Loop).

### 3. Alternatively, Use Commands Directly

```cmd
bdev hello
bdev version
bdev security-status
```

## Available Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `bdev` | Start interactive REPL (default) |
| `bdev repl` | Start interactive REPL |
| `bdev --version` | Show version |
| `bdev --help` | Show help |

### REPL Commands

When you're in the REPL (after typing `bdev`), you can use:

| Command | Description |
|---------|-------------|
| `help` | List all available commands |
| `exit` or `quit` | Exit the REPL |
| `clear` | Clear the screen |
| `version` | Show CLI version |
| `config` | View or update configuration |
| `security` | Security management |

### Plugin Commands

#### Git Commands
- `git_status` - Show Git status
- `git_log [n]` - Show last n commits
- `git_add <file>` - Stage files
- `git_commit <message>` - Create commit
- `git_diff` - Show changes
- And many more...

#### Todo Commands
- `todo` - List tasks
- `todo add <text>` - Add task
- `todo done <n>` - Complete task

#### Project Commands
- `init <name> <type>` - Create new project

#### System Commands
- `sysinfo` - Show system information
- `doctor` - Run diagnostics

#### Context Commands
- `context show` - Show current context
- `context set <key> <value>` - Set context value

## Command Options

You can use either lowercase or uppercase:

```cmd
bdev --help
B.DEV --help
```

Both work the same way!

## Next Steps

1. **Explore the REPL**: Type `bdev` and then `help` to see all commands
2. **Check system info**: Run `sysinfo` in the REPL
3. **Manage tasks**: Try the todo commands
4. **Configure**: Use the `config` command to customize settings

## Getting Help

If you need help:

```cmd
# Show general help
bdev --help

# Show specific command help
bdev repl --help
```

## Uninstallation

If you want to remove B.DEV CLI:

```powershell
# Run the uninstall script as Administrator
.\uninstall.ps1
```

---

Made with [OK] by B.DEV
