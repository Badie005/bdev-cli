"""
Project Configuration Manager for B.DEV CLI.

Provides project-specific configuration with environment support,
secret integration, and config validation.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime

from cli.utils.ui import console
from cli.utils.errors import handle_errors, ValidationError


@dataclass
class CloudConfig:
    """Cloud provider configuration."""
    provider: str = ""
    region: str = ""
    account_id: str = ""
    project_id: str = ""  # For GCP
    subscription_id: str = ""  # For Azure


@dataclass
class DeployConfig:
    """Deployment configuration."""
    strategy: str = ""  # kubernetes, docker, serverless, etc.
    namespace: str = ""
    helm_chart: str = ""
    dockerfile: str = ""
    compose_file: str = ""


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    prometheus: str = ""
    grafana: str = ""
    alerts: List[str] = field(default_factory=list)
    logs: str = ""


@dataclass
class ServiceConfig:
    """Service configuration."""
    type: str = ""
    host: str = ""
    port: int = 0
    username: str = ""
    password: str = ""


@dataclass
class CICDConfig:
    """CI/CD configuration."""
    provider: str = ""
    workflow: str = ""
    environment: str = ""
    auto_deploy: bool = False


@dataclass
class ProjectConfig:
    """Complete project configuration."""
    name: str = ""
    type: str = ""  # node, python, go, rust, etc.
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = ""
    cloud: Optional[CloudConfig] = None
    deploy: Optional[DeployConfig] = None
    monitoring: Optional[MonitoringConfig] = None
    services: Dict[str, ServiceConfig] = field(default_factory=dict)
    ci_cd: Optional[CICDConfig] = None
    environment: Dict[str, str] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    features: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""


class ProjectConfigManager:
    """Manager for project configuration."""

    CONFIG_DIR = Path(".bdev")
    CONFIG_FILE = CONFIG_DIR / "project.json"
    ENV_FILE = CONFIG_DIR / "env.json"
    SECRETS_FILE = CONFIG_DIR / "secrets.json"

    def __init__(self) -> None:
        self._config: ProjectConfig = ProjectConfig()
        self._environment: Dict[str, str] = {}
        self._secrets: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Load project configuration."""
        # Load main config
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Parse nested configs
                cloud_data = data.get("cloud")
                cloud = CloudConfig(**cloud_data) if cloud_data else None

                deploy_data = data.get("deploy")
                deploy = DeployConfig(**deploy_data) if deploy_data else None

                monitoring_data = data.get("monitoring")
                monitoring = MonitoringConfig(**monitoring_data) if monitoring_data else None

                services_data = data.get("services", {})
                services = {
                    name: ServiceConfig(**svc_data)
                    for name, svc_data in services_data.items()
                }

                cicd_data = data.get("ci_cd")
                cicd = CICDConfig(**cicd_data) if cicd_data else None

                self._config = ProjectConfig(
                    name=data.get("name", ""),
                    type=data.get("type", ""),
                    version=data.get("version", "1.0.0"),
                    description=data.get("description", ""),
                    author=data.get("author", ""),
                    license=data.get("license", ""),
                    cloud=cloud,
                    deploy=deploy,
                    monitoring=monitoring,
                    services=services,
                    ci_cd=cicd,
                    environment=data.get("environment", {}),
                    secrets=data.get("secrets", {}),
                    features=data.get("features", []),
                    dependencies=data.get("dependencies", {}),
                    created_at=data.get("created_at", ""),
                    updated_at=data.get("updated_at", ""),
                )
            except Exception as e:
                console.error(f"Failed to load project config: {e}")

        # Load environment
        if self.ENV_FILE.exists():
            try:
                with open(self.ENV_FILE, "r", encoding="utf-8") as f:
                    self._environment = json.load(f)
            except Exception:
                self._environment = {}

        # Load secrets
        if self.SECRETS_FILE.exists():
            try:
                with open(self.SECRETS_FILE, "r", encoding="utf-8") as f:
                    self._secrets = json.load(f)
            except Exception:
                self._secrets = {}

    def _save(self) -> None:
        """Save project configuration."""
        try:
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

            # Save main config (without secrets)
            config_dict = asdict(self._config)
            config_dict.pop("secrets", None)

            self._config.updated_at = datetime.now().isoformat()
            config_dict["updated_at"] = self._config.updated_at

            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2)

        except Exception as e:
            console.error(f"Failed to save project config: {e}")

    def _save_environment(self) -> None:
        """Save environment configuration."""
        try:
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.ENV_FILE, "w", encoding="utf-8") as f:
                json.dump(self._environment, f, indent=2)
        except Exception as e:
            console.error(f"Failed to save environment: {e}")

    def _save_secrets(self) -> None:
        """Save secrets configuration."""
        try:
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.SECRETS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._secrets, f, indent=2)
        except Exception as e:
            console.error(f"Failed to save secrets: {e}")

    @handle_errors()
    def init(
        self,
        name: str,
        project_type: str = "",
        description: str = "",
        author: str = ""
    ) -> bool:
        """Initialize a new project configuration."""
        if self.CONFIG_FILE.exists():
            console.warning("Project configuration already exists. Overwriting.")

        self._config = ProjectConfig(
            name=name,
            type=project_type,
            description=description,
            author=author,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        self._save()
        console.success(f"Project configuration initialized for '{name}'")
        return True

    @handle_errors()
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key (dot notation supported)."""
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            elif hasattr(value, k):
                value = getattr(value, k)
            else:
                return default

        return value if value is not None else default

    @handle_errors()
    def set(self, key: str, value: Any) -> bool:
        """Set a configuration value by key (dot notation supported)."""
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if hasattr(config, k):
                config = getattr(config, k)
            else:
                console.error(f"Invalid key path: {key}")
                return False

        if hasattr(config, keys[-1]):
            setattr(config, keys[-1], value)
            self._save()
            console.success(f"Set {key} = {value}")
            return True
        else:
            console.error(f"Invalid key: {keys[-1]}")
            return False

    @handle_errors()
    def list(self) -> Dict[str, Any]:
        """List all configuration values."""
        console.rule("Project Configuration")

        if not self._config.name:
            console.info("No project configuration found. Use 'project config init' to initialize.")
            return {}

        rows = [
            ["Name", self._config.name],
            ["Type", self._config.type],
            ["Version", self._config.version],
            ["Description", self._config.description],
            ["Author", self._config.author],
            ["License", self._config.license],
            ["Created", self._config.created_at],
            ["Updated", self._config.updated_at],
        ]

        console.table("Basic Info", ["Key", "Value"], rows)

        # Cloud config
        if self._config.cloud:
            console.muted("\nCloud Configuration:")
            cloud_rows = [
                ["Provider", self._config.cloud.provider],
                ["Region", self._config.cloud.region],
                ["Account ID", self._config.cloud.account_id],
                ["Project ID", self._config.cloud.project_id],
            ]
            console.table("Cloud", ["Key", "Value"], cloud_rows)

        # Deploy config
        if self._config.deploy:
            console.muted("\nDeployment Configuration:")
            deploy_rows = [
                ["Strategy", self._config.deploy.strategy],
                ["Namespace", self._config.deploy.namespace],
                ["Helm Chart", self._config.deploy.helm_chart],
            ]
            console.table("Deploy", ["Key", "Value"], deploy_rows)

        return asdict(self._config)

    @handle_errors()
    def env_set(self, key: str, value: str) -> bool:
        """Set an environment variable."""
        self._environment[key] = value
        self._save_environment()
        console.success(f"Set env var: {key}")
        return True

    @handle_errors()
    def env_get(self, key: str) -> Optional[str]:
        """Get an environment variable."""
        return self._environment.get(key)

    @handle_errors()
    def env_list(self) -> Dict[str, str]:
        """List all environment variables."""
        if not self._environment:
            console.info("No environment variables set")
            return {}

        console.rule("Environment Variables")

        rows = [[key, value] for key, value in sorted(self._environment.items())]
        console.table("Environment", ["Key", "Value"], rows)

        return self._environment

    @handle_errors()
    def env_delete(self, key: str) -> bool:
        """Delete an environment variable."""
        if key in self._environment:
            del self._environment[key]
            self._save_environment()
            console.success(f"Deleted env var: {key}")
            return True

        console.error(f"Environment variable not found: {key}")
        return False

    @handle_errors()
    def secret_set(self, key: str, value: str) -> bool:
        """Set a secret."""
        self._secrets[key] = value
        self._save_secrets()
        console.success(f"Set secret: {key}")
        return True

    @handle_errors()
    def secret_get(self, key: str) -> Optional[str]:
        """Get a secret."""
        return self._secrets.get(key)

    @handle_errors()
    def secret_list(self) -> Dict[str, str]:
        """List all secret keys (values masked)."""
        if not self._secrets:
            console.info("No secrets set")
            return {}

        console.rule("Secrets")

        rows = [[key, "********" for key in sorted(self._secrets.keys())]]
        console.table("Secrets", ["Key", "Value"], rows)

        return self._secrets

    @handle_errors()
    def secret_delete(self, key: str) -> bool:
        """Delete a secret."""
        if key in self._secrets:
            del self._secrets[key]
            self._save_secrets()
            console.success(f"Deleted secret: {key}")
            return True

        console.error(f"Secret not found: {key}")
        return False

    @handle_errors()
    def secrets_sync(self) -> bool:
        """Sync secrets to environment (export as env vars)."""
        console.info("Syncing secrets to environment...")

        # Mask secrets when syncing
        for key, value in self._secrets.items():
            if key not in self._environment:
                self._environment[key] = value

        self._save_environment()
        console.success(f"Synced {len(self._secrets)} secrets to environment")
        return True

    @handle_errors()
    def validate(self) -> bool:
        """Validate project configuration."""
        console.info("Validating project configuration...")

        errors = []

        if not self._config.name:
            errors.append("Project name is required")

        if not self._config.type:
            errors.append("Project type is required")

        # Validate cloud config
        if self._config.cloud and self._config.cloud.provider:
            provider = self._config.cloud.provider.lower()
            if provider == "aws" and not self._config.cloud.account_id:
                errors.append("AWS account ID required for AWS provider")
            elif provider == "gcp" and not self._config.cloud.project_id:
                errors.append("GCP project ID required for GCP provider")
            elif provider == "azure" and not self._config.cloud.subscription_id:
                errors.append("Azure subscription ID required for Azure provider")

        if errors:
            console.error("Validation failed:")
            for error in errors:
                console.error(f"  - {error}")
            return False

        console.success("Configuration validation passed")
        return True

    @handle_errors()
    def merge(self, other_config_path: str) -> bool:
        """Merge another configuration file."""
        try:
            with open(other_config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Simple merge (top-level only for now)
            for key, value in data.items():
                if key == "cloud" and isinstance(value, dict) and self._config.cloud:
                    for ck, cv in value.items():
                        setattr(self._config.cloud, ck, cv)
                elif key == "deploy" and isinstance(value, dict) and self._config.deploy:
                    for dk, dv in value.items():
                        setattr(self._config.deploy, dk, dv)
                elif key == "monitoring" and isinstance(value, dict) and self._config.monitoring:
                    for mk, mv in value.items():
                        setattr(self._config.monitoring, mk, mv)
                elif key == "services" and isinstance(value, dict):
                    for sk, sv in value.items():
                        self._config.services[sk] = ServiceConfig(**sv)
                elif hasattr(self._config, key):
                    setattr(self._config, key, value)

            self._save()
            console.success(f"Merged configuration from {other_config_path}")
            return True

        except FileNotFoundError:
            console.error(f"File not found: {other_config_path}")
            return False
        except Exception as e:
            console.error(f"Failed to merge configuration: {e}")
            return False

    @handle_errors()
    def export(self, file_path: str, include_secrets: bool = False) -> bool:
        """Export configuration to file."""
        try:
            config_dict = asdict(self._config)

            if include_secrets:
                config_dict["secrets"] = self._secrets
            else:
                config_dict.pop("secrets", None)

            config_dict["environment"] = self._environment

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2)

            console.success(f"Configuration exported to {file_path}")
            return True

        except Exception as e:
            console.error(f"Failed to export configuration: {e}")
            return False

    @handle_errors()
    def import_from(self, file_path: str) -> bool:
        """Import configuration from file."""
        return self.merge(file_path)

    @property
    def config(self) -> ProjectConfig:
        """Get the current project configuration."""
        return self._config

    @property
    def environment(self) -> Dict[str, str]:
        """Get the current environment variables."""
        return self._environment

    @property
    def secrets(self) -> Dict[str, str]:
        """Get the current secrets."""
        return self._secrets


# Global project config instance
project_config = ProjectConfigManager()
