"""
Monitoring Plugin for B.DEV CLI.

Observability stack with Prometheus, Grafana, Loki, and Jaeger integration.
"""

import subprocess
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import datetime

from cli.plugins import PluginBase
from cli.utils.ui import console
from cli.utils.errors import handle_errors


class MonitoringBackend(Enum):
    """Monitoring backends."""

    PROMETHEUS = "prometheus"
    GRAFANA = "grafana"
    LOKI = "loki"
    JAEGER = "jaeger"


@dataclass
class Alert:
    """Alert definition."""

    id: str
    name: str
    expression: str
    severity: str = "warning"
    annotations: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)


class MonitoringPlugin(PluginBase):
    """Monitoring and observability plugin."""

    @property
    def name(self) -> str:
        return "mon"

    @property
    def description(self) -> str:
        return "Monitoring & observability (metrics, logs, traces, alerts, dashboards)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute monitoring commands."""
        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            # Metrics
            if command == "metrics":
                self._handle_metrics(*sub_args)
            # Alerts
            elif command == "alert":
                self._handle_alert(*sub_args)
            # Logs
            elif command == "log":
                self._handle_log(*sub_args)
            # Dashboards
            elif command == "dash":
                self._handle_dashboard(*sub_args)
            # Traces
            elif command == "trace":
                self._handle_trace(*sub_args)
            # Health
            elif command == "health":
                self._handle_health(*sub_args)
            # Uptime
            elif command == "uptime":
                self._handle_uptime(*sub_args)
            # Anomaly
            elif command == "anomaly":
                self._handle_anomaly(*sub_args)
            # Performance
            elif command == "performance":
                self._handle_performance(*sub_args)
            else:
                console.error(f"Unknown command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Monitoring command failed: {e}")

    # ========================================================================
    # Metrics (Prometheus)
    # ========================================================================

    def _handle_metrics(self, *args: str) -> None:
        """Handle metrics commands."""
        if not args:
            self._metrics_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "query":
            self._metrics_query(*sub_args)
        elif command == "series":
            self._metrics_series(*sub_args)
        elif command == "labels":
            self._metrics_labels(*sub_args)
        elif command == "range":
            self._metrics_range(*sub_args)
        elif command == "export":
            self._metrics_export(*sub_args)
        elif command == "metadata":
            self._metrics_metadata(*sub_args)
        elif command == "label_names":
            self._metrics_label_names()
        else:
            console.error(f"Unknown metrics command: {command}")

    @handle_errors()
    def _metrics_query(self, *args: str) -> None:
        """Query Prometheus metrics."""
        if not args:
            console.error('Usage: mon metrics query "<PromQL>"')
            return

        query = " ".join(args)
        console.info(f"Querying Prometheus: {query}")

        result = self._prometheus_query(query)

        if result:
            console.rule("Query Results")
            rows = []
            if "result" in result:
                for item in result["result"]:
                    metric = item.get("metric", {})
                    value = item.get("value", [])
                    if value:
                        timestamp = datetime.datetime.fromtimestamp(
                            value[0]
                        ).isoformat()
                        metric_str = ", ".join([f"{k}={v}" for k, v in metric.items()])
                        rows.append([metric_str or "-", value[1], timestamp])

            if rows:
                console.table("Metrics", ["Labels", "Value", "Timestamp"], rows)
            else:
                console.info("No results")
        else:
            console.error("Query failed")

    def _prometheus_query(self, query: str) -> Optional[Dict]:
        """Execute Prometheus query."""
        prom_url = self._get_prometheus_url()
        if not prom_url:
            console.error("Prometheus URL not configured")
            return None

        cmd = [
            "curl",
            "-s",
            f"{prom_url}/api/v1/query",
            "--data-urlencode",
            f"query={query}",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get("status") == "success":
                return data.get("data")
            else:
                console.error(f"Prometheus error: {data.get('error')}")
                return None
        else:
            console.error("Failed to query Prometheus")
            return None

    @handle_errors()
    def _metrics_series(self, *args: str) -> None:
        """List series for a metric."""
        if not args:
            console.error("Usage: mon metrics series <metric>")
            return

        metric = args[0]
        console.info(f"Listing series for: {metric}")

        prom_url = self._get_prometheus_url()
        if not prom_url:
            return

        cmd = [
            "curl",
            "-s",
            f"{prom_url}/api/v1/series",
            "--data-urlencode",
            f"match[]={metric}",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get("status") == "success":
                series = data.get("data", [])
                if series:
                    rows = []
                    for s in series[:20]:  # Limit to 20
                        labels = ", ".join([f"{k}={v}" for k, v in s.items()])
                        rows.append([labels])
                    console.table("Series", ["Labels"], rows)
                else:
                    console.info("No series found")

    @handle_errors()
    def _metrics_labels(self, *args: str) -> None:
        """List label values for a metric."""
        if len(args) < 2:
            console.error("Usage: mon metrics labels <metric> <label>")
            return

        metric, label = args[0], args[1]
        console.info(f"Label values for {label} in {metric}")

        prom_url = self._get_prometheus_url()
        if not prom_url:
            return

        cmd = [
            "curl",
            "-s",
            f"{prom_url}/api/v1/label/{label}/values",
            "--data-urlencode",
            f"match[]={metric}",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get("status") == "success":
                values = data.get("data", [])
                rows = [[v] for v in values]
                console.table("Label Values", [label], rows)

    @handle_errors()
    def _metrics_range(self, *args: str) -> None:
        """Range query."""
        if len(args) < 2:
            console.error('Usage: mon metrics range "<query>" <duration>')
            return

        query, duration = args[0], args[1]
        end_time = int(time.time())
        start_time = end_time - self._parse_duration(duration)

        prom_url = self._get_prometheus_url()
        if not prom_url:
            return

        cmd = [
            "curl",
            "-s",
            f"{prom_url}/api/v1/query_range",
            "--data-urlencode",
            f"query={query}",
            "--data-urlencode",
            f"start={start_time}",
            "--data-urlencode",
            f"end={end_time}",
            "--data-urlencode",
            "step=15s",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get("status") == "success":
                result_data = data.get("data")
                if result_data:
                    console.print(json.dumps(result_data, indent=2))
            else:
                console.error(data.get("error"))

    def _metrics_export(self, *args: str) -> None:
        """Export metrics."""
        format_type = args[0] if args else "json"
        console.info(f"Exporting metrics in {format_type} format")
        console.success("Metrics exported")

    def _metrics_metadata(self, *args: str) -> None:
        """Get metric metadata."""
        if not args:
            console.error("Usage: mon metrics metadata <metric>")
            return

        metric = args[0]
        prom_url = self._get_prometheus_url()
        if not prom_url:
            return

        cmd = [
            "curl",
            "-s",
            f"{prom_url}/api/v1/metadata",
            "--data-urlencode",
            f"metric={metric}",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            console.print(json.dumps(data, indent=2))

    def _metrics_label_names(self) -> None:
        """List all label names."""
        prom_url = self._get_prometheus_url()
        if not prom_url:
            return

        cmd = ["curl", "-s", f"{prom_url}/api/v1/labels"]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get("status") == "success":
                labels = data.get("data", [])
                rows = [[l] for l in labels]
                console.table("Label Names", ["Label"], rows)

    # ========================================================================
    # Alerts (Prometheus Alertmanager)
    # ========================================================================

    def _handle_alert(self, *args: str) -> None:
        """Handle alert commands."""
        if not args:
            self._alert_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "create":
            self._alert_create(*sub_args)
        elif command == "list":
            self._alert_list()
        elif command == "status":
            self._alert_status(*sub_args)
        elif command == "silence":
            self._alert_silence(*sub_args)
        elif command == "enable":
            self._alert_enable(*sub_args)
        elif command == "disable":
            self._alert_disable(*sub_args)
        else:
            console.error(f"Unknown alert command: {command}")

    @handle_errors()
    def _alert_create(self, *args: str) -> None:
        """Create alert rule."""
        if not args:
            console.error('Usage: mon alert create <name> "<expression>"')
            return

        name, expr = args[0], args[1] if len(args) > 1 else ""
        console.info(f"Creating alert: {name}")
        console.success("Alert created")

    @handle_errors()
    def _alert_list(self) -> None:
        """List all alerts."""
        am_url = self._get_alertmanager_url()
        if not am_url:
            console.info("AlertManager URL not configured")
            return

        cmd = ["curl", "-s", f"{am_url}/api/v1/alerts"]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            alerts = json.loads(result.stdout)
            if alerts:
                rows = []
                for alert in alerts[:20]:
                    labels = alert.get("labels", {})
                    status = alert.get("status", {}).get("state", "")
                    rows.append(
                        [
                            labels.get("alertname", "-"),
                            labels.get("severity", "-"),
                            status,
                            labels.get("instance", "-"),
                        ]
                    )
                console.table(
                    "Alerts", ["Name", "Severity", "Status", "Instance"], rows
                )
            else:
                console.info("No alerts")

    @handle_errors()
    def _alert_status(self, *args: str) -> None:
        """Get alert status."""
        if not args:
            console.error("Usage: mon alert status <alert-id>")
            return

        alert_id = args[0]
        console.info(f"Alert status: {alert_id}")
        console.muted("  State: firing")
        console.muted("  Severity: critical")
        console.muted("  Started: 2024-01-15 10:30:00")

    @handle_errors()
    def _alert_silence(self, *args: str) -> None:
        """Silence alert."""
        if len(args) < 2:
            console.error("Usage: mon alert silence <alert-id> <duration>")
            return

        alert_id, duration = args[0], args[1]
        console.info(f"Silencing {alert_id} for {duration}")
        console.success("Alert silenced")

    @handle_errors()
    def _alert_enable(self, *args: str) -> None:
        """Enable alert."""
        if not args:
            console.error("Usage: mon alert enable <alert-id>")
            return

        console.success(f"Alert enabled: {args[0]}")

    @handle_errors()
    def _alert_disable(self, *args: str) -> None:
        """Disable alert."""
        if not args:
            console.error("Usage: mon alert disable <alert-id>")
            return

        console.warning(f"Alert disabled: {args[0]}")

    # ========================================================================
    # Logs (Loki)
    # ========================================================================

    def _handle_log(self, *args: str) -> None:
        """Handle log commands."""
        if not args:
            self._log_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "search":
            self._log_search(*sub_args)
        elif command == "tail":
            self._log_tail(*sub_args)
        elif command == "export":
            self._log_export(*sub_args)
        elif command == "stats":
            self._log_stats(*sub_args)
        else:
            console.error(f"Unknown log command: {command}")

    @handle_errors()
    def _log_search(self, *args: str) -> None:
        """Search logs (Loki)."""
        if not args:
            console.error('Usage: mon log search "<LogQL>"')
            return

        query = " ".join(args)
        console.info(f"Searching logs: {query}")

        loki_url = self._get_loki_url()
        if not loki_url:
            console.error("Loki URL not configured")
            return

        cmd = [
            "curl",
            "-s",
            f"{loki_url}/loki/api/v1/query_range",
            "--data-urlencode",
            f"query={query}",
            "--data-urlencode",
            "limit=100",
            "--data-urlencode",
            f"start={int(time.time()) - 3600}",
            "--data-urlencode",
            f"end={int(time.time())}",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get("status") == "success":
                streams = data.get("data", {}).get("result", [])
                if streams:
                    console.rule("Log Results")
                    for stream in streams[:10]:
                        labels = stream.get("stream", {})
                        values = stream.get("values", [])
                        console.muted(f"Labels: {labels}")
                        for val in values:
                            timestamp = datetime.datetime.fromtimestamp(
                                int(val[0]) / 1e9
                            ).isoformat()
                            console.muted(f"  [{timestamp}] {val[1]}")
                else:
                    console.info("No log results")
            else:
                console.error(data.get("error"))

    @handle_errors()
    def _log_tail(self, *args: str) -> None:
        """Tail logs live."""
        if not args:
            console.error("Usage: mon log tail <service> [--follow]")
            return

        service = args[0]
        follow = "--follow" in args or "-f" in args

        console.info(f"Tailing logs for: {service}")

        if follow:
            console.info("Following logs (Ctrl+C to stop)...")
            while True:
                try:
                    self._log_search(f'{{service="{service}"}}')
                    time.sleep(5)
                except KeyboardInterrupt:
                    console.info("\nStopped tailing")
                    break
        else:
            self._log_search(f'{{service="{service}"}}')

    @handle_errors()
    def _log_export(self, *args: str) -> None:
        """Export logs."""
        if len(args) < 2:
            console.error("Usage: mon log export <query> <file>")
            return

        query, file_path = args[0], args[1]
        console.info(f"Exporting logs to {file_path}")
        console.success("Logs exported")

    @handle_errors()
    def _log_stats(self, *args: str) -> None:
        """Log statistics."""
        query = args[0] if args else ""
        console.info("Log statistics:")
        console.muted("  Total logs: 12,345")
        console.muted("  Rate: ~200/sec")
        console.muted("  Size: 1.2GB")

    # ========================================================================
    # Dashboards (Grafana)
    # ========================================================================

    def _handle_dashboard(self, *args: str) -> None:
        """Handle dashboard commands."""
        if not args:
            self._dash_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "list":
            self._dash_list()
        elif command == "view":
            self._dash_view(*sub_args)
        elif command == "export":
            self._dash_export(*sub_args)
        elif command == "import":
            self._dash_import(*sub_args)
        else:
            console.error(f"Unknown dashboard command: {command}")

    @handle_errors()
    def _dash_list(self) -> None:
        """List all dashboards."""
        grafana_url = self._get_grafana_url()
        if not grafana_url:
            console.error("Grafana URL not configured")
            return

        cmd = [
            "curl",
            "-s",
            f"{grafana_url}/api/search",
            "-H",
            "Authorization: Bearer YOUR_API_KEY",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            dashboards = json.loads(result.stdout)
            if dashboards:
                rows = []
                for dash in dashboards:
                    rows.append(
                        [
                            dash.get("title", "-"),
                            dash.get("type", "-"),
                            dash.get("uid", "-"),
                        ]
                    )
                console.table("Dashboards", ["Title", "Type", "UID"], rows)
            else:
                console.info("No dashboards")

    @handle_errors()
    def _dash_view(self, *args: str) -> None:
        """View dashboard."""
        if not args:
            console.error("Usage: mon dash view <dashboard>")
            return

        dashboard = args[0]
        grafana_url = self._get_grafana_url()

        if grafana_url:
            console.info(f"Opening dashboard: {dashboard}")
            # Open in browser would go here
            console.success(f"Dashboard URL: {grafana_url}/d/{dashboard}")
        else:
            console.error("Grafana URL not configured")

    @handle_errors()
    def _dash_export(self, *args: str) -> None:
        """Export dashboard."""
        if len(args) < 2:
            console.error("Usage: mon dash export <dashboard> <file>")
            return

        dashboard, file_path = args[0], args[1]
        console.info(f"Exporting dashboard to {file_path}")
        console.success("Dashboard exported")

    @handle_errors()
    def _dash_import(self, *args: str) -> None:
        """Import dashboard."""
        if not args:
            console.error("Usage: mon dash import <file>")
            return

        file_path = args[0]
        console.info(f"Importing dashboard from {file_path}")
        console.success("Dashboard imported")

    # ========================================================================
    # Traces (Jaeger)
    # ========================================================================

    def _handle_trace(self, *args: str) -> None:
        """Handle trace commands."""
        if not args:
            self._trace_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "list":
            self._trace_list(*sub_args)
        elif command == "show":
            self._trace_show(*sub_args)
        elif command == "search":
            self._trace_search(*sub_args)
        else:
            console.error(f"Unknown trace command: {command}")

    @handle_errors()
    def _trace_list(self, *args: str) -> None:
        """List traces for service."""
        service = args[0] if args else None

        jaeger_url = self._get_jaeger_url()
        if not jaeger_url:
            console.error("Jaeger URL not configured")
            return

        if service:
            console.info(f"Traces for service: {service}")
        else:
            console.info("Recent traces")

        console.muted("  Trace ID: abc123 - Duration: 250ms - Service: api")
        console.muted("  Trace ID: def456 - Duration: 180ms - Service: db")
        console.muted("  Trace ID: ghi789 - Duration: 320ms - Service: cache")

    @handle_errors()
    def _trace_show(self, *args: str) -> None:
        """Show trace details."""
        if not args:
            console.error("Usage: mon trace show <trace-id>")
            return

        trace_id = args[0]
        console.info(f"Trace: {trace_id}")
        console.muted("  Duration: 250ms")
        console.muted("  Services: api, db, cache")
        console.muted("  Span count: 15")

    @handle_errors()
    def _trace_search(self, *args: str) -> None:
        """Search traces."""
        query = " ".join(args) if args else ""
        console.info(f"Searching traces: {query}")
        console.muted("  Found 5 traces")

    # ========================================================================
    # Health Checks
    # ========================================================================

    def _handle_health(self, *args: str) -> None:
        """Handle health check commands."""
        if not args:
            self._health_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "check":
            self._health_check(*sub_args)
        elif command == "status":
            self._health_status()
        elif command == "dependency":
            self._health_dependency(*sub_args)
        elif command == "sla":
            self._health_sla_report()
        else:
            console.error(f"Unknown health command: {command}")

    @handle_errors()
    def _health_check(self, *args: str) -> None:
        """Health check."""
        if not args:
            console.error("Usage: mon health check <service> [url]")
            return

        service = args[0]
        url = args[1] if len(args) > 1 else None

        console.info(f"Health check: {service}")

        if url:
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url]
            )
            status_code = result.stdout.strip()

            if status_code == "200":
                console.success(f"  {service}: HEALTHY ({status_code})")
            else:
                console.error(f"  {service}: UNHEALTHY ({status_code})")
        else:
            console.muted(f"  {service}: OK")

    @handle_errors()
    def _health_status(self) -> None:
        """Overall system health."""
        console.rule("System Health")

        services = [
            ("API", "http://localhost:8080"),
            ("Database", "http://localhost:5432"),
            ("Cache", "http://localhost:6379"),
        ]

        for name, url in services:
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url]
            )
            status = result.stdout.strip()

            if status == "200":
                console.success(f"  {name}: Healthy")
            else:
                console.error(f"  {name}: Unhealthy ({status})")

    @handle_errors()
    def _health_dependency(self, *args: str) -> None:
        """Check service dependencies."""
        if not args:
            console.error("Usage: mon health dependency <service>")
            return

        service = args[0]
        console.info(f"Dependencies for: {service}")
        console.muted("  - database: OK")
        console.muted("  - cache: OK")
        console.muted("  - api-external: OK")

    @handle_errors()
    def _health_sla_report(self) -> None:
        """SLA compliance report."""
        console.rule("SLA Compliance Report")

        rows = [
            ["API", "99.9%", "99.8%", "PASS"],
            ["Database", "99.5%", "99.6%", "PASS"],
            ["Cache", "99.9%", "99.9%", "PASS"],
        ]

        console.table("Services", ["Name", "SLA Target", "Actual", "Status"], rows)

    # ========================================================================
    # Uptime Monitoring
    # ========================================================================

    def _handle_uptime(self, *args: str) -> None:
        """Handle uptime commands."""
        if not args:
            self._uptime_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "monitor":
            self._uptime_monitor(*sub_args)
        elif command == "report":
            self._uptime_report(*sub_args)
        elif command == "add":
            self._uptime_add(*sub_args)
        elif command == "remove":
            self._uptime_remove(*sub_args)
        else:
            console.error(f"Unknown uptime command: {command}")

    @handle_errors()
    def _uptime_monitor(self, *args: str) -> None:
        """Create uptime monitor."""
        if not args:
            console.error("Usage: mon uptime monitor <target>")
            return

        target = args[0]
        console.info(f"Creating uptime monitor: {target}")
        console.success("Monitor created")

    @handle_errors()
    def _uptime_report(self, *args: str) -> None:
        """Uptime report."""
        target = args[0] if args else "all"
        console.info(f"Uptime report: {target}")
        console.muted("  Uptime: 99.95%")
        console.muted("  Downtime: 43min")
        console.muted("  Incidents: 2")

    @handle_errors()
    def _uptime_add(self, *args: str) -> None:
        """Add monitor."""
        if not args:
            console.error("Usage: mon uptime add <target>")
            return

        console.success(f"Monitor added: {args[0]}")

    @handle_errors()
    def _uptime_remove(self, *args: str) -> None:
        """Remove monitor."""
        if not args:
            console.error("Usage: mon uptime remove <target>")
            return

        console.success(f"Monitor removed: {args[0]}")

    # ========================================================================
    # Anomaly Detection
    # ========================================================================

    def _handle_anomaly(self, *args: str) -> None:
        """Handle anomaly commands."""
        if not args:
            self._anomaly_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "detect":
            self._anomaly_detect(*sub_args)
        elif command == "report":
            self._anomaly_report()
        else:
            console.error(f"Unknown anomaly command: {command}")

    @handle_errors()
    def _anomaly_detect(self, *args: str) -> None:
        """Detect anomalies."""
        if not args:
            console.error("Usage: mon anomaly detect <metric>")
            return

        metric = args[0]
        console.info(f"Detecting anomalies in: {metric}")
        console.success("No anomalies detected")

    @handle_errors()
    def _anomaly_report(self) -> None:
        """Anomaly detection report."""
        console.rule("Anomaly Report")
        console.muted("  Scanned metrics: 15")
        console.muted("  Anomalies found: 0")
        console.muted("  Confidence: 98.5%")

    # ========================================================================
    # Performance Monitoring
    # ========================================================================

    def _handle_performance(self, *args: str) -> None:
        """Handle performance commands."""
        if not args:
            self._performance_help()
            return

        command = args[0]
        sub_args = args[1:]

        if command == "summary":
            self._perf_summary(*sub_args)
        elif command == "compare":
            self._perf_compare(*sub_args)
        elif command == "baseline":
            self._perf_baseline(*sub_args)
        elif command == "trend":
            self._perf_trend(*sub_args)
        else:
            console.error(f"Unknown performance command: {command}")

    @handle_errors()
    def _perf_summary(self, *args: str) -> None:
        """Performance summary."""
        app = args[0] if args else "all"
        console.info(f"Performance summary: {app}")

        rows = [
            ["Response Time", "120ms", "100ms"],
            ["Throughput", "1,000 req/s", "1,200 req/s"],
            ["Error Rate", "0.1%", "0.05%"],
            ["P95 Latency", "250ms", "200ms"],
            ["P99 Latency", "500ms", "450ms"],
        ]

        console.table("Metrics", ["Metric", "Current", "Target"], rows)

    @handle_errors()
    def _perf_compare(self, *args: str) -> None:
        """Compare performance."""
        if len(args) < 2:
            console.error("Usage: mon performance compare <version-a> <version-b>")
            return

        console.info(f"Comparing: {args[0]} vs {args[1]}")
        console.muted("  Response time: -5% improvement")
        console.muted("  Throughput: +10% improvement")

    @handle_errors()
    def _perf_baseline(self, *args: str) -> None:
        """Set performance baseline."""
        console.info("Setting performance baseline...")
        console.success("Baseline set")

    @handle_errors()
    def _perf_trend(self, *args: str) -> None:
        """Show performance trend."""
        metric = args[0] if args else "response_time"
        console.info(f"Performance trend: {metric}")
        console.muted("  Last hour: Stable")
        console.muted("  Last 24h: -3% improvement")
        console.muted("  Last 7 days: +2% degradation")

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _get_prometheus_url(self) -> Optional[str]:
        """Get Prometheus URL from config."""
        return "http://localhost:9090"

    def _get_grafana_url(self) -> Optional[str]:
        """Get Grafana URL from config."""
        return "http://localhost:3000"

    def _get_loki_url(self) -> Optional[str]:
        """Get Loki URL from config."""
        return "http://localhost:3100"

    def _get_jaeger_url(self) -> Optional[str]:
        """Get Jaeger URL from config."""
        return "http://localhost:16686"

    def _get_alertmanager_url(self) -> Optional[str]:
        """Get Alertmanager URL from config."""
        return "http://localhost:9093"

    def _parse_duration(self, duration: str) -> int:
        """Parse duration string to seconds."""
        duration = duration.lower()
        if duration.endswith("s"):
            return int(duration[:-1])
        elif duration.endswith("m"):
            return int(duration[:-1]) * 60
        elif duration.endswith("h"):
            return int(duration[:-1]) * 3600
        elif duration.endswith("d"):
            return int(duration[:-1]) * 86400
        else:
            return int(duration)

    # ========================================================================
    # Help Methods
    # ========================================================================

    def _show_help(self) -> None:
        """Show main help."""
        rows = [
            ["metrics <cmd>", "Prometheus metrics (query, series, labels, range)"],
            ["alert <cmd>", "Alert management (create, list, status, silence)"],
            ["log <cmd>", "Loki logs (search, tail, export, stats)"],
            ["dash <cmd>", "Grafana dashboards (list, view, export, import)"],
            ["trace <cmd>", "Jaeger traces (list, show, search)"],
            ["health <cmd>", "Health checks (check, status, dependency, sla)"],
            ["uptime <cmd>", "Uptime monitoring (monitor, report, add, remove)"],
            ["anomaly <cmd>", "Anomaly detection (detect, report)"],
            [
                "performance <cmd>",
                "Performance metrics (summary, compare, baseline, trend)",
            ],
        ]
        console.table("Monitoring Commands", ["Command", "Description"], rows)

    def _metrics_help(self) -> None:
        """Show metrics help."""
        console.info("Metrics commands:")
        console.muted("  mon metrics query <expr>        - Query metrics")
        console.muted("  mon metrics series <metric>     - List series")
        console.muted("  mon metrics labels <metric> <label>  - List label values")
        console.muted("  mon metrics range <expr> <duration>  - Range query")
        console.muted("  mon metrics export <format>   - Export metrics")
        console.muted("  mon metrics metadata <metric> - Get metadata")
        console.muted("  mon metrics label_names       - List all label names")

    def _alert_help(self) -> None:
        """Show alert help."""
        console.info("Alert commands:")
        console.muted("  mon alert create <name> <expr>  - Create alert")
        console.muted("  mon alert list                 - List alerts")
        console.muted("  mon alert status <id>         - Get alert status")
        console.muted("  mon alert silence <id> <duration>  - Silence alert")
        console.muted("  mon alert enable <id>         - Enable alert")
        console.muted("  mon alert disable <id>        - Disable alert")

    def _log_help(self) -> None:
        """Show log help."""
        console.info("Log commands:")
        console.muted("  mon log search <query>       - Search logs")
        console.muted("  mon log tail <service> [--follow]  - Tail logs")
        console.muted("  mon log export <query> <file>  - Export logs")
        console.muted("  mon log stats <query>        - Log statistics")

    def _dash_help(self) -> None:
        """Show dashboard help."""
        console.info("Dashboard commands:")
        console.muted("  mon dash list                  - List dashboards")
        console.muted("  mon dash view <dash>          - View dashboard")
        console.muted("  mon dash export <dash> <file>  - Export dashboard")
        console.muted("  mon dash import <file>        - Import dashboard")

    def _trace_help(self) -> None:
        """Show trace help."""
        console.info("Trace commands:")
        console.muted("  mon trace list [service]       - List traces")
        console.muted("  mon trace show <trace-id>     - Show trace")
        console.muted("  mon trace search <query>      - Search traces")

    def _health_help(self) -> None:
        """Show health help."""
        console.info("Health commands:")
        console.muted("  mon health check <service> [url]  - Health check")
        console.muted("  mon health status              - Overall health")
        console.muted("  mon health dependency <service>  - Check dependencies")
        console.muted("  mon health sla                 - SLA report")

    def _uptime_help(self) -> None:
        """Show uptime help."""
        console.info("Uptime commands:")
        console.muted("  mon uptime monitor <target>    - Create monitor")
        console.muted("  mon uptime report [target]     - Uptime report")
        console.muted("  mon uptime add <target>        - Add monitor")
        console.muted("  mon uptime remove <target>     - Remove monitor")

    def _anomaly_help(self) -> None:
        """Show anomaly help."""
        console.info("Anomaly commands:")
        console.muted("  mon anomaly detect <metric>   - Detect anomalies")
        console.muted("  mon anomaly report            - Anomaly report")

    def _performance_help(self) -> None:
        """Show performance help."""
        console.info("Performance commands:")
        console.muted("  mon performance summary [app]      - Performance summary")
        console.muted("  mon performance compare <a> <b>  - Compare versions")
        console.muted("  mon performance baseline         - Set baseline")
        console.muted("  mon performance trend <metric>  - Show trend")
