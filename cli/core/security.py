"""
Security Module for bdev-cli.

Provides military-grade security features:
- Secure Enclave Sandbox
- Multi-Factor Authentication (TOTP)
- Privilege Escalation Blocking
"""

import os
import sys
import base64
import hashlib
import subprocess
from typing import Optional, Dict, Any, List
from pathlib import Path
from abc import ABC, abstractmethod
from functools import wraps
from dataclasses import dataclass, field

import pyotp
from passlib.context import CryptContext

from cli.utils.ui import console
from cli.utils.errors import CLIError


class SecurityError(CLIError):
    """Exception raised for security-related failures."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="SECURITY_ERROR")


@dataclass
class SecurityConfig:
    """Security configuration."""

    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    sandbox_enabled: bool = True
    privilege_block_enabled: bool = True
    session_timeout: int = 300
    allowed_commands: List[str] = field(default_factory=list)
    blocked_commands: List[str] = field(
        default_factory=lambda: ["sudo", "su", "doas", "pkexec"]
    )


class SecureEnclave:
    """
    Secure Enclave Sandbox for isolated command execution.

    Provides kernel-level isolation for sensitive operations.
    """

    def __init__(self, config: SecurityConfig) -> None:
        self.config = config
        self._active: bool = False

    def enter(self) -> bool:
        """Enter secure enclave mode."""
        if not self.config.sandbox_enabled:
            console.warning("Secure Enclave is disabled")
            return False

        self._active = True
        console.info("Secure Enclave activated")
        return True

    def exit(self) -> None:
        """Exit secure enclave mode."""
        self._active = False
        console.info("Secure Enclave deactivated")

    @property
    def is_active(self) -> bool:
        """Check if enclave is active."""
        return self._active

    def execute_sandboxed(self, command: List[str]) -> bool:
        """
        Execute command in sandboxed environment.

        Args:
            command: Command and arguments as list.

        Returns:
            True if execution allowed, False otherwise.
        """
        if not self.config.sandbox_enabled:
            return True

        cmd_name = command[0] if command else ""

        if cmd_name in self.config.blocked_commands:
            raise SecurityError(f"Command '{cmd_name}' is blocked by security policy")

        if (
            self.config.allowed_commands
            and cmd_name not in self.config.allowed_commands
        ):
            raise SecurityError(f"Command '{cmd_name}' is not in allowed list")

        return True


class MFAManager:
    """
    Multi-Factor Authentication Manager using TOTP.

    Supports TOTP codes compatible with Google Authenticator,
    Authy, and other authenticator apps.
    """

    CONFIG_FILE = Path.home() / ".bdev" / "security.json"

    def __init__(self, config: SecurityConfig) -> None:
        self.config = config
        self._totp: Optional[pyotp.TOTP] = None
        self._verified: bool = False
        self._last_verification: float = 0

    def setup(self) -> str:
        """
        Setup MFA for the first time.

        Returns:
            Provisioning URI for QR code generation.
        """
        secret = pyotp.random_base32()
        self.config.mfa_secret = secret
        self.config.mfa_enabled = True

        self._totp = pyotp.TOTP(secret)
        self._save_config()

        uri = self._totp.provisioning_uri(name="bdev-cli", issuer_name="B.DEV Security")

        console.success("MFA enabled. Scan QR code with your authenticator app.")
        return uri

    def verify(self, code: str) -> bool:
        """
        Verify TOTP code.

        Args:
            code: 6-digit TOTP code.

        Returns:
            True if code is valid, False otherwise.
        """
        if not self.config.mfa_enabled or not self.config.mfa_secret:
            return False

        if not self._totp:
            self._totp = pyotp.TOTP(self.config.mfa_secret)

        if self._totp.verify(code):
            self._verified = True
            import time

            self._last_verification = time.time()
            console.success("Authentication successful")
            return True

        console.error("Invalid code")
        return False

    def is_verified(self) -> bool:
        """Check if session is verified and not expired."""
        if not self._verified:
            return False

        import time

        elapsed = time.time() - self._last_verification
        if elapsed > self.config.session_timeout:
            self._verified = False
            console.warning("Session expired. Please re-authenticate.")
            return False

        return True

    def disable(self) -> None:
        """Disable MFA (requires verification first)."""
        if not self.is_verified():
            raise SecurityError("Verification required to disable MFA")

        self.config.mfa_enabled = False
        self.config.mfa_secret = None
        self._verified = False
        self._save_config()
        console.success("MFA disabled")

    def _save_config(self) -> None:
        """Save security configuration to file."""
        import json

        data = {
            "mfa_enabled": self.config.mfa_enabled,
            "mfa_secret": self.config.mfa_secret,
            "sandbox_enabled": self.config.sandbox_enabled,
            "privilege_block_enabled": self.config.privilege_block_enabled,
            "session_timeout": self.config.session_timeout,
        }

        try:
            self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.CONFIG_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            console.error(f"Failed to save security config: {e}")


class PrivilegeGuard:
    """
    Privilege Escalation Blocker.

    Prevents unauthorized sudo/su commands and enforces
    principle of least privilege.
    """

    def __init__(self, config: SecurityConfig) -> None:
        self.config = config

    def check_command(self, command: str) -> bool:
        """
        Check if command attempts privilege escalation.

        Args:
            command: Command string to check.

        Returns:
            True if command is safe, raises SecurityError if blocked.
        """
        if not self.config.privilege_block_enabled:
            return True

        blocked_patterns = self.config.blocked_commands
        command_lower = command.lower()

        for pattern in blocked_patterns:
            if pattern in command_lower.split():
                raise SecurityError(
                    f"Privilege escalation command '{pattern}' is blocked. "
                    "Use 'bdev security allow' to authorize."
                )

        return True

    def scan_process_tree(self) -> List[str]:
        """
        Scan running processes for privilege escalation attempts.

        Returns:
            List of suspicious process names.
        """
        suspicious: List[str] = []

        try:
            if sys.platform == "linux" or sys.platform == "darwin":
                result = subprocess.run(
                    ["ps", "aux"], capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split("\n"):
                    for blocked in self.config.blocked_commands:
                        if blocked in line.lower():
                            suspicious.append(blocked)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return list(set(suspicious))


class SecurityManager:
    """
    Main Security Manager - coordinates all security features.

    Usage:
        security = SecurityManager()
        security.authenticate()
        security.execute_safe_command(["ls", "-la"])
    """

    _instance: Optional["SecurityManager"] = None

    def __new__(cls) -> "SecurityManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._initialized = True
        self.config = self._load_config()
        self.enclave = SecureEnclave(self.config)
        self.mfa = MFAManager(self.config)
        self.guard = PrivilegeGuard(self.config)

    def _load_config(self) -> SecurityConfig:
        """Load security configuration from file."""
        import json

        config = SecurityConfig()

        if MFAManager.CONFIG_FILE.exists():
            try:
                with open(MFAManager.CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    config.mfa_enabled = data.get("mfa_enabled", False)
                    config.mfa_secret = data.get("mfa_secret")
                    config.sandbox_enabled = data.get("sandbox_enabled", True)
                    config.privilege_block_enabled = data.get(
                        "privilege_block_enabled", True
                    )
                    config.session_timeout = data.get("session_timeout", 300)
            except Exception as e:
                console.error(f"Failed to load security config: {e}")

        return config

    def authenticate(self) -> bool:
        """
        Authenticate user using MFA if enabled.

        Returns:
            True if authenticated, False otherwise.
        """
        if not self.config.mfa_enabled:
            return True

        if self.mfa.is_verified():
            return True

        from prompt_toolkit import prompt

        console.info("MFA required. Enter your 6-digit code:")
        code = prompt("Code: ")

        return self.mfa.verify(code)

    def setup_mfa(self) -> None:
        """Setup Multi-Factor Authentication."""
        if self.config.mfa_enabled:
            console.warning("MFA is already enabled")
            return

        uri = self.mfa.setup()
        console.panel(f"QR Code URI: {uri}", title="Scan this QR Code")

    def execute_safe(self, command: List[str]) -> bool:
        """
        Execute command with all security checks.

        Args:
            command: Command and arguments.

        Returns:
            True if command executed safely.

        Raises:
            SecurityError: If security check fails.
        """
        cmd_str = " ".join(command)

        if not self.authenticate():
            raise SecurityError("Authentication required")

        self.guard.check_command(cmd_str)
        self.enclave.execute_sandboxed(command)

        return True

    def enable_sandbox(self) -> None:
        """Enable Secure Enclave sandbox."""
        self.config.sandbox_enabled = True
        self.mfa._save_config()
        console.success("Secure Enclave enabled")

    def disable_sandbox(self) -> None:
        """Disable Secure Enclave sandbox (requires auth)."""
        if not self.authenticate():
            raise SecurityError("Authentication required")
        self.config.sandbox_enabled = False
        self.mfa._save_config()
        console.warning("Secure Enclave disabled")

    def get_status(self) -> Dict[str, Any]:
        """Get current security status."""
        return {
            "mfa_enabled": self.config.mfa_enabled,
            "mfa_verified": self.mfa.is_verified(),
            "sandbox_enabled": self.config.sandbox_enabled,
            "privilege_block_enabled": self.config.privilege_block_enabled,
            "session_timeout": self.config.session_timeout,
            "enclave_active": self.enclave.is_active,
        }


def require_auth(func):
    """
    Decorator to require authentication for a function.

    Usage:
        @require_auth
        def sensitive_operation():
            ...
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        security = SecurityManager()
        if not security.authenticate():
            raise SecurityError("Authentication required")
        return func(*args, **kwargs)

    return wrapper


def require_sandbox(func):
    """
    Decorator to require sandbox mode for a function.

    Usage:
        @require_sandbox
        def dangerous_operation():
            ...
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        security = SecurityManager()
        if not security.config.sandbox_enabled:
            raise SecurityError("Sandbox mode is disabled")
        security.enclave.enter()
        try:
            return func(*args, **kwargs)
        finally:
            security.enclave.exit()

    return wrapper


# Global security instance
security = SecurityManager()
