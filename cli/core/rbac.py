"""
RBAC (Role-Based Access Control) System for B.DEV CLI.

Provides comprehensive role and permission management.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

from cli.utils.ui import console
from cli.utils.errors import handle_errors, ValidationError


class Permission(Enum):
    """System permissions."""

    # Command permissions
    COMMAND_EXECUTE = "command:execute"
    COMMAND_SHELL = "command:shell"
    COMMAND_ADMIN = "command:admin"

    # Plugin permissions
    PLUGIN_LOAD = "plugin:load"
    PLUGIN_UNLOAD = "plugin:unload"
    PLUGIN_INSTALL = "plugin:install"

    # Configuration permissions
    CONFIG_READ = "config:read"
    CONFIG_WRITE = "config:write"
    CONFIG_ADMIN = "config:admin"

    # Security permissions
    SECURITY_MFA = "security:mfa"
    SECURITY_AUDIT = "security:audit"
    SECURITY_ADMIN = "security:admin"

    # Deployment permissions
    DEPLOY_READ = "deploy:read"
    DEPLOY_WRITE = "deploy:write"
    DEPLOY_PRODUCTION = "deploy:production"
    DEPLOY_ROLLBACK = "deploy:rollback"

    # Data permissions
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_DELETE = "data:delete"

    # Secret permissions
    SECRET_READ = "secret:read"
    SECRET_WRITE = "secret:write"
    SECRET_DELETE = "secret:delete"

    # Git permissions
    GIT_READ = "git:read"
    GIT_WRITE = "git:write"
    GIT_FORCE = "git:force"

    # System permissions
    SYSTEM_INFO = "system:info"
    SYSTEM_ADMIN = "system:admin"


@dataclass
class Role:
    """Role definition."""

    name: str
    description: str = ""
    permissions: Set[str] = field(default_factory=set)
    inherited_roles: Set[str] = field(default_factory=set)
    created_at: str = ""
    created_by: str = ""


@dataclass
class User:
    """User definition."""

    username: str
    roles: Set[str] = field(default_factory=set)
    created_at: str = ""
    last_login: str = ""
    active: bool = True


@dataclass
class PermissionGrant:
    """Permission grant record."""

    id: str
    permission: str
    role: str
    granted_by: str
    granted_at: str


class RBACManager:
    """Role-Based Access Control manager."""

    ROLES_FILE = Path.home() / ".bdev" / "rbac" / "roles.json"
    USERS_FILE = Path.home() / ".bdev" / "rbac" / "users.json"
    GRANTS_FILE = Path.home() / ".bdev" / "rbac" / "grants.json"

    # Built-in roles
    BUILTIN_ROLES = {
        "admin": {
            "description": "Full system access",
            "permissions": {p.value for p in Permission},
        },
        "developer": {
            "description": "Development access",
            "permissions": {
                Permission.COMMAND_EXECUTE.value,
                Permission.CONFIG_READ.value,
                Permission.DEPLOY_READ.value,
                Permission.DEPLOY_WRITE.value,
                Permission.GIT_READ.value,
                Permission.GIT_WRITE.value,
                Permission.DATA_READ.value,
                Permission.DATA_WRITE.value,
                Permission.SECRET_READ.value,
                Permission.SYSTEM_INFO.value,
            },
        },
        "operator": {
            "description": "Operations access",
            "permissions": {
                Permission.COMMAND_EXECUTE.value,
                Permission.CONFIG_READ.value,
                Permission.DEPLOY_READ.value,
                Permission.DEPLOY_WRITE.value,
                Permission.DEPLOY_PRODUCTION.value,
                Permission.DEPLOY_ROLLBACK.value,
                Permission.GIT_READ.value,
                Permission.SECRET_READ.value,
                Permission.SECRET_WRITE.value,
                Permission.SECURITY_AUDIT.value,
                Permission.SYSTEM_INFO.value,
            },
        },
        "readonly": {
            "description": "Read-only access",
            "permissions": {
                Permission.COMMAND_EXECUTE.value,
                Permission.CONFIG_READ.value,
                Permission.DEPLOY_READ.value,
                Permission.GIT_READ.value,
                Permission.DATA_READ.value,
                Permission.SECRET_READ.value,
                Permission.SYSTEM_INFO.value,
            },
        },
    }

    def __init__(self) -> None:
        self._roles: Dict[str, Role] = {}
        self._users: Dict[str, User] = {}
        self._grants: List[PermissionGrant] = []
        self._ensure_dirs()
        self._load()

    def _ensure_dirs(self) -> None:
        """Create RBAC directories."""
        for file_path in [self.ROLES_FILE, self.USERS_FILE, self.GRANTS_FILE]:
            file_path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> None:
        """Load RBAC data from files."""
        # Load roles
        if self.ROLES_FILE.exists():
            try:
                with open(self.ROLES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for name, role_data in data.items():
                        self._roles[name] = Role(
                            name=name,
                            description=role_data.get("description", ""),
                            permissions=set(role_data.get("permissions", [])),
                            inherited_roles=set(role_data.get("inherited_roles", [])),
                            created_at=role_data.get("created_at", ""),
                            created_by=role_data.get("created_by", ""),
                        )
            except Exception as e:
                console.error(f"Failed to load roles: {e}")

        # Load users
        if self.USERS_FILE.exists():
            try:
                with open(self.USERS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for username, user_data in data.items():
                        self._users[username] = User(
                            username=username,
                            roles=set(user_data.get("roles", [])),
                            created_at=user_data.get("created_at", ""),
                            last_login=user_data.get("last_login", ""),
                            active=user_data.get("active", True),
                        )
            except Exception as e:
                console.error(f"Failed to load users: {e}")

        # Load grants
        if self.GRANTS_FILE.exists():
            try:
                with open(self.GRANTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for grant_data in data:
                        self._grants.append(PermissionGrant(**grant_data))
            except Exception as e:
                console.error(f"Failed to load grants: {e}")

    def _save(self) -> None:
        """Save RBAC data to files."""
        # Save roles
        try:
            with open(self.ROLES_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        name: {
                            "description": role.description,
                            "permissions": list(role.permissions),
                            "inherited_roles": list(role.inherited_roles),
                            "created_at": role.created_at,
                            "created_by": role.created_by,
                        }
                        for name, role in self._roles.items()
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            console.error(f"Failed to save roles: {e}")

        # Save users
        try:
            with open(self.USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        username: {
                            "roles": list(user.roles),
                            "created_at": user.created_at,
                            "last_login": user.last_login,
                            "active": user.active,
                        }
                        for username, user in self._users.items()
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            console.error(f"Failed to save users: {e}")

        # Save grants
        try:
            with open(self.GRANTS_FILE, "w", encoding="utf-8") as f:
                json.dump([asdict(grant) for grant in self._grants], f, indent=2)
        except Exception as e:
            console.error(f"Failed to save grants: {e}")

    @handle_errors()
    def init(self) -> bool:
        """Initialize RBAC with built-in roles."""
        console.info("Initializing RBAC with built-in roles...")

        for role_name, role_config in self.BUILTIN_ROLES.items():
            if role_name not in self._roles:
                self._roles[role_name] = Role(
                    name=role_name,
                    description=role_config["description"],
                    permissions=set(role_config["permissions"]),
                    created_at=datetime.now().isoformat(),
                    created_by="system",
                )

        self._save()
        console.success(f"Initialized {len(self._roles)} built-in roles")
        return True

    @handle_errors()
    def create_role(
        self,
        name: str,
        description: str = "",
        permissions: Optional[List[str]] = None,
        inherited_roles: Optional[List[str]] = None,
        created_by: str = "",
    ) -> Role:
        """Create a new role."""
        if name in self._roles:
            console.warning(f"Role '{name}' already exists. Overwriting.")

        role = Role(
            name=name,
            description=description,
            permissions=set(permissions or []),
            inherited_roles=set(inherited_roles or []),
            created_at=datetime.now().isoformat(),
            created_by=created_by,
        )

        self._roles[name] = role
        self._save()
        console.success(f"Role '{name}' created")
        return role

    @handle_errors()
    def delete_role(self, name: str) -> bool:
        """Delete a role."""
        if name in self.BUILTIN_ROLES:
            console.error(f"Cannot delete built-in role: {name}")
            return False

        if name not in self._roles:
            console.error(f"Role '{name}' not found")
            return False

        # Check if role is in use
        for user in self._users.values():
            if name in user.roles:
                console.error(f"Role '{name}' is in use by user '{user.username}'")
                return False

        del self._roles[name]
        self._save()
        console.success(f"Role '{name}' deleted")
        return True

    @handle_errors()
    def grant_permission(
        self, role_name: str, permission: str, granted_by: str = ""
    ) -> bool:
        """Grant a permission to a role."""
        if role_name not in self._roles:
            console.error(f"Role '{role_name}' not found")
            return False

        self._roles[role_name].permissions.add(permission)

        # Record grant
        grant = PermissionGrant(
            id=f"{role_name}_{permission}_{len(self._grants)}",
            permission=permission,
            role=role_name,
            granted_by=granted_by,
            granted_at=datetime.now().isoformat(),
        )
        self._grants.append(grant)

        self._save()
        console.success(f"Granted '{permission}' to role '{role_name}'")
        return True

    @handle_errors()
    def revoke_permission(self, role_name: str, permission: str) -> bool:
        """Revoke a permission from a role."""
        if role_name not in self._roles:
            console.error(f"Role '{role_name}' not found")
            return False

        if permission in self._roles[role_name].permissions:
            self._roles[role_name].permissions.remove(permission)
            self._save()
            console.success(f"Revoked '{permission}' from role '{role_name}'")
            return True

        console.error(f"Permission '{permission}' not found in role '{role_name}'")
        return False

    @handle_errors()
    def assign_role(self, username: str, role_name: str) -> bool:
        """Assign a role to a user."""
        if role_name not in self._roles:
            console.error(f"Role '{role_name}' not found")
            return False

        if username not in self._users:
            self._users[username] = User(
                username=username,
                created_at=datetime.now().isoformat(),
            )

        self._users[username].roles.add(role_name)
        self._save()
        console.success(f"Assigned role '{role_name}' to user '{username}'")
        return True

    @handle_errors()
    def unassign_role(self, username: str, role_name: str) -> bool:
        """Unassign a role from a user."""
        if username not in self._users:
            console.error(f"User '{username}' not found")
            return False

        if role_name in self._users[username].roles:
            self._users[username].roles.remove(role_name)
            self._save()
            console.success(f"Unassigned role '{role_name}' from user '{username}'")
            return True

        console.error(f"User '{username}' does not have role '{role_name}'")
        return False

    @handle_errors()
    def check_permission(self, username: str, permission: str) -> bool:
        """Check if a user has a permission."""
        if username not in self._users:
            return False

        user = self._users[username]

        # Check all user roles
        for role_name in user.roles:
            if role_name in self._roles:
                role = self._roles[role_name]

                # Check direct permissions
                if permission in role.permissions:
                    return True

                # Check inherited roles
                for inherited_role_name in role.inherited_roles:
                    if inherited_role_name in self._roles:
                        inherited_role = self._roles[inherited_role_name]
                        if permission in inherited_role.permissions:
                            return True

        return False

    @handle_errors()
    def get_user_permissions(self, username: str) -> Set[str]:
        """Get all permissions for a user."""
        if username not in self._users:
            return set()

        user = self._users[username]
        permissions = set()

        for role_name in user.roles:
            if role_name in self._roles:
                role = self._roles[role_name]
                permissions.update(role.permissions)

                # Include inherited roles
                for inherited_role_name in role.inherited_roles:
                    if inherited_role_name in self._roles:
                        permissions.update(self._roles[inherited_role_name].permissions)

        return permissions

    @handle_errors()
    def list_roles(self) -> List[Role]:
        """List all roles."""
        if not self._roles:
            console.info("No roles found")
            return []

        console.rule("Roles")

        rows = []
        for role in sorted(self._roles.values(), key=lambda r: r.name):
            builtin = " (built-in)" if role.name in self.BUILTIN_ROLES else ""
            rows.append(
                [
                    role.name + builtin,
                    role.description or "-",
                    str(len(role.permissions)),
                    str(len(role.inherited_roles)),
                ]
            )

        console.table("Roles", ["Name", "Description", "Permissions", "Inherits"], rows)

        return list(self._roles.values())

    @handle_errors()
    def list_users(self) -> List[User]:
        """List all users."""
        if not self._users:
            console.info("No users found")
            return []

        console.rule("Users")

        rows = []
        for user in sorted(self._users.values(), key=lambda u: u.username):
            status = "active" if user.active else "inactive"
            rows.append(
                [
                    user.username,
                    ", ".join(sorted(user.roles)) or "-",
                    status,
                    user.last_login or "Never",
                ]
            )

        console.table("Users", ["Username", "Roles", "Status", "Last Login"], rows)

        return list(self._users.values())

    @handle_errors()
    def clone_role(
        self, source_name: str, new_name: str, description: str = ""
    ) -> Optional[Role]:
        """Clone a role."""
        if source_name not in self._roles:
            console.error(f"Source role '{source_name}' not found")
            return None

        source = self._roles[source_name]

        return self.create_role(
            name=new_name,
            description=description or f"Clone of {source_name}",
            permissions=list(source.permissions),
            inherited_roles=list(source.inherited_roles),
            created_by="clone",
        )

    @handle_errors()
    def export_role(self, role_name: str, file_path: str) -> bool:
        """Export a role to file."""
        if role_name not in self._roles:
            console.error(f"Role '{role_name}' not found")
            return False

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(asdict(self._roles[role_name]), f, indent=2)
            console.success(f"Role '{role_name}' exported to {file_path}")
            return True
        except Exception as e:
            console.error(f"Failed to export role: {e}")
            return False

    @handle_errors()
    def import_role(self, file_path: str) -> Optional[Role]:
        """Import a role from file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return self.create_role(
                name=data["name"],
                description=data.get("description", ""),
                permissions=data.get("permissions", []),
                inherited_roles=data.get("inherited_roles", []),
                created_by="import",
            )
        except FileNotFoundError:
            console.error(f"File not found: {file_path}")
            return None
        except Exception as e:
            console.error(f"Failed to import role: {e}")
            return None


# Global RBAC manager instance
rbac = RBACManager()
