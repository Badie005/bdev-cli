"""
Kubernetes Plugin for B.DEV CLI

Provides comprehensive Kubernetes management including pods, services, deployments,
configmaps, secrets, namespaces, ingress, helm, and more using kubectl.
"""

import subprocess
import json
from typing import Any, List, Dict, Optional
from pathlib import Path

from cli.plugins import PluginBase
from cli.utils.ui import console


class KubernetesBase(PluginBase):
    """Base class for Kubernetes plugins."""

    _is_base = True

    def _run_kubectl(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run kubectl command."""
        cmd = ["kubectl"] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def _check_kubectl(self) -> bool:
        """Check if kubectl is installed."""
        result = self._run_kubectl(["version", "--client"])
        return result.returncode == 0

    def _check_context(self) -> bool:
        """Check if kubectl context is set."""
        result = self._run_kubectl(["config", "current-context"])
        return result.returncode == 0


# ============================================================================
# Cluster & Nodes
# ============================================================================


class K8sStatusPlugin(KubernetesBase):
    """Cluster status and information."""

    @property
    def name(self) -> str:
        return "k8s_status"

    @property
    def description(self) -> str:
        return "Show Kubernetes cluster status and information"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Show cluster status."""
        if not self._check_kubectl():
            console.error(
                "kubectl is not installed. Install from https://kubernetes.io/docs/tasks/tools/"
            )
            return None

        console.info("Cluster Status:")

        # Cluster info
        result = self._run_kubectl(["cluster-info"])
        if result.returncode == 0:
            console.rule("Cluster Info")
            console.muted(result.stdout)

        # Nodes
        result = self._run_kubectl(["get", "nodes", "-o", "wide"])
        if result.returncode == 0:
            console.rule("Nodes")
            console.muted(result.stdout)

        # Context
        result = self._run_kubectl(["config", "current-context"])
        if result.returncode == 0:
            console.muted(f"Current context: {result.stdout.strip()}")

        # Version
        result = self._run_kubectl(["version", "--short"])
        if result.returncode == 0:
            console.rule("Version")
            console.muted(result.stdout)


class K8sContextPlugin(KubernetesBase):
    """Manage kubectl contexts."""

    @property
    def name(self) -> str:
        return "k8s_context"

    @property
    def description(self) -> str:
        return "Manage Kubernetes contexts (list, set, use)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle context commands."""
        if not self._check_kubectl():
            console.error("kubectl is not installed")
            return None

        if not args:
            self._list_contexts()
            return

        command = args[0].lower()

        try:
            if command == "list":
                self._list_contexts()
            elif command == "set":
                self._set_context(*args[1:])
            elif command == "use":
                self._use_context(*args[1:])
            elif command == "namespace":
                self._set_namespace(*args[1:])
            else:
                console.error(f"Unknown context command: {command}")
        except Exception as e:
            console.error(f"Context command failed: {e}")

    def _list_contexts(self) -> None:
        """List all contexts."""
        result = self._run_kubectl(["config", "get-contexts"])
        if result.stdout:
            console.rule("Contexts")
            console.muted(result.stdout)

    def _set_context(self, *args: str) -> None:
        """Set context."""
        if not args:
            console.error("Usage: k8s_context set <context>")
            return

        context = args[0]
        console.info(f"Setting context: {context}")

        result = self._run_kubectl(["config", "use-context", context])

        if result.returncode == 0:
            console.success(f"Context set to {context}")
        else:
            console.error(f"Failed to set context: {result.stderr}")

    def _use_context(self, *args: str) -> None:
        """Use context (same as set)."""
        self._set_context(*args)

    def _set_namespace(self, *args: str) -> None:
        """Set default namespace."""
        namespace = args[0] if args else "default"
        console.info(f"Setting namespace: {namespace}")

        result = self._run_kubectl(
            ["config", "set-context", "--current", "--namespace", namespace]
        )

        if result.returncode == 0:
            console.success(f"Namespace set to {namespace}")
        else:
            console.error(f"Failed to set namespace: {result.stderr}")


# ============================================================================
# Pods
# ============================================================================


class K8sPodsPlugin(KubernetesBase):
    """Pod management."""

    @property
    def name(self) -> str:
        return "k8s_pods"

    @property
    def description(self) -> str:
        return "Pod management (list, describe, logs, exec, delete, port-forward)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle pod commands."""
        if not self._check_kubectl():
            console.error("kubectl is not installed")
            return None

        if not args:
            self._list_pods()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "list":
                self._list_pods(*sub_args)
            elif command == "get":
                self._list_pods(*sub_args)
            elif command == "describe":
                self._describe_pod(*sub_args)
            elif command == "logs":
                self._pod_logs(*sub_args)
            elif command == "exec":
                self._pod_exec(*sub_args)
            elif command == "delete":
                self._delete_pod(*sub_args)
            elif command == "port-forward":
                self._port_forward(*sub_args)
            elif command == "restart":
                self._restart_pod(*sub_args)
            elif command == "top":
                self._pod_top(*sub_args)
            elif command == "cp":
                self._pod_cp(*sub_args)
            else:
                console.error(f"Unknown pod command: {command}")
        except Exception as e:
            console.error(f"Pod command failed: {e}")

    def _list_pods(self, *args: str) -> None:
        """List pods."""
        namespace = args[0] if args else "all"
        wide = "--wide" in args or "-w" in args

        console.info(f"Listing pods in {namespace}...")

        cmd = ["get", "pods"]
        if namespace != "all":
            cmd.extend(["-n", namespace])
        if wide:
            cmd.append("--wide")

        result = self._run_kubectl(cmd)

        if result.stdout:
            console.rule(f"Pods in {namespace}")
            console.muted(result.stdout)
        else:
            console.info(f"No pods found in {namespace}")

    def _describe_pod(self, *args: str) -> None:
        """Describe pod details."""
        if len(args) < 1:
            console.error("Usage: k8s_pods describe <pod_name> [namespace]")
            return

        pod_name = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.info(f"Describing pod: {pod_name}")

        result = self._run_kubectl(["describe", "pod", pod_name, "-n", namespace])

        if result.stdout:
            console.muted(result.stdout)
        else:
            console.info(f"Pod {pod_name} not found in {namespace}")

    def _pod_logs(self, *args: str) -> None:
        """Get pod logs."""
        if len(args) < 1:
            console.error(
                "Usage: k8s_pods logs <pod_name> [namespace] [--follow] [--tail <n>]"
            )
            return

        pod_name = args[0]
        namespace = (
            args[1] if len(args) > 1 and not args[1].startswith("--") else "default"
        )

        follow = "--follow" in args or "-f" in args
        tail_idx = args.index("--tail") + 1 if "--tail" in args else None
        tail = args[tail_idx] if tail_idx is not None else "100"

        console.info(f"Logs for pod: {pod_name}")

        cmd = ["logs", pod_name, "-n", namespace, "--tail", tail]

        if follow:
            console.warning("Following logs (Ctrl+C to stop)...")
            subprocess.run(["kubectl"] + cmd)
        else:
            result = self._run_kubectl(cmd)
            if result.stdout:
                console.muted(result.stdout)
            else:
                console.info("No logs found")

    def _pod_exec(self, *args: str) -> None:
        """Execute command in pod."""
        if len(args) < 2:
            console.error("Usage: k8s_pods exec <pod_name> <command> [namespace] [-it]")
            return

        pod_name = args[0]
        command = args[1]
        namespace_idx = 2
        interactive = "-it" in args or "-i" in args or "-t" in args

        if args[namespace_idx] and not args[namespace_idx].startswith("-"):
            namespace = args[namespace_idx]
        else:
            namespace = "default"

        console.info(f"Executing in pod {pod_name}: {command}")

        cmd = ["exec"]
        if interactive:
            cmd.extend(["-it"])
        cmd.extend([pod_name, "-n", namespace, "--", command])

        subprocess.run(["kubectl"] + cmd)

    def _delete_pod(self, *args: str) -> None:
        """Delete pod."""
        if len(args) < 1:
            console.error("Usage: k8s_pods delete <pod_name> [namespace] [--force]")
            return

        pod_name = args[0]
        namespace = (
            args[1] if len(args) > 1 and not args[1].startswith("--") else "default"
        )
        force = "--force" in args or "-f" in args

        console.warning(f"Deleting pod: {pod_name}")

        cmd = ["delete", "pod", pod_name, "-n", namespace]
        if force:
            cmd.append("--force")

        result = self._run_kubectl(cmd)

        if result.returncode == 0:
            console.success(f"Pod {pod_name} deleted")
        else:
            console.error(f"Failed to delete: {result.stderr}")

    def _port_forward(self, *args: str) -> None:
        """Port forward to pod."""
        if len(args) < 2:
            console.error(
                "Usage: k8s_pods port-forward <pod_name> <local_port:remote_port> [namespace]"
            )
            return

        pod_name = args[0]
        port_mapping = args[1]
        namespace = args[2] if len(args) > 2 else "default"

        console.info(f"Port forwarding {pod_name}: {port_mapping}")
        console.warning("Press Ctrl+C to stop...")

        cmd = ["port-forward", pod_name, port_mapping, "-n", namespace]
        subprocess.run(["kubectl"] + cmd)

    def _restart_pod(self, *args: str) -> None:
        """Restart pod (by deleting and letting it recreate)."""
        if len(args) < 1:
            console.error("Usage: k8s_pods restart <pod_name> [namespace]")
            return

        pod_name = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.warning(f"Restarting pod: {pod_name}")

        result = self._run_kubectl(["delete", "pod", pod_name, "-n", namespace])

        if result.returncode == 0:
            console.success(f"Pod {pod_name} deleted. It should restart automatically.")
        else:
            console.error(f"Failed to restart: {result.stderr}")

    def _pod_top(self, *args: str) -> None:
        """Show pod resource usage."""
        if not args:
            console.error("Usage: k8s_pods top <pod_name> [namespace]")
            return

        pod_name = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        result = self._run_kubectl(["top", "pod", pod_name, "-n", namespace])

        if result.stdout:
            console.rule(f"Resource usage: {pod_name}")
            console.muted(result.stdout)
        else:
            console.info("No resource usage data available")

    def _pod_cp(self, *args: str) -> None:
        """Copy files to/from pod."""
        if len(args) < 2:
            console.error("Usage: k8s_pods cp <source> <dest>")
            return

        source = args[0]
        dest = args[1]

        console.info(f"Copying {source} -> {dest}")
        result = self._run_kubectl(["cp", source, dest])

        if result.returncode == 0:
            console.success("Copy completed")
        else:
            console.error(f"Copy failed: {result.stderr}")


# ============================================================================
# Deployments
# ============================================================================


class K8sDeploymentsPlugin(KubernetesBase):
    """Deployment management."""

    @property
    def name(self) -> str:
        return "k8s_deployments"

    @property
    def description(self) -> str:
        return "Deployment management (list, describe, scale, rollout, restart)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle deployment commands."""
        if not self._check_kubectl():
            console.error("kubectl is not installed")
            return None

        if not args:
            self._list_deployments()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "list":
                self._list_deployments(*sub_args)
            elif command == "describe":
                self._describe_deployment(*sub_args)
            elif command == "scale":
                self._scale_deployment(*sub_args)
            elif command == "rollout":
                self._rollout_deployment(*sub_args)
            elif command == "restart":
                self._restart_deployment(*sub_args)
            elif command == "status":
                self._deployment_status(*sub_args)
            elif command == "history":
                self._deployment_history(*sub_args)
            elif command == "pause":
                self._pause_deployment(*sub_args)
            elif command == "resume":
                self._resume_deployment(*sub_args)
            elif command == "undo":
                self._undo_deployment(*sub_args)
            else:
                console.error(f"Unknown deployment command: {command}")
        except Exception as e:
            console.error(f"Deployment command failed: {e}")

    def _list_deployments(self, *args: str) -> None:
        """List deployments."""
        namespace = args[0] if args else "all"

        console.info(f"Listing deployments in {namespace}...")

        cmd = ["get", "deployments"]
        if namespace != "all":
            cmd.extend(["-n", namespace])

        result = self._run_kubectl(cmd)

        if result.stdout:
            console.rule(f"Deployments in {namespace}")
            console.muted(result.stdout)
        else:
            console.info(f"No deployments found in {namespace}")

    def _describe_deployment(self, *args: str) -> None:
        """Describe deployment."""
        if len(args) < 1:
            console.error(
                "Usage: k8s_deployments describe <deployment_name> [namespace]"
            )
            return

        deployment = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.info(f"Describing deployment: {deployment}")

        result = self._run_kubectl(
            ["describe", "deployment", deployment, "-n", namespace]
        )

        if result.stdout:
            console.muted(result.stdout)
        else:
            console.info(f"Deployment {deployment} not found")

    def _scale_deployment(self, *args: str) -> None:
        """Scale deployment replicas."""
        if len(args) < 2:
            console.error(
                "Usage: k8s_deployments scale <deployment> <replicas> [namespace]"
            )
            return

        deployment = args[0]
        replicas = args[1]
        namespace = args[2] if len(args) > 2 else "default"

        console.info(f"Scaling {deployment} to {replicas} replicas...")

        result = self._run_kubectl(
            [
                "scale",
                "deployment",
                deployment,
                f"--replicas={replicas}",
                "-n",
                namespace,
            ]
        )

        if result.returncode == 0:
            console.success(f"Deployment {deployment} scaled to {replicas} replicas")
        else:
            console.error(f"Failed to scale: {result.stderr}")

    def _rollout_deployment(self, *args: str) -> None:
        """Rollout management."""
        if len(args) < 2:
            console.error(
                "Usage: k8s_deployments rollout <status|history|pause|resume|undo> <deployment> [namespace]"
            )
            return

        action = args[0]
        deployment = args[1]
        namespace = args[2] if len(args) > 2 else "default"

        console.info(f"Rollout {action}: {deployment}")

        result = self._run_kubectl(
            ["rollout", action, "deployment", deployment, "-n", namespace]
        )

        if result.stdout:
            console.muted(result.stdout)
        else:
            console.info("No rollout information")

    def _restart_deployment(self, *args: str) -> None:
        """Restart deployment."""
        if len(args) < 1:
            console.error("Usage: k8s_deployments restart <deployment> [namespace]")
            return

        deployment = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.info(f"Restarting deployment: {deployment}")

        result = self._run_kubectl(
            ["rollout", "restart", "deployment", deployment, "-n", namespace]
        )

        if result.returncode == 0:
            console.success(f"Deployment {deployment} restarted")
        else:
            console.error(f"Failed to restart: {result.stderr}")

    def _deployment_status(self, *args: str) -> None:
        """Show deployment status."""
        if len(args) < 1:
            console.error("Usage: k8s_deployments status <deployment> [namespace]")
            return

        deployment = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        result = self._run_kubectl(
            ["rollout", "status", "deployment", deployment, "-n", namespace]
        )

        if result.stdout:
            console.muted(result.stdout)
        else:
            console.info("No status information")

    def _deployment_history(self, *args: str) -> None:
        """Show deployment history."""
        if len(args) < 1:
            console.error("Usage: k8s_deployments history <deployment> [namespace]")
            return

        deployment = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        result = self._run_kubectl(
            ["rollout", "history", "deployment", deployment, "-n", namespace]
        )

        if result.stdout:
            console.rule(f"History: {deployment}")
            console.muted(result.stdout)
        else:
            console.info("No history found")

    def _pause_deployment(self, *args: str) -> None:
        """Pause deployment."""
        if len(args) < 1:
            console.error("Usage: k8s_deployments pause <deployment> [namespace]")
            return

        deployment = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.warning(f"Pausing deployment: {deployment}")

        result = self._run_kubectl(
            ["rollout", "pause", "deployment", deployment, "-n", namespace]
        )

        if result.returncode == 0:
            console.success(f"Deployment {deployment} paused")
        else:
            console.error(f"Failed to pause: {result.stderr}")

    def _resume_deployment(self, *args: str) -> None:
        """Resume deployment."""
        if len(args) < 1:
            console.error("Usage: k8s_deployments resume <deployment> [namespace]")
            return

        deployment = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.info(f"Resuming deployment: {deployment}")

        result = self._run_kubectl(
            ["rollout", "resume", "deployment", deployment, "-n", namespace]
        )

        if result.returncode == 0:
            console.success(f"Deployment {deployment} resumed")
        else:
            console.error(f"Failed to resume: {result.stderr}")

    def _undo_deployment(self, *args: str) -> None:
        """Undo deployment rollout."""
        if len(args) < 1:
            console.error(
                "Usage: k8s_deployments undo <deployment> [revision] [namespace]"
            )
            return

        deployment = args[0]
        revision = args[1] if len(args) > 1 and not args[1].startswith("-") else None
        namespace = args[2] if len(args) > 2 else "default"

        console.warning(f"Undoing rollout for: {deployment}")

        cmd = ["rollout", "undo", "deployment", deployment, "-n", namespace]
        if revision:
            cmd.extend(["--to-revision", revision])

        result = self._run_kubectl(cmd)

        if result.returncode == 0:
            console.success(f"Rollout undone for {deployment}")
        else:
            console.error(f"Failed to undo: {result.stderr}")


# ============================================================================
# Services
# ============================================================================


class K8sServicesPlugin(KubernetesBase):
    """Service management."""

    @property
    def name(self) -> str:
        return "k8s_services"

    @property
    def description(self) -> str:
        return "Service management (list, describe, expose, delete, endpoints)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle service commands."""
        if not self._check_kubectl():
            console.error("kubectl is not installed")
            return None

        if not args:
            self._list_services()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "list":
                self._list_services(*sub_args)
            elif command == "describe":
                self._describe_service(*sub_args)
            elif command == "expose":
                self._expose_service(*sub_args)
            elif command == "delete":
                self._delete_service(*sub_args)
            elif command == "endpoints":
                self._service_endpoints(*sub_args)
            else:
                console.error(f"Unknown service command: {command}")
        except Exception as e:
            console.error(f"Service command failed: {e}")

    def _list_services(self, *args: str) -> None:
        """List services."""
        namespace = args[0] if args else "all"

        console.info(f"Listing services in {namespace}...")

        cmd = ["get", "services"]
        if namespace != "all":
            cmd.extend(["-n", namespace])

        result = self._run_kubectl(cmd)

        if result.stdout:
            console.rule(f"Services in {namespace}")
            console.muted(result.stdout)
        else:
            console.info(f"No services found in {namespace}")

    def _describe_service(self, *args: str) -> None:
        """Describe service."""
        if len(args) < 1:
            console.error("Usage: k8s_services describe <service_name> [namespace]")
            return

        service = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.info(f"Describing service: {service}")

        result = self._run_kubectl(["describe", "service", service, "-n", namespace])

        if result.stdout:
            console.muted(result.stdout)
        else:
            console.info(f"Service {service} not found")

    def _expose_service(self, *args: str) -> None:
        """Expose deployment as service."""
        if len(args) < 2:
            console.error(
                "Usage: k8s_services expose <deployment> <port> [--type <type>] [--name <name>]"
            )
            return

        deployment = args[0]
        port = args[1]
        service_type = "ClusterIP"
        service_name = deployment

        for i, arg in enumerate(args):
            if arg == "--type" and i + 1 < len(args):
                service_type = args[i + 1]
            elif arg == "--name" and i + 1 < len(args):
                service_name = args[i + 1]

        console.info(f"Exposing {deployment} on port {port} as {service_type}...")

        result = self._run_kubectl(
            [
                "expose",
                "deployment",
                deployment,
                f"--port={port}",
                f"--type={service_type}",
                f"--name={service_name}",
            ]
        )

        if result.returncode == 0:
            console.success(f"Service {service_name} created")
            console.muted(result.stdout)
        else:
            console.error(f"Failed to expose: {result.stderr}")

    def _delete_service(self, *args: str) -> None:
        """Delete service."""
        if len(args) < 1:
            console.error("Usage: k8s_services delete <service_name> [namespace]")
            return

        service = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.warning(f"Deleting service: {service}")

        result = self._run_kubectl(["delete", "service", service, "-n", namespace])

        if result.returncode == 0:
            console.success(f"Service {service} deleted")
        else:
            console.error(f"Failed to delete: {result.stderr}")

    def _service_endpoints(self, *args: str) -> None:
        """Show service endpoints."""
        if len(args) < 1:
            console.error("Usage: k8s_services endpoints <service_name> [namespace]")
            return

        service = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        result = self._run_kubectl(["get", "endpoints", service, "-n", namespace])

        if result.stdout:
            console.rule(f"Endpoints: {service}")
            console.muted(result.stdout)
        else:
            console.info("No endpoints found")


# ============================================================================
# ConfigMaps & Secrets
# ============================================================================


class K8sConfigPlugin(KubernetesBase):
    """ConfigMap and Secret management."""

    @property
    def name(self) -> str:
        return "k8s_config"

    @property
    def description(self) -> str:
        return "ConfigMap and Secret management (list, create, describe, delete, edit)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle config commands."""
        if not self._check_kubectl():
            console.error("kubectl is not installed")
            return None

        if not args:
            self._show_help()
            return

        resource_type = args[0].lower()
        sub_args = args[1:]

        if resource_type not in ["configmap", "secret", "cm", "sec"]:
            console.error(f"Unknown resource type: {resource_type}")
            self._show_help()
            return

        resource = "configmap" if resource_type in ["configmap", "cm"] else "secret"

        if not sub_args:
            self._list_config(resource)
            return

        command = sub_args[0].lower()
        args_list = sub_args[1:]

        try:
            if command == "list":
                self._list_config(resource, *args_list)
            elif command == "describe":
                self._describe_config(resource, *args_list)
            elif command == "create":
                self._create_config(resource, *args_list)
            elif command == "delete":
                self._delete_config(resource, *args_list)
            elif command == "edit":
                self._edit_config(resource, *args_list)
            elif command == "get":
                self._get_config(resource, *args_list)
            elif command == "from-literal":
                self._create_from_literal(resource, *args_list)
            elif command == "from-file":
                self._create_from_file(resource, *args_list)
            else:
                console.error(f"Unknown config command: {command}")
        except Exception as e:
            console.error(f"Config command failed: {e}")

    def _list_config(self, resource: str, *args: str) -> None:
        """List configmaps or secrets."""
        namespace = args[0] if args else "all"

        console.info(f"Listing {resource}s in {namespace}...")

        cmd = ["get", resource]
        if namespace != "all":
            cmd.extend(["-n", namespace])

        result = self._run_kubectl(cmd)

        if result.stdout:
            console.rule(f"{resource.capitalize()}s")
            console.muted(result.stdout)
        else:
            console.info(f"No {resource}s found")

    def _describe_config(self, resource: str, *args: str) -> None:
        """Describe configmap or secret."""
        if len(args) < 1:
            console.error(f"Usage: k8s_config {resource} describe <name> [namespace]")
            return

        name = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.info(f"Describing {resource}: {name}")

        result = self._run_kubectl(["describe", resource, name, "-n", namespace])

        if result.stdout:
            console.muted(result.stdout)
        else:
            console.info(f"{resource.capitalize()} {name} not found")

    def _create_config(self, resource: str, *args: str) -> None:
        """Create configmap or secret from file."""
        if len(args) < 1:
            console.error(
                f"Usage: k8s_config {resource} create <name> --from-file <file> [namespace]"
            )
            return

        name = args[0]

        console.info(f"Creating {resource}: {name}")
        console.muted(
            "Use 'from-file' or 'from-literal' to create from file or literal values"
        )

    def _create_from_literal(self, resource: str, *args: str) -> None:
        """Create configmap/secret from literal values."""
        if len(args) < 2:
            console.error(
                f"Usage: k8s_config {resource} from-literal <name> <key=value> [key=value...]"
            )
            return

        name = args[0]
        key_values = args[1:]

        console.info(f"Creating {resource}: {name}")

        cmd = ["create", resource, name]
        for kv in key_values:
            cmd.extend(["--from-literal", kv])

        result = self._run_kubectl(cmd)

        if result.returncode == 0:
            console.success(f"{resource.capitalize()} {name} created")
        else:
            console.error(f"Failed to create: {result.stderr}")

    def _create_from_file(self, resource: str, *args: str) -> None:
        """Create configmap/secret from file."""
        if len(args) < 1:
            console.error(
                f"Usage: k8s_config {resource} from-file <name> <file> [namespace]"
            )
            return

        name = args[0]
        file_path = args[1]
        namespace = args[2] if len(args) > 2 else "default"

        console.info(f"Creating {resource} from file: {file_path}")

        result = self._run_kubectl(
            ["create", resource, name, f"--from-file={file_path}", "-n", namespace]
        )

        if result.returncode == 0:
            console.success(f"{resource.capitalize()} {name} created")
        else:
            console.error(f"Failed to create: {result.stderr}")

    def _delete_config(self, resource: str, *args: str) -> None:
        """Delete configmap or secret."""
        if len(args) < 1:
            console.error(f"Usage: k8s_config {resource} delete <name> [namespace]")
            return

        name = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.warning(f"Deleting {resource}: {name}")

        result = self._run_kubectl(["delete", resource, name, "-n", namespace])

        if result.returncode == 0:
            console.success(f"{resource.capitalize()} {name} deleted")
        else:
            console.error(f"Failed to delete: {result.stderr}")

    def _edit_config(self, resource: str, *args: str) -> None:
        """Edit configmap or secret."""
        if len(args) < 1:
            console.error(f"Usage: k8s_config {resource} edit <name> [namespace]")
            return

        name = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.info(f"Editing {resource}: {name}")
        console.muted("Opening editor...")

        subprocess.run(["kubectl", "edit", resource, name, "-n", namespace])

    def _get_config(self, resource: str, *args: str) -> None:
        """Get configmap or secret value."""
        if len(args) < 1:
            console.error(
                f"Usage: k8s_config {resource} get <name> [--key <key>] [namespace]"
            )
            return

        name = args[0]
        namespace = args[2] if len(args) > 2 else "default"
        get_key = None

        for i, arg in enumerate(args):
            if arg == "--key" and i + 1 < len(args):
                get_key = args[i + 1]

        result = self._run_kubectl(
            ["get", resource, name, "-n", namespace, "-o", "yaml"]
        )

        if result.stdout:
            if get_key:
                import yaml

                data = yaml.safe_load(result.stdout)
                value = data.get("data", {}).get(get_key, "Key not found")
                console.muted(f"{get_key} = {value}")
            else:
                console.muted(result.stdout)
        else:
            console.info(f"{resource.capitalize()} not found")

    def _show_help(self) -> None:
        console.muted("Usage: k8s_config <configmap|secret> <command> [args]")
        console.muted(
            "Commands: list, describe, create, delete, edit, get, from-literal, from-file"
        )


# ============================================================================
# Namespaces
# ============================================================================


class K8sNamespacePlugin(KubernetesBase):
    """Namespace management."""

    @property
    def name(self) -> str:
        return "k8s_namespace"

    @property
    def description(self) -> str:
        return "Namespace management (list, create, delete, describe, set-default)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle namespace commands."""
        if not self._check_kubectl():
            console.error("kubectl is not installed")
            return None

        if not args:
            self._list_namespaces()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "list":
                self._list_namespaces()
            elif command == "create":
                self._create_namespace(*sub_args)
            elif command == "delete":
                self._delete_namespace(*sub_args)
            elif command == "describe":
                self._describe_namespace(*sub_args)
            elif command == "set-default":
                self._set_default_namespace(*sub_args)
            elif command == "current":
                self._current_namespace()
            else:
                console.error(f"Unknown namespace command: {command}")
        except Exception as e:
            console.error(f"Namespace command failed: {e}")

    def _list_namespaces(self) -> None:
        """List namespaces."""
        console.info("Listing namespaces...")

        result = self._run_kubectl(["get", "namespaces"])

        if result.stdout:
            console.rule("Namespaces")
            console.muted(result.stdout)
        else:
            console.info("No namespaces found")

    def _create_namespace(self, *args: str) -> None:
        """Create namespace."""
        if not args:
            console.error("Usage: k8s_namespace create <name>")
            return

        name = args[0]
        console.info(f"Creating namespace: {name}")

        result = self._run_kubectl(["create", "namespace", name])

        if result.returncode == 0:
            console.success(f"Namespace {name} created")
        else:
            console.error(f"Failed to create: {result.stderr}")

    def _delete_namespace(self, *args: str) -> None:
        """Delete namespace."""
        if not args:
            console.error("Usage: k8s_namespace delete <name>")
            return

        name = args[0]
        console.warning(
            f"[!] Deleting namespace: {name} (will delete all resources in it)"
        )

        confirmation = input("Are you sure? (yes/no): ")
        if confirmation.lower() != "yes":
            console.info("Operation cancelled")
            return

        result = self._run_kubectl(["delete", "namespace", name])

        if result.returncode == 0:
            console.success(f"Namespace {name} deleted")
        else:
            console.error(f"Failed to delete: {result.stderr}")

    def _describe_namespace(self, *args: str) -> None:
        """Describe namespace."""
        if not args:
            console.error("Usage: k8s_namespace describe <name>")
            return

        name = args[0]
        console.info(f"Describing namespace: {name}")

        result = self._run_kubectl(["describe", "namespace", name])

        if result.stdout:
            console.muted(result.stdout)
        else:
            console.info(f"Namespace {name} not found")

    def _set_default_namespace(self, *args: str) -> None:
        """Set default namespace for context."""
        namespace = args[0] if args else "default"

        console.info(f"Setting default namespace to {namespace}...")

        result = self._run_kubectl(
            ["config", "set-context", "--current", "--namespace", namespace]
        )

        if result.returncode == 0:
            console.success(f"Default namespace set to {namespace}")
        else:
            console.error(f"Failed to set namespace: {result.stderr}")

    def _current_namespace(self) -> None:
        """Show current namespace."""
        result = self._run_kubectl(
            ["config", "view", "--minify", "--output", "jsonpath={..namespace}"]
        )

        if result.stdout:
            console.muted(f"Current namespace: {result.stdout.strip()}")
        else:
            console.info("No current namespace set")


# ============================================================================
# Ingress
# ============================================================================


class K8sIngressPlugin(KubernetesBase):
    """Ingress management."""

    @property
    def name(self) -> str:
        return "k8s_ingress"

    @property
    def description(self) -> str:
        return "Ingress management (list, describe, create, delete, update)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle ingress commands."""
        if not self._check_kubectl():
            console.error("kubectl is not installed")
            return None

        if not args:
            self._list_ingress()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "list":
                self._list_ingress(*sub_args)
            elif command == "describe":
                self._describe_ingress(*sub_args)
            elif command == "create":
                self._create_ingress(*sub_args)
            elif command == "delete":
                self._delete_ingress(*sub_args)
            elif command == "update":
                self._update_ingress(*sub_args)
            elif command == "status":
                self._ingress_status(*sub_args)
            else:
                console.error(f"Unknown ingress command: {command}")
        except Exception as e:
            console.error(f"Ingress command failed: {e}")

    def _list_ingress(self, *args: str) -> None:
        """List ingress."""
        namespace = args[0] if args else "all"

        console.info(f"Listing ingress in {namespace}...")

        cmd = ["get", "ingress"]
        if namespace != "all":
            cmd.extend(["-n", namespace])

        result = self._run_kubectl(cmd)

        if result.stdout:
            console.rule(f"Ingress in {namespace}")
            console.muted(result.stdout)
        else:
            console.info(f"No ingress found in {namespace}")

    def _describe_ingress(self, *args: str) -> None:
        """Describe ingress."""
        if len(args) < 1:
            console.error("Usage: k8s_ingress describe <name> [namespace]")
            return

        name = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.info(f"Describing ingress: {name}")

        result = self._run_kubectl(["describe", "ingress", name, "-n", namespace])

        if result.stdout:
            console.muted(result.stdout)
        else:
            console.info(f"Ingress {name} not found")

    def _create_ingress(self, *args: str) -> None:
        """Create ingress from YAML."""
        if not args:
            console.error("Usage: k8s_ingress create <yaml_file> [namespace]")
            return

        yaml_file = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.info(f"Creating ingress from {yaml_file}...")

        result = self._run_kubectl(["apply", "-f", yaml_file, "-n", namespace])

        if result.returncode == 0:
            console.success("Ingress created")
        else:
            console.error(f"Failed to create: {result.stderr}")

    def _delete_ingress(self, *args: str) -> None:
        """Delete ingress."""
        if len(args) < 1:
            console.error("Usage: k8s_ingress delete <name> [namespace]")
            return

        name = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.warning(f"Deleting ingress: {name}")

        result = self._run_kubectl(["delete", "ingress", name, "-n", namespace])

        if result.returncode == 0:
            console.success(f"Ingress {name} deleted")
        else:
            console.error(f"Failed to delete: {result.stderr}")

    def _update_ingress(self, *args: str) -> None:
        """Update ingress."""
        if not args:
            console.error("Usage: k8s_ingress update <yaml_file> [namespace]")
            return

        yaml_file = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.info(f"Updating ingress from {yaml_file}...")

        result = self._run_kubectl(["apply", "-f", yaml_file, "-n", namespace])

        if result.returncode == 0:
            console.success("Ingress updated")
        else:
            console.error(f"Failed to update: {result.stderr}")

    def _ingress_status(self, *args: str) -> None:
        """Show ingress status."""
        if len(args) < 1:
            console.error("Usage: k8s_ingress status <name> [namespace]")
            return

        name = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        result = self._run_kubectl(
            ["get", "ingress", name, "-n", namespace, "-o", "yaml"]
        )

        if result.stdout:
            console.muted(result.stdout)
        else:
            console.info(f"Ingress {name} not found")


# ============================================================================
# Events & Logs
# ============================================================================


class K8sEventsPlugin(KubernetesBase):
    """Event management."""

    @property
    def name(self) -> str:
        return "k8s_events"

    @property
    def description(self) -> str:
        return "Cluster and resource events (list, watch, describe)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle event commands."""
        if not self._check_kubectl():
            console.error("kubectl is not installed")
            return None

        command = args[0] if args else "list"
        sub_args = args[1:] if len(args) > 1 else []

        try:
            if command == "list":
                self._list_events(*sub_args)
            elif command == "watch":
                self._watch_events(*sub_args)
            elif command == "describe":
                self._describe_events(*sub_args)
            else:
                console.error(f"Unknown event command: {command}")
        except Exception as e:
            console.error(f"Event command failed: {e}")

    def _list_events(self, *args: str) -> None:
        """List events."""
        namespace = args[0] if args else "all"
        limit = args[1] if len(args) > 1 and args[1].isdigit() else "20"

        console.info(f"Listing recent events in {namespace}...")

        cmd = ["get", "events"]
        if namespace != "all":
            cmd.extend(["-n", namespace])
        cmd.extend(["--sort-by=.lastTimestamp", f"--limit={limit}"])

        result = self._run_kubectl(cmd)

        if result.stdout:
            console.rule(f"Events in {namespace}")
            console.muted(result.stdout)
        else:
            console.info(f"No events found in {namespace}")

    def _watch_events(self, *args: str) -> None:
        """Watch events in real-time."""
        namespace = args[0] if args else "all"

        console.warning(f"Watching events in {namespace} (Ctrl+C to stop)...")

        cmd = ["get", "events", "-w"]
        if namespace != "all":
            cmd.extend(["-n", namespace])

        subprocess.run(["kubectl"] + cmd)

    def _describe_events(self, *args: str) -> None:
        """Describe event."""
        if not args:
            console.error("Usage: k8s_events describe <event_name> [namespace]")
            return

        event_name = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.info(f"Describing event: {event_name}")

        result = self._run_kubectl(["describe", "event", event_name, "-n", namespace])

        if result.stdout:
            console.muted(result.stdout)
        else:
            console.info(f"Event {event_name} not found")


# ============================================================================
# Apply & Apply Management
# ============================================================================


class K8sApplyPlugin(KubernetesBase):
    """Apply manifests to cluster."""

    @property
    def name(self) -> str:
        return "k8s_apply"

    @property
    def description(self) -> str:
        return "Apply manifests (file, directory, url) to cluster"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle apply commands."""
        if not self._check_kubectl():
            console.error("kubectl is not installed")
            return None

        if not args:
            console.error("Usage: k8s_apply <file|directory|url> [namespace]")
            return

        target = args[0]
        namespace = args[1] if len(args) > 1 else "default"
        dry_run = "--dry-run" in args or "-d" in args

        console.info(f"Applying {target}...")

        cmd = ["apply", "-f", target]
        if dry_run:
            cmd.append("--dry-run=client")

        result = self._run_kubectl(cmd)

        if result.returncode == 0:
            if dry_run:
                console.success("Dry-run successful")
            else:
                console.success("Applied successfully")
            console.muted(result.stdout)
        else:
            console.error(f"Failed to apply: {result.stderr}")


# ============================================================================
# Helm Support
# ============================================================================


class K8sHelmPlugin(KubernetesBase):
    """Helm package manager support."""

    @property
    def name(self) -> str:
        return "k8s_helm"

    @property
    def description(self) -> str:
        return (
            "Helm package manager commands (list, install, uninstall, upgrade, status)"
        )

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle helm commands."""
        if not self._check_helm():
            console.error("Helm is not installed. Install from https://helm.sh/")
            return None

        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "list":
                self._helm_list(*sub_args)
            elif command == "install":
                self._helm_install(*sub_args)
            elif command == "uninstall":
                self._helm_uninstall(*sub_args)
            elif command == "upgrade":
                self._helm_upgrade(*sub_args)
            elif command == "status":
                self._helm_status(*sub_args)
            elif command == "repo":
                self._helm_repo(*sub_args)
            elif command == "search":
                self._helm_search(*sub_args)
            elif command == "version":
                self._helm_version(*sub_args)
            elif command == "history":
                self._helm_history(*sub_args)
            elif command == "rollback":
                self._helm_rollback(*sub_args)
            elif command == "test":
                self._helm_test(*sub_args)
            elif command == "values":
                self._helm_values(*sub_args)
            else:
                console.error(f"Unknown helm command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Helm command failed: {e}")

    def _check_helm(self) -> bool:
        """Check if helm is installed."""
        result = subprocess.run(["helm", "version"], capture_output=True, text=True)
        return result.returncode == 0

    def _run_helm(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run helm command."""
        cmd = ["helm"] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def _helm_list(self, *args: str) -> None:
        """List installed releases."""
        namespace = args[0] if args else "all"

        console.info(f"Listing Helm releases in {namespace}...")

        cmd = ["list", "--all"]
        if namespace != "all":
            cmd.extend(["-n", namespace])

        result = self._run_helm(cmd)

        if result.stdout:
            console.rule("Helm Releases")
            console.muted(result.stdout)
        else:
            console.info("No releases found")

    def _helm_install(self, *args: str) -> None:
        """Install chart."""
        if len(args) < 2:
            console.error("Usage: k8s_helm install <release_name> <chart> [values]")
            return

        release_name = args[0]
        chart = args[1]
        values = args[2] if len(args) > 2 else None
        namespace = args[3] if len(args) > 3 else "default"

        console.info(f"Installing {chart} as {release_name}...")

        cmd = ["install", release_name, chart, "-n", namespace]
        if values:
            cmd.extend(["-f", values])

        result = self._run_helm(cmd)

        if result.returncode == 0:
            console.success(f"Release {release_name} installed")
            console.muted(result.stdout)
        else:
            console.error(f"Failed to install: {result.stderr}")

    def _helm_uninstall(self, *args: str) -> None:
        """Uninstall release."""
        if len(args) < 1:
            console.error("Usage: k8s_helm uninstall <release_name> [namespace]")
            return

        release_name = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.warning(f"Uninstalling release: {release_name}")

        result = self._run_helm(["uninstall", release_name, "-n", namespace])

        if result.returncode == 0:
            console.success(f"Release {release_name} uninstalled")
        else:
            console.error(f"Failed to uninstall: {result.stderr}")

    def _helm_upgrade(self, *args: str) -> None:
        """Upgrade release."""
        if len(args) < 2:
            console.error("Usage: k8s_helm upgrade <release_name> <chart> [values]")
            return

        release_name = args[0]
        chart = args[1]
        values = args[2] if len(args) > 2 else None
        namespace = args[3] if len(args) > 3 else "default"

        console.info(f"Upgrading {release_name} with {chart}...")

        cmd = ["upgrade", release_name, chart, "-n", namespace]
        if values:
            cmd.extend(["-f", values])

        result = self._run_helm(cmd)

        if result.returncode == 0:
            console.success(f"Release {release_name} upgraded")
        else:
            console.error(f"Failed to upgrade: {result.stderr}")

    def _helm_status(self, *args: str) -> None:
        """Show release status."""
        if not args:
            console.error("Usage: k8s_helm status <release_name> [namespace]")
            return

        release_name = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        result = self._run_helm(["status", release_name, "-n", namespace])

        if result.stdout:
            console.rule(f"Status: {release_name}")
            console.muted(result.stdout)
        else:
            console.info(f"Release {release_name} not found")

    def _helm_repo(self, *args: str) -> None:
        """Manage helm repositories."""
        if not args:
            self._run_helm(["repo", "list"])
            return

        action = args[0]
        repo_args = args[1:]

        if action == "add":
            if len(repo_args) < 1:
                console.error("Usage: k8s_helm repo add <name> <url>")
                return
            result = self._run_helm(["repo", "add"] + repo_args)
            if result.returncode == 0:
                console.success(f"Repository {repo_args[0]} added")
        elif action == "update":
            if not repo_args:
                console.error("Usage: k8s_helm repo update <name>")
                return
            result = self._run_helm(["repo", "update"] + repo_args)
            if result.returncode == 0:
                console.success(f"Repository {repo_args[0]} updated")
        elif action == "remove":
            if not repo_args:
                console.error("Usage: k8s_helm repo remove <name>")
                return
            result = self._run_helm(["repo", "remove"] + repo_args)
            if result.returncode == 0:
                console.success(f"Repository {repo_args[0]} removed")
        elif action == "list":
            result = self._run_helm(["repo", "list"])
            if result.stdout:
                console.rule("Helm Repositories")
                console.muted(result.stdout)

    def _helm_search(self, *args: str) -> None:
        """Search charts."""
        keyword = args[0] if args else ""
        repo = args[1] if len(args) > 1 else ""

        console.info(f"Searching for: {keyword}")

        cmd = ["search", keyword]
        if repo:
            cmd.extend(["--repo", repo])

        result = self._run_helm(cmd)

        if result.stdout:
            console.rule("Search Results")
            console.muted(result.stdout)
        else:
            console.info("No charts found")

    def _helm_version(self, *args: str) -> None:
        """Show chart versions."""
        if not args:
            console.error("Usage: k8s_helm version <chart> [version]")
            return

        chart = args[0]
        version = args[1] if len(args) > 1 else ""

        cmd = ["search", chart, "--versions"]
        if version:
            cmd.extend(["--version", version])

        result = self._run_helm(cmd)

        if result.stdout:
            console.rule(f"Versions: {chart}")
            console.muted(result.stdout)

    def _helm_history(self, *args: str) -> None:
        """Show release history."""
        if not args:
            console.error("Usage: k8s_helm history <release_name> [namespace]")
            return

        release_name = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        result = self._run_helm(["history", release_name, "-n", namespace])

        if result.stdout:
            console.rule(f"History: {release_name}")
            console.muted(result.stdout)
        else:
            console.info(f"Release {release_name} not found")

    def _helm_rollback(self, *args: str) -> None:
        """Rollback release."""
        if len(args) < 1:
            console.error(
                "Usage: k8s_helm rollback <release_name> [revision] [namespace]"
            )
            return

        release_name = args[0]
        revision = args[1] if len(args) > 1 and not args[1].startswith("-") else None
        namespace = args[2] if len(args) > 2 else "default"

        console.warning(f"Rolling back {release_name}...")

        cmd = ["rollback", release_name, "-n", namespace]
        if revision:
            cmd.append(revision)

        result = self._run_helm(cmd)

        if result.returncode == 0:
            console.success(f"Rollback {release_name} completed")
        else:
            console.error(f"Rollback failed: {result.stderr}")

    def _helm_test(self, *args: str) -> None:
        """Test release."""
        if not args:
            console.error("Usage: k8s_helm test <release_name> [namespace]")
            return

        release_name = args[0]
        namespace = args[1] if len(args) > 1 else "default"

        console.info(f"Testing release: {release_name}")

        result = self._run_helm(["test", release_name, "-n", namespace])

        if result.returncode == 0:
            console.success(f"Release {release_name} tests passed")
            console.muted(result.stdout)
        else:
            console.error(f"Tests failed: {result.stderr}")

    def _helm_values(self, *args: str) -> None:
        """Show release values."""
        if not args:
            console.error("Usage: k8s_helm values <release_name> [namespace] [--all]")
            return

        release_name = args[0]
        namespace = (
            args[1] if len(args) > 1 and not args[1].startswith("--") else "default"
        )
        all_values = "--all" in args

        cmd = ["get", "values", release_name, "-n", namespace]
        if all_values:
            cmd.append("--all")

        result = self._run_helm(cmd)

        if result.stdout:
            console.rule(f"Values: {release_name}")
            console.muted(result.stdout)
        else:
            console.info(f"Release {release_name} not found")

    def _show_help(self) -> None:
        rows = [
            ["list [namespace]", "List installed releases"],
            ["install <release> <chart> [values]", "Install chart"],
            ["uninstall <release> [namespace]", "Uninstall release"],
            ["upgrade <release> <chart> [values]", "Upgrade release"],
            ["status <release> [namespace]", "Show release status"],
            ["repo <add|update|remove|list>", "Manage repositories"],
            ["search <keyword>", "Search charts"],
            ["version <chart>", "Show chart versions"],
            ["history <release>", "Show release history"],
            ["rollback <release> [revision]", "Rollback release"],
            ["test <release>", "Test release"],
            ["values <release>", "Show release values"],
        ]
        console.table("Helm Commands", ["Command", "Description"], rows)


# ============================================================================
# Resource Management
# ============================================================================


class K8sResourcePlugin(KubernetesBase):
    """General resource management."""

    @property
    def name(self) -> str:
        return "k8s"

    @property
    def description(self) -> str:
        return "General Kubernetes resource management (get, describe, delete, edit, scale)"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Handle resource commands."""
        if not self._check_kubectl():
            console.error("kubectl is not installed")
            return None

        if not args:
            self._show_help()
            return

        command = args[0].lower()
        sub_args = args[1:]

        try:
            if command == "get":
                self._get_resource(*sub_args)
            elif command == "describe":
                self._describe_resource(*sub_args)
            elif command == "delete":
                self._delete_resource(*sub_args)
            elif command == "edit":
                self._edit_resource(*sub_args)
            elif command == "scale":
                self._scale_resource(*sub_args)
            elif command == "top":
                self._top_resource(*sub_args)
            elif command == "logs":
                self._resource_logs(*sub_args)
            elif command == "exec":
                self._resource_exec(*sub_args)
            else:
                console.error(f"Unknown resource command: {command}")
                self._show_help()
        except Exception as e:
            console.error(f"Resource command failed: {e}")

    def _get_resource(self, *args: str) -> None:
        """Get resource."""
        resource = args[0] if args else "pods"
        namespace = args[1] if len(args) > 1 and not args[1].startswith("-") else "all"

        console.info(f"Getting {resource}...")

        cmd = ["get", resource]
        if namespace != "all":
            cmd.extend(["-n", namespace])

        result = self._run_kubectl(cmd)

        if result.stdout:
            console.rule(f"{resource.capitalize()}s")
            console.muted(result.stdout)
        else:
            console.info(f"No {resource}s found")

    def _describe_resource(self, *args: str) -> None:
        """Describe resource."""
        if len(args) < 2:
            console.error("Usage: k8s describe <resource> <name> [namespace]")
            return

        resource = args[0]
        name = args[1]
        namespace = args[2] if len(args) > 2 else "default"

        console.info(f"Describing {resource}: {name}")

        result = self._run_kubectl(["describe", resource, name, "-n", namespace])

        if result.stdout:
            console.muted(result.stdout)
        else:
            console.info(f"{resource.capitalize()} {name} not found")

    def _delete_resource(self, *args: str) -> None:
        """Delete resource."""
        if len(args) < 2:
            console.error("Usage: k8s delete <resource> <name> [namespace] [--force]")
            return

        resource = args[0]
        name = args[1]
        namespace = (
            args[2] if len(args) > 2 and not args[2].startswith("-") else "default"
        )
        force = "--force" in args or "-f" in args

        console.warning(f"Deleting {resource}: {name}")

        cmd = ["delete", resource, name, "-n", namespace]
        if force:
            cmd.append("--force")

        result = self._run_kubectl(cmd)

        if result.returncode == 0:
            console.success(f"{resource.capitalize()} {name} deleted")
        else:
            console.error(f"Failed to delete: {result.stderr}")

    def _edit_resource(self, *args: str) -> None:
        """Edit resource."""
        if len(args) < 2:
            console.error("Usage: k8s edit <resource> <name> [namespace]")
            return

        resource = args[0]
        name = args[1]
        namespace = args[2] if len(args) > 2 else "default"

        console.info(f"Editing {resource}: {name}")

        subprocess.run(["kubectl", "edit", resource, name, "-n", namespace])

    def _scale_resource(self, *args: str) -> None:
        """Scale resource."""
        if len(args) < 3:
            console.error("Usage: k8s scale <resource> <name> <replicas> [namespace]")
            return

        resource = args[0]
        name = args[1]
        replicas = args[2]
        namespace = args[3] if len(args) > 3 else "default"

        console.info(f"Scaling {resource} {name} to {replicas}...")

        result = self._run_kubectl(
            ["scale", resource, name, f"--replicas={replicas}", "-n", namespace]
        )

        if result.returncode == 0:
            console.success(f"Resource scaled to {replicas}")
        else:
            console.error(f"Failed to scale: {result.stderr}")

    def _top_resource(self, *args: str) -> None:
        """Show resource usage."""
        resource = args[0] if args else "pods"

        console.info(f"Top {resource}...")

        result = self._run_kubectl(["top", resource])

        if result.stdout:
            console.rule(f"Resource Usage: {resource}")
            console.muted(result.stdout)
        else:
            console.info("No usage data available")

    def _resource_logs(self, *args: str) -> None:
        """Get resource logs."""
        if len(args) < 2:
            console.error(
                "Usage: k8s logs <resource_type> <name> [namespace] [--follow] [--tail <n>]"
            )
            return

        resource_type = args[0]
        name = args[1]
        namespace = (
            args[2] if len(args) > 2 and not args[2].startswith("--") else "default"
        )

        follow = "--follow" in args or "-f" in args
        tail_idx = args.index("--tail") + 1 if "--tail" in args else None
        tail = args[tail_idx] if tail_idx is not None else "100"

        console.info(f"Logs for {resource_type}: {name}")

        cmd = ["logs", resource_type, name, "-n", namespace, "--tail", tail]

        if follow:
            subprocess.run(["kubectl"] + cmd)
        else:
            result = self._run_kubectl(cmd)
            if result.stdout:
                console.muted(result.stdout)

    def _resource_exec(self, *args: str) -> None:
        """Execute in resource."""
        if len(args) < 2:
            console.error(
                "Usage: k8s exec <resource_type> <name> <command> [namespace] [-it]"
            )
            return

        resource_type = args[0]
        name = args[1]
        command = args[2]
        namespace = args[3] if len(args) > 3 else "default"

        console.info(f"Executing in {resource_type} {name}: {command}")

        cmd = ["exec", resource_type, name, "-n", namespace, "--", command]
        subprocess.run(["kubectl"] + cmd)

    def _show_help(self) -> None:
        rows = [
            ["get <resource> [namespace]", "Get resources"],
            ["describe <resource> <name> [namespace]", "Describe resource"],
            ["delete <resource> <name> [namespace]", "Delete resource"],
            ["edit <resource> <name> [namespace]", "Edit resource"],
            ["scale <resource> <name> <replicas> [namespace]", "Scale resource"],
            ["top [resource]", "Show resource usage"],
            ["logs <resource> <name> [namespace]", "Get logs"],
            ["exec <resource> <name> <command>", "Execute in resource"],
        ]
        console.table("Resource Commands", ["Command", "Description"], rows)


# ============================================================================
# Dashboard
# ============================================================================


class K8sDashboardPlugin(KubernetesBase):
    """Kubernetes dashboard access."""

    @property
    def name(self) -> str:
        return "k8s_dashboard"

    @property
    def description(self) -> str:
        return "Open Kubernetes dashboard in browser"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Open dashboard."""
        import webbrowser

        console.info("Opening Kubernetes dashboard...")

        # Try to find dashboard service
        result = self._run_kubectl(
            ["get", "svc", "-A", "-l", "app.kubernetes.io/name=kubernetes-dashboard"]
        )

        if result.stdout:
            console.muted("Dashboard service found. Opening in browser...")
            webbrowser.open(
                "http://localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/#/overview"
            )
        else:
            console.warning("Dashboard not found. You can install it with:")
            console.muted(
                "kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml"
            )


# ============================================================================
# Top Command (All Resources)
# ============================================================================


class K8sTopPlugin(KubernetesBase):
    """Top command for resource usage."""

    @property
    def name(self) -> str:
        return "k8s_top"

    @property
    def description(self) -> str:
        return "Show resource usage across all resources"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Show top."""
        console.info("Resource Usage (Ctrl+C to exit)...")

        subprocess.run(["kubectl", "top"])
