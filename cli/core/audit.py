"""
Audit Logging System for B.DEV CLI.

Provides comprehensive audit logging for security, compliance,
and operational monitoring.
"""

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

from cli.utils.ui import console
from cli.utils.errors import handle_errors


class AuditEventType(Enum):
    """Types of audit events."""

    COMMAND = "command"
    PLUGIN = "plugin"
    CONFIG = "config"
    SECURITY = "security"
    DEPLOY = "deploy"
    ACCESS = "access"
    SYSTEM = "system"
    ERROR = "error"


class AuditSeverity(Enum):
    """Severity levels for audit events."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event entry."""

    id: str
    timestamp: str
    event_type: AuditEventType
    severity: AuditSeverity
    message: str
    user: str = ""
    source: str = ""
    command: str = ""
    exit_code: int = 0
    duration: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    hash: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = self._generate_id()
        if not self.hash:
            self.hash = self._generate_hash()

    def _generate_id(self) -> str:
        """Generate unique event ID."""
        return hashlib.sha256(
            f"{self.timestamp}{self.event_type}{self.message}".encode()
        ).hexdigest()[:16]

    def _generate_hash(self) -> str:
        """Generate event hash for integrity verification."""
        data = {
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "message": self.message,
            "user": self.user,
            "command": self.command,
            "exit_code": self.exit_code,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


class AuditLogger:
    """Audit logging system with rotation and filtering."""

    AUDIT_DIR = Path.home() / ".bdev" / "audit"
    LOG_FILE = AUDIT_DIR / "audit.log"
    INDEX_FILE = AUDIT_DIR / "index.json"

    def __init__(self) -> None:
        self._events: List[AuditEvent] = []
        self._ensure_audit_dir()
        self._load()

    def _ensure_audit_dir(self) -> None:
        """Create audit directory if it doesn't exist."""
        self.AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    def _load(self) -> None:
        """Load audit events from file."""
        if self.LOG_FILE.exists():
            try:
                with open(self.LOG_FILE, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines:
                        try:
                            data = json.loads(line.strip())
                            event = AuditEvent(
                                id=data.get("id", ""),
                                timestamp=data.get("timestamp", ""),
                                event_type=AuditEventType(
                                    data.get("event_type", "system")
                                ),
                                severity=AuditSeverity(data.get("severity", "info")),
                                message=data.get("message", ""),
                                user=data.get("user", ""),
                                source=data.get("source", ""),
                                command=data.get("command", ""),
                                exit_code=data.get("exit_code", 0),
                                duration=data.get("duration", 0),
                                metadata=data.get("metadata", {}),
                                hash=data.get("hash", ""),
                            )
                            self._events.append(event)
                        except Exception:
                            continue
            except Exception as e:
                console.error(f"Failed to load audit log: {e}")

    def _save_event(self, event: AuditEvent) -> None:
        """Append event to log file."""
        try:
            with open(self.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(event)) + "\n")
        except Exception as e:
            console.error(f"Failed to write audit log: {e}")

    def _save_index(self) -> None:
        """Save audit index."""
        try:
            index_data = {
                "total_events": len(self._events),
                "last_updated": datetime.now().isoformat(),
                "event_types": {
                    et.value: len([e for e in self._events if e.event_type == et])
                    for et in AuditEventType
                },
            }
            with open(self.INDEX_FILE, "w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2)
        except Exception as e:
            console.error(f"Failed to save audit index: {e}")

    @handle_errors()
    def log(
        self,
        event_type: AuditEventType,
        message: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        user: str = "",
        source: str = "",
        command: str = "",
        exit_code: int = 0,
        duration: float = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log an audit event."""
        event = AuditEvent(
            id="",
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            severity=severity,
            message=message,
            user=user,
            source=source,
            command=command,
            exit_code=exit_code,
            duration=duration,
            metadata=metadata or {},
        )

        self._events.append(event)
        self._save_event(event)
        self._save_index()

        return event

    @handle_errors()
    def log_command(
        self,
        command: str,
        exit_code: int,
        duration: float,
        user: str = "",
    ) -> AuditEvent:
        """Log a command execution."""
        severity = AuditSeverity.ERROR if exit_code != 0 else AuditSeverity.INFO
        message = f"Command {'failed' if exit_code != 0 else 'completed'}: {command}"

        return self.log(
            event_type=AuditEventType.COMMAND,
            message=message,
            severity=severity,
            user=user,
            command=command,
            exit_code=exit_code,
            duration=duration,
        )

    @handle_errors()
    def log_plugin(
        self,
        plugin_name: str,
        action: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log a plugin action."""
        severity = AuditSeverity.ERROR if not success else AuditSeverity.INFO
        message = f"Plugin {action}: {plugin_name}"

        return self.log(
            event_type=AuditEventType.PLUGIN,
            message=message,
            severity=severity,
            source=plugin_name,
            metadata=metadata or {},
        )

    @handle_errors()
    def log_security(
        self,
        event: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        user: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log a security event."""
        return self.log(
            event_type=AuditEventType.SECURITY,
            message=event,
            severity=severity,
            user=user,
            metadata=metadata or {},
        )

    @handle_errors()
    def log_config(
        self,
        action: str,
        key: str,
        value: Any,
        user: str = "",
    ) -> AuditEvent:
        """Log a configuration change."""
        return self.log(
            event_type=AuditEventType.CONFIG,
            message=f"Configuration {action}: {key}",
            severity=AuditSeverity.INFO,
            user=user,
            metadata={"key": key, "value": str(value)},
        )

    @handle_errors()
    def get_logs(
        self,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[AuditSeverity] = None,
        user: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        """Get audit logs with filtering."""
        filtered = self._events.copy()

        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]

        if severity:
            filtered = [e for e in filtered if e.severity == severity]

        if user:
            filtered = [e for e in filtered if e.user == user]

        return filtered[offset : offset + limit]

    @handle_errors()
    def search(self, query: str, limit: int = 100) -> List[AuditEvent]:
        """Search audit logs."""
        query_lower = query.lower()
        return [
            event
            for event in self._events
            if query_lower in event.message.lower()
            or query_lower in event.command.lower()
            or query_lower in event.source.lower()
        ][:limit]

    @handle_errors()
    def export(self, file_path: str, format: str = "json") -> bool:
        """Export audit logs."""
        try:
            if format == "json":
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump([asdict(event) for event in self._events], f, indent=2)
            elif format == "jsonl":
                with open(file_path, "w", encoding="utf-8") as f:
                    for event in self._events:
                        f.write(json.dumps(asdict(event)) + "\n")
            elif format == "csv":
                import csv

                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        [
                            "id",
                            "timestamp",
                            "event_type",
                            "severity",
                            "message",
                            "user",
                            "source",
                            "command",
                            "exit_code",
                            "duration",
                        ]
                    )
                    for event in self._events:
                        writer.writerow(
                            [
                                event.id,
                                event.timestamp,
                                event.event_type.value,
                                event.severity.value,
                                event.message,
                                event.user,
                                event.source,
                                event.command,
                                event.exit_code,
                                event.duration,
                            ]
                        )
            else:
                console.error(f"Unsupported format: {format}")
                return False

            console.success(f"Exported {len(self._events)} audit events to {file_path}")
            return True

        except Exception as e:
            console.error(f"Failed to export audit logs: {e}")
            return False

    @handle_errors()
    def clear(self, before_date: Optional[str] = None) -> int:
        """Clear audit logs (optionally before a specific date)."""
        if before_date:
            try:
                cutoff = datetime.fromisoformat(before_date)
                old_count = len(self._events)
                self._events = [
                    e
                    for e in self._events
                    if datetime.fromisoformat(e.timestamp) >= cutoff
                ]
                cleared = old_count - len(self._events)
            except ValueError:
                console.error(f"Invalid date format: {before_date}")
                return 0
        else:
            cleared = len(self._events)
            self._events.clear()

        self._save_index()
        console.success(f"Cleared {cleared} audit events")
        return cleared

    @handle_errors()
    def verify_integrity(self) -> Dict[str, Any]:
        """Verify integrity of audit logs."""
        issues = []

        for i, event in enumerate(self._events):
            # Recalculate hash
            data = {
                "timestamp": event.timestamp,
                "event_type": event.event_type.value,
                "message": event.message,
                "user": event.user,
                "command": event.command,
                "exit_code": event.exit_code,
            }
            expected_hash = hashlib.sha256(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest()

            if event.hash != expected_hash:
                issues.append(
                    {
                        "index": i,
                        "event_id": event.id,
                        "issue": "hash_mismatch",
                        "expected": expected_hash,
                        "actual": event.hash,
                    }
                )

        return {
            "total_events": len(self._events),
            "verified": len(self._events) - len(issues),
            "issues": issues,
            "integrity_ok": len(issues) == 0,
        }

    @handle_errors()
    def stats(self) -> Dict[str, Any]:
        """Get audit log statistics."""
        if not self._events:
            return {"total": 0, "by_type": {}, "by_severity": {}}

        by_type = {
            et.value: len([e for e in self._events if e.event_type == et])
            for et in AuditEventType
        }

        by_severity = {
            s.value: len([e for e in self._events if e.severity == s])
            for s in AuditSeverity
        }

        # Calculate time range
        timestamps = [datetime.fromisoformat(e.timestamp) for e in self._events]
        time_range = {
            "first": min(timestamps).isoformat(),
            "last": max(timestamps).isoformat(),
            "span_days": (max(timestamps) - min(timestamps)).days,
        }

        # User activity
        users = {}
        for event in self._events:
            if event.user:
                users[event.user] = users.get(event.user, 0) + 1

        return {
            "total": len(self._events),
            "by_type": by_type,
            "by_severity": by_severity,
            "time_range": time_range,
            "top_users": sorted(users.items(), key=lambda x: x[1], reverse=True)[:10],
        }


# Global audit logger instance
audit = AuditLogger()
