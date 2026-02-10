"""
Database Plugin for B.DEV CLI

Provides database management commands for various databases.
"""

import subprocess
import json
from typing import Any, Optional
from pathlib import Path

from cli.plugins import PluginBase
from cli.utils.ui import console


class DatabasePlugin(PluginBase):
    """Plugin for database management and operations."""

    @property
    def name(self) -> str:
        return "db"

    @property
    def description(self) -> str:
        return "Database management (migrate, seed, backup, restore, schema, etc.)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute database commands."""
        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "status":
                self._status()
            elif command == "migrate":
                self._migrate(*sub_args)
            elif command == "seed":
                self._seed(*sub_args)
            elif command == "backup":
                self._backup(*sub_args)
            elif command == "restore":
                self._restore(*sub_args)
            elif command == "schema":
                self._schema(*sub_args)
            elif command == "connect":
                self._connect(*sub_args)
            elif command == "query":
                self._query(*sub_args)
            elif command == "shell":
                self._shell(*sub_args)
            elif command == "reset":
                self._reset()
            elif command == "create":
                self._create(*sub_args)
            elif command == "drop":
                self._drop(*sub_args)
            elif command == "import":
                self._import_data(*sub_args)
            elif command == "export":
                self._export_data(*sub_args)
            else:
                console.error(f"Unknown command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Database command failed: {e}")

    def _detect_database_type(self) -> Optional[str]:
        """Detect the type of database from project files."""
        files = Path(".").iterdir()

        if any(
            f.name == "Dockerfile" and f.read_text().find("postgres") > -1
            for f in files
            if f.is_file()
        ):
            return "postgresql"
        if any(
            f.name == "Dockerfile" and f.read_text().find("mysql") > -1
            for f in files
            if f.is_file()
        ):
            return "mysql"
        if any(
            f.name == "Dockerfile" and f.read_text().find("mongodb") > -1
            for f in files
            if f.is_file()
        ):
            return "mongodb"
        if Path("db.sqlite").exists():
            return "sqlite"
        if any(f.name == "migrations" for f in files if f.is_dir()):
            return "orm"

        return None

    def _status(self) -> None:
        """Show database connection status."""
        db_type = self._detect_database_type()

        if not db_type:
            console.warning("No database detected in current project")
            console.muted("Supported: PostgreSQL, MySQL, MongoDB, SQLite")
            return

        rows = [
            ["Database Type", db_type.upper()],
            ["Status", "Connected" if db_type else "Not configured"],
        ]

        if db_type == "sqlite":
            if Path("db.sqlite").exists():
                rows.append(["File", "db.sqlite"])
                size = Path("db.sqlite").stat().st_size
                rows.append(["Size", f"{size:,} bytes"])

        console.table("Database Status", ["Property", "Value"], rows)

    def _migrate(self, *args: str) -> None:
        """Run database migrations."""
        console.info("Running database migrations...")

        if Path("manage.py").exists():
            console.info("Detected Django project")
            self._run_command(["python", "manage.py", "migrate"])
        elif Path("alembic.ini").exists():
            console.info("Detected Alembic (SQLAlchemy)")
            self._run_command(["alembic", "upgrade", "head"])
        elif Path("node_modules/prisma").exists():
            console.info("Detected Prisma")
            self._run_command(["npx", "prisma", "migrate", "dev"])
        elif Path("node_modules/.prisma").exists():
            console.info("Detected Prisma")
            self._run_command(["npx", "prisma", "migrate", "dev"])
        elif Path("drizzle.config.ts").exists():
            console.info("Detected Drizzle ORM")
            self._run_command(["npx", "drizzle-kit", "push"])
        else:
            console.warning("No migration tool detected")
            console.muted("Supported: Django, Alembic, Prisma, Drizzle")

    def _seed(self, *args: str) -> None:
        """Seed database with initial data."""
        console.info("Seeding database...")

        if Path("manage.py").exists():
            self._run_command(
                ["python", "manage.py", "loaddata"] + list(args)
                if args
                else ["python", "manage.py", "loaddata", "seed"]
            )
        elif Path("prisma/seed.ts").exists():
            self._run_command(["npx", "ts-node", "prisma/seed.ts"])
        else:
            console.warning("No seeder script found")
            console.muted("Create a seed script for your database")

    def _backup(self, *args: str) -> None:
        """Backup database."""
        db_type = self._detect_database_type()
        output = args[0] if args else f"backup_{self._get_timestamp()}.sql"

        console.info(f"Creating backup: {output}")

        if db_type == "postgresql":
            self._run_command(
                ["pg_dump", "-h", "localhost", "-U", "postgres", "-f", output, "dbname"]
            )
        elif db_type == "mysql":
            self._run_command(["mysqldump", "-u", "root", "-p", "dbname", ">", output])
        elif db_type == "sqlite":
            import shutil

            if Path("db.sqlite").exists():
                shutil.copy("db.sqlite", output)
                console.success(f"Backup created: {output}")
        else:
            console.warning(f"Backup not implemented for {db_type}")

    def _restore(self, *args: str) -> None:
        """Restore database from backup."""
        if not args:
            console.error("Usage: db restore <backup_file>")
            return

        backup_file = args[0]
        if not Path(backup_file).exists():
            console.error(f"Backup file not found: {backup_file}")
            return

        db_type = self._detect_database_type()
        console.info(f"Restoring from: {backup_file}")

        if db_type == "postgresql":
            self._run_command(
                [
                    "psql",
                    "-h",
                    "localhost",
                    "-U",
                    "postgres",
                    "-d",
                    "dbname",
                    "-f",
                    backup_file,
                ]
            )
        elif db_type == "mysql":
            self._run_command(["mysql", "-u", "root", "-p", "dbname", "<", backup_file])
        elif db_type == "sqlite":
            import shutil

            shutil.copy(backup_file, "db.sqlite")
            console.success("Database restored")
        else:
            console.warning(f"Restore not implemented for {db_type}")

    def _schema(self, *args: str) -> None:
        """Show database schema."""
        db_type = self._detect_database_type()

        if db_type == "postgresql":
            self._run_command(
                [
                    "psql",
                    "-h",
                    "localhost",
                    "-U",
                    "postgres",
                    "-d",
                    "dbname",
                    "-c",
                    "\dt",
                ]
            )
        elif db_type == "mysql":
            self._run_command(
                ["mysql", "-u", "root", "-p", "dbname", "-e", "SHOW TABLES;"]
            )
        elif db_type == "sqlite":
            if Path("db.sqlite").exists():
                self._run_command(["sqlite3", "db.sqlite", ".schema"])
        elif db_type == "orm":
            if Path("manage.py").exists():
                self._run_command(["python", "manage.py", "showmigrations"])
            elif Path("node_modules/prisma").exists():
                self._run_command(["npx", "prisma", "studio"])

    def _connect(self, *args: str) -> None:
        """Connect to database interactive shell."""
        db_type = self._detect_database_type()

        console.info(f"Connecting to {db_type} database...")

        if db_type == "postgresql":
            self._run_command(
                ["psql", "-h", "localhost", "-U", "postgres", "-d", "dbname"],
                capture=False,
            )
        elif db_type == "mysql":
            self._run_command(["mysql", "-u", "root", "-p", "dbname"], capture=False)
        elif db_type == "sqlite":
            if Path("db.sqlite").exists():
                self._run_command(["sqlite3", "db.sqlite"], capture=False)
        elif db_type == "mongodb":
            self._run_command(["mongosh"], capture=False)

    def _query(self, *args: str) -> None:
        """Execute SQL query."""
        if not args:
            console.error("Usage: db query 'SELECT * FROM users'")
            return

        query = " ".join(args)
        console.info(f"Executing: {query}")

        db_type = self._detect_database_type()

        if db_type == "postgresql":
            self._run_command(
                [
                    "psql",
                    "-h",
                    "localhost",
                    "-U",
                    "postgres",
                    "-d",
                    "dbname",
                    "-c",
                    query,
                ]
            )
        elif db_type == "mysql":
            self._run_command(["mysql", "-u", "root", "-p", "dbname", "-e", query])
        elif db_type == "sqlite":
            if Path("db.sqlite").exists():
                self._run_command(["sqlite3", "db.sqlite", query])

    def _shell(self, *args: str) -> None:
        """Open database shell."""
        self._connect(*args)

    def _reset(self) -> None:
        """Reset database (drop and recreate)."""
        console.warning("[!] This will DELETE all data!")
        confirmation = input("Are you sure? (yes/no): ")

        if confirmation.lower() != "yes":
            console.info("Operation cancelled")
            return

        console.info("Resetting database...")

        if Path("manage.py").exists():
            self._run_command(["python", "manage.py", "flush"])
        elif Path("db.sqlite").exists():
            Path("db.sqlite").unlink()
            console.success("Database reset")
            console.muted("Run migrations to recreate tables")

    def _create(self, *args: str) -> None:
        """Create new database."""
        if not args:
            console.error("Usage: db create <database_name>")
            return

        db_name = args[0]
        console.info(f"Creating database: {db_name}")

        db_type = self._detect_database_type()

        if db_type == "postgresql":
            self._run_command(
                ["createdb", "-h", "localhost", "-U", "postgres", db_name]
            )
        elif db_type == "mysql":
            self._run_command(
                ["mysql", "-u", "root", "-p", "-e", f"CREATE DATABASE {db_name};"]
            )
        else:
            console.warning(f"Create not implemented for {db_type}")

    def _drop(self, *args: str) -> None:
        """Drop database."""
        if not args:
            console.error("Usage: db drop <database_name>")
            return

        db_name = args[0]
        console.warning(f"[!] This will DELETE database: {db_name}")
        confirmation = input("Are you sure? (yes/no): ")

        if confirmation.lower() != "yes":
            console.info("Operation cancelled")
            return

        console.info(f"Dropping database: {db_name}")

        db_type = self._detect_database_type()

        if db_type == "postgresql":
            self._run_command(["dropdb", "-h", "localhost", "-U", "postgres", db_name])
        elif db_type == "mysql":
            self._run_command(
                ["mysql", "-u", "root", "-p", "-e", f"DROP DATABASE {db_name};"]
            )

    def _import_data(self, *args: str) -> None:
        """Import data from file."""
        if not args:
            console.error("Usage: db import <file>")
            return

        file_path = args[0]
        if not Path(file_path).exists():
            console.error(f"File not found: {file_path}")
            return

        console.info(f"Importing from: {file_path}")
        self._restore(file_path)

    def _export_data(self, *args: str) -> None:
        """Export data to file."""
        table = args[0] if args else None
        output = args[1] if len(args) > 1 else f"export_{self._get_timestamp()}.csv"

        console.info(f"Exporting to: {output}")

        db_type = self._detect_database_type()

        if db_type == "postgresql" and table:
            self._run_command(
                [
                    "psql",
                    "-h",
                    "localhost",
                    "-U",
                    "postgres",
                    "-d",
                    "dbname",
                    "-c",
                    f"COPY {table} TO STDOUT WITH CSV HEADER",
                    ">",
                    output,
                ]
            )
        elif db_type == "mysql" and table:
            self._run_command(
                [
                    "mysql",
                    "-u",
                    "root",
                    "-p",
                    "dbname",
                    "-e",
                    f"SELECT * FROM {table} INTO OUTFILE '{output}' FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n'",
                ]
            )
        else:
            console.warning("Export requires table name for SQL databases")

    def _run_command(self, cmd: list, capture: bool = False) -> str:
        """Run a database command."""
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, check=False)
            return ""

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime

        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _show_help(self) -> None:
        """Show database command help."""
        rows = [
            ["status", "Show database status"],
            ["migrate", "Run migrations"],
            ["seed", "Seed database with data"],
            ["backup [file]", "Backup database"],
            ["restore <file>", "Restore from backup"],
            ["schema", "Show database schema"],
            ["connect", "Connect to database shell"],
            ["query 'SQL'", "Execute SQL query"],
            ["shell", "Open database shell"],
            ["reset", "Reset database (drop all)"],
            ["create <name>", "Create new database"],
            ["drop <name>", "Drop database"],
            ["import <file>", "Import data from file"],
            ["export <table> [file]", "Export table to CSV"],
        ]
        console.table("Database Commands", ["Command", "Description"], rows)
